import { FormEvent, useState } from "react";
import type { Schema } from "../api/client";

interface Props {
  onCreated(schema: Schema): void;
}

export function SchemaForm({ onCreated }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [rawSchema, setRawSchema] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name || !rawSchema) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await import("../api/client").then((m) =>
        m.createSchema({
          name,
          description: description || undefined,
          raw_schema: rawSchema,
        }),
      );
      onCreated(res);
      setName("");
      setDescription("");
      setRawSchema("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="schema-form" onSubmit={handleSubmit}>
      <div>
        <input
          placeholder="Schema name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      <div>
        <input
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      <div>
        <textarea
          placeholder="Paste your table schema here (DDL or description)"
          value={rawSchema}
          onChange={(e) => setRawSchema(e.target.value)}
        />
      </div>
      {error && <div className="error-text-small">{error}</div>}
      <button className="button" type="submit" disabled={submitting}>
        {submitting ? "Saving..." : "Save schema"}
      </button>
    </form>
  );
}

