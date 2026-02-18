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


def _build_prompt(
    nl_query: str,
    schema_text: str,
    history_messages: List[Dict[str, str]],
) -> str:
    system_instruction = (
        "You are an assistant that converts natural language questions "
        "to syntactically correct SQL for the given database schema.\n"
        "Follow these rules strictly:\n"
        "1. Use only the tables and columns that exist in the schema.\n"
        "2. Do not invent columns or tables.\n"
        "3. Return only a single SQL query.\n"
        "4. Wrap the SQL in a Markdown ```sql code block.\n"
    )

    schema_block = f"SCHEMA:\n{schema_text.strip()}\n\n" if schema_text.strip() else ""

    history_block_lines: list[str] = []
    for msg in history_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "assistant":
            prefix = "Assistant"
        elif role == "system":
            prefix = "System"
        else:
            prefix = "User"
        history_block_lines.append(f"{prefix}: {content}")
    history_block = ""
    if history_block_lines:
        history_block = "Conversation history (last messages):\n" + "\n".join(history_block_lines) + "\n\n"

    user_instruction = (
        f"User question: {nl_query}\n\n"
        "Return only the SQL query in a ```sql code block. "
        "Do not add explanations or comments outside the code block."
    )

    return f"{system_instruction}\n{schema_block}{history_block}{user_instruction}"


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

    # Require at least one structural SQL keyword to avoid short fragments
    # like "with SELECT or WITH." being treated as valid.
    structural_keywords = (
        " from ",
        " where ",
        " join ",
        " group by ",
        " order by ",
        " having ",
        " limit ",
        " offset ",
        " union ",
        " intersect ",
        " except ",
    )
    if not any(kw in lowered for kw in structural_keywords):
        return False

    return True


def generate_sql(
    nl_query: str,
    schema_text: str,
    history_messages: List[Dict[str, str]],
) -> Tuple[str, str | None, str]:
    """
    Call the local Hugging Face small language model to generate SQL.
    """
    prompt = _build_prompt(nl_query=nl_query, schema_text=schema_text, history_messages=history_messages)

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

    # Extract SQL only
    sql = _extract_sql_from_output(raw_text)

    # If we failed to find a plausible SQL statement (e.g. the model just
    # echoed the prompt or returned plain text / meta instructions), avoid
    # sending that back to the UI as "SQL".
    if not _is_plausible_sql(sql):
        sql = "-- The model did not produce a valid SQL query. Please try rephrasing your question."

    explanation = None

    return sql, explanation, raw_text


