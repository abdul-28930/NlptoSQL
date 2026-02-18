import { Session, Schema } from "../api/client";

interface Props {
  sessions: Session[];
  activeSessionId: number | null;
  onSelect(sessionId: number): void;
  onCreate(schemaId: number | null): void;
  schemas: Schema[];
  activeSchemaId: number | null;
  onChangeSchema(schemaId: number | null): void;
}

export function SessionList({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
  schemas,
  activeSchemaId,
  onChangeSchema,
}: Props) {
  return (
    <div>
      <h2 className="section-title">Sessions</h2>
      <button className="button button-fullwidth button-spaced" onClick={() => onCreate(activeSchemaId)}>
        New session
      </button>
      <div>
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`session-item ${s.id === activeSessionId ? "active" : ""}`}
            onClick={() => onSelect(s.id)}
          >
            {s.title || `Session #${s.id}`}
          </div>
        ))}
        {sessions.length === 0 && <div className="text-muted-small">No sessions yet.</div>}
      </div>

      <hr className="divider" />

      <h2 className="section-title">Active schema</h2>
      <select
        className="select-input"
        aria-label="Active schema"
        value={activeSchemaId ?? ""}
        onChange={(e) => {
          const value = e.target.value;
          onChangeSchema(value ? Number(value) : null);
        }}
      >
        <option value="">None</option>
        {schemas.map((schema) => (
          <option key={schema.id} value={schema.id}>
            {schema.name}
          </option>
        ))}
      </select>
    </div>
  );
}

