from __future__ import annotations

import re
from typing import Dict, List, Tuple

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from ..config import settings


_generator = None


def _get_generator():
    """
    Lazily load the Hugging Face model and tokenizer.

    This is kept intentionally simple: it loads the model on first use
    and reuses a single text-generation pipeline for all requests.
    """
    global _generator
    if _generator is None:
        tokenizer = AutoTokenizer.from_pretrained(settings.hf_model_name)
        model = AutoModelForCausalLM.from_pretrained(settings.hf_model_name)
        _generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
        )
    return _generator


def _build_initial_prompt(nl_query: str, schema_text: str) -> str:
    """
    Build a short, focused prompt for initial SQL generation.
    No conversation history to avoid prompt poisoning.
    """
    system_instruction = (
        "You are an assistant that converts natural language questions "
        "to syntactically correct SQL for the given database schema.\n"
        "Follow these rules strictly:\n"
        "1. Use only the tables and columns that exist in the schema.\n"
        "2. Do not invent columns or tables.\n"
        "3. Return only a single SQL query.\n"
        "4. Wrap the SQL in a Markdown ```sql code block.\n"
    )

    schema_block = f"SCHEMA:\n{schema_text.strip()}\n\n"

    user_instruction = (
        f"User question: {nl_query}\n\n"
        "Return only the SQL query in a ```sql code block. "
        "Do not add explanations or comments outside the code block."
    )

    return f"{system_instruction}{schema_block}{user_instruction}"


def _build_repair_prompt(nl_query: str, schema_text: str, previous_output: str) -> str:
    """
    Build a repair prompt when initial generation fails.
    Includes the previous bad output and asks for a rewrite.
    """
    system_instruction = (
        "You are an assistant that converts natural language questions "
        "to syntactically correct SQL for the given database schema.\n"
        "The previous attempt failed. Rewrite it as a single SQL query.\n"
    )

    schema_block = f"SCHEMA:\n{schema_text.strip()}\n\n"

    repair_instruction = (
        f"User question: {nl_query}\n\n"
        f"Previous (incorrect) output:\n{previous_output}\n\n"
        "Rewrite as a single SQL query in a ```sql code block. Output nothing else."
    )

    return f"{system_instruction}{schema_block}{repair_instruction}"


def _extract_sql_from_output(text: str) -> str:
    """
    Try to extract a clean SQL query from the model output.

    Strategy:
    1. Prefer content inside ```sql ... ``` or ``` ... ``` blocks (backwards compatibility).
    2. Otherwise, find the first occurrence of a likely SQL statement
       starting with SELECT or WITH and trim off any trailing prompt echo.
    """
    code_block_pattern = re.compile(r"```sql(.*?```)", re.IGNORECASE | re.DOTALL)
    match = code_block_pattern.search(text)
    if not match:
        generic_pattern = re.compile(r"```(.*?```)", re.DOTALL)
        match = generic_pattern.search(text)

    if match:
        content = match.group(1)
        content = content.rsplit("```", 1)[0]
        return content.strip()

    # No fenced code block found – fall back to searching for SQL keywords.
    lowered = text.lower()
    start = -1
    for keyword in ("select ", "with "):
        idx = lowered.find(keyword)
        if idx != -1 and (start == -1 or idx < start):
            start = idx

    if start == -1:
        # Give up and return the raw text; the caller can surface it for debugging.
        return text.strip()

    end = len(text)
    # Cut off any obvious prompt-echo sections if present.
    for marker in ("schema:", "conversation history", "user question:"):
        marker_idx = lowered.find(marker, start)
        if marker_idx != -1:
            end = min(end, marker_idx)

    sql = text[start:end].strip()
    return sql


def _is_plausible_sql(candidate: str) -> bool:
    """
    Heuristic check to avoid treating prompt fragments or plain text as SQL.
    """
    stripped = candidate.strip()
    if not stripped:
        return False

    lowered = stripped.lower()

    # Obvious prompt-echo or meta text – reject.
    if any(marker in lowered for marker in ("conversation history", "user question:", "return only the sql query")):
        return False

    # Must contain a SQL keyword like SELECT/WITH.
    if not re.search(r"\b(select|with)\b", stripped, re.IGNORECASE):
        return False

    # Basic length check to avoid tiny fragments like "with SELECT or WITH."
    if len(stripped) < 20:
        return False

    return True


def _generate_with_prompt(prompt: str) -> Tuple[str, str]:
    """
    Helper to generate SQL from a prompt and return both completion and raw output.
    Returns: (completion_text, raw_output_text)
    """
    generator = _get_generator()
    outputs = generator(
        prompt,
        max_new_tokens=settings.max_new_tokens,
        temperature=settings.temperature,
        top_p=settings.top_p,
        do_sample=settings.temperature > 0,
    )
    # text-generation pipeline returns a list of dicts with "generated_text"
    raw_text = outputs[0]["generated_text"]

    # Many HF text-generation models return the full prompt + completion.
    # Strip off the original prompt so we only parse the model's continuation.
    if raw_text.startswith(prompt):
        completion = raw_text[len(prompt) :]
    else:
        completion = raw_text

    return completion, raw_text


def generate_sql(
    nl_query: str,
    schema_text: str,
    history_messages: List[Dict[str, str]],
) -> Tuple[str, str | None, str]:
    """
    2-step orchestrator: generate SQL → validate → repair if needed.

    Step 1: Generate SQL with a short, focused prompt (no history to avoid poisoning).
    Step 2: If validation fails, attempt repair with a second prompt that includes the bad output.
    """
    # Step 1: Initial generation with short prompt (no history)
    initial_prompt = _build_initial_prompt(nl_query=nl_query, schema_text=schema_text)
    completion_1, raw_output_1 = _generate_with_prompt(initial_prompt)
    sql_1 = _extract_sql_from_output(completion_1)

    # Validate step 1 output
    if _is_plausible_sql(sql_1):
        # Success on first try
        explanation = None
        return sql_1, explanation, raw_output_1

    # Step 2: Repair attempt
    repair_prompt = _build_repair_prompt(
        nl_query=nl_query,
        schema_text=schema_text,
        previous_output=completion_1[:500],  # Limit previous output length
    )
    completion_2, raw_output_2 = _generate_with_prompt(repair_prompt)
    sql_2 = _extract_sql_from_output(completion_2)

    # Validate step 2 output
    if _is_plausible_sql(sql_2):
        # Success on repair attempt
        explanation = None
        # Combine both raw outputs for debugging (separated by delimiter)
        combined_raw = f"=== Initial attempt ===\n{raw_output_1}\n\n=== Repair attempt ===\n{raw_output_2}"
        return sql_2, explanation, combined_raw

    # Both attempts failed
    sql = "-- The model did not produce a valid SQL query. Please try rephrasing your question."
    explanation = None
    # Combine both raw outputs for debugging
    combined_raw = f"=== Initial attempt ===\n{raw_output_1}\n\n=== Repair attempt ===\n{raw_output_2}"
    return sql, explanation, combined_raw


