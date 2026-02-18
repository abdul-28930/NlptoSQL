import { useEffect, useState } from "react";
import {
  bootstrapUser,
  createSession,
  listSchemas,
  listSessions,
  type Schema,
  type Session,
} from "./api/client";
import { SchemaForm } from "./components/SchemaForm";
import { SessionList } from "./components/SessionList";
import { Chat } from "./components/Chat";

export function AppShell() {
  const [ready, setReady] = useState(false);
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [activeSchemaId, setActiveSchemaId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        await bootstrapUser();
        const [schemaList, sessionList] = await Promise.all([listSchemas(), listSessions()]);
        setSchemas(schemaList);
        setSessions(sessionList);
        if (sessionList.length > 0) {
          setActiveSessionId(sessionList[0].id);
          setActiveSchemaId(sessionList[0].schema_id ?? null);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setReady(true);
      }
    })();
  }, []);

  async function handleCreateSession(initialSchemaId: number | null) {
    try {
      const session = await createSession({
        title: "",
        schema_id: initialSchemaId ?? undefined,
      });
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setActiveSchemaId(session.schema_id ?? null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function handleSchemaCreated(schema: Schema) {
    setSchemas((prev) => [...prev, schema]);
    setActiveSchemaId(schema.id);
  }

  function handleChangeSchema(schemaId: number | null) {
    setActiveSchemaId(schemaId);
  }

  return (
    <div className="app-root">
      <aside className="sidebar">
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={setActiveSessionId}
          onCreate={handleCreateSession}
          schemas={schemas}
          activeSchemaId={activeSchemaId}
          onChangeSchema={handleChangeSchema}
        />
        <SchemaForm onCreated={handleSchemaCreated} />
      </aside>
      <main className="main">
        <header className="header">
          <h1 className="header-title">NL to SQL</h1>
          {error && <div className="error-text">{error}</div>}
        </header>
        {!ready ? (
          <div className="loading-text">Loading...</div>
        ) : (
          <Chat sessionId={activeSessionId} />
        )}
      </main>
    </div>
  );
}

