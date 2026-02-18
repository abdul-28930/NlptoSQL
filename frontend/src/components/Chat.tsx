import { FormEvent, useEffect, useRef, useState } from "react";
import type { ChatResponse, Message } from "../api/client";

interface Props {
  sessionId: number | null;
}

type Role = Message["role"];

type UIMessage = Message & {
  isStreaming?: boolean;
};

function useReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReduced(mq.matches);
    const listener = (event: MediaQueryListEvent) => setPrefersReduced(event.matches);
    mq.addEventListener("change", listener);
    return () => mq.removeEventListener("change", listener);
  }, []);

  return prefersReduced;
}

export function Chat({ sessionId }: Props) {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSql, setLastSql] = useState<ChatResponse | null>(null);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      setLastSql(null);
      return;
    }
    (async () => {
      try {
        const api = await import("../api/client");
        const data = await api.listMessages(sessionId);
        setMessages(
          data.map((m) => ({
            ...m,
            isStreaming: false,
          })),
        );
      } catch (err) {
        setError((err as Error).message);
      }
    })();
  }, [sessionId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!sessionId || !input.trim()) return;
    setError(null);
    const content = input.trim();
    setInput("");

    const optimisticMessage: UIMessage = {
      id: Date.now(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMessage]);
    setLoading(true);

    try {
      const api = await import("../api/client");
      const res = await api.sendMessage(sessionId, content);
      setLastSql(res);

      const assistantMessage: UIMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: res.sql,
        created_at: new Date().toISOString(),
        isStreaming: !prefersReducedMotion,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-container">
      <MessageList
        sessionId={sessionId}
        messages={messages}
        loading={loading}
      />

      {lastSql && <LatestSqlPanel sql={lastSql.sql} />}

      <Composer
        sessionId={sessionId}
        loading={loading}
        input={input}
        setInput={setInput}
        onSubmit={handleSubmit}
      />

      {error && <div className="error-banner">{error}</div>}
    </div>
  );
}

interface MessageListProps {
  sessionId: number | null;
  messages: UIMessage[];
  loading: boolean;
}

function MessageList({ sessionId, messages, loading }: MessageListProps) {
  const endRef = useRef<HTMLDivElement | null>(null);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (!endRef.current) return;
    endRef.current.scrollIntoView({
      behavior: prefersReducedMotion ? "auto" : "smooth",
      block: "end",
    });
  }, [messages.length, prefersReducedMotion]);

  return (
    <div className="chat-messages" role="log" aria-live="polite">
      {sessionId == null && (
        <div className="text-muted">Select or create a session to start chatting.</div>
      )}
      {sessionId != null && messages.length === 0 && !loading && (
        <div className="text-muted">No messages yet. Ask a question in natural language.</div>
      )}
      {messages.map((m) => (
        <ChatMessage key={m.id} message={m} />
      ))}
      {loading && sessionId != null && (
        <div className="chat-message-row">
          <div className="message-assistant">
            <span>ENGINE</span>
            <span className="ml-2 typing-indicator">
              <span />
              <span />
              <span />
            </span>
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}

interface ChatMessageProps {
  message: UIMessage;
}

function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const label = isUser ? "YOU" : "ENGINE";

  return (
    <div className={`chat-message-row flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={
          isUser
            ? "max-w-[90%] text-xs md:text-sm bg-muted px-3 py-2 border border-border"
            : "max-w-[90%] text-xs md:text-sm border-2 border-border bg-background px-3 py-2"
        }
      >
        <div className="text-[0.6rem] uppercase tracking-[0.2em] text-muted-foreground mb-1">
          {label}
        </div>
        <div className={isUser ? "message-user" : "message-assistant"}>
          {message.content}
        </div>
      </div>
    </div>
  );
}

interface LatestSqlPanelProps {
  sql: string;
}

function LatestSqlPanel({ sql }: LatestSqlPanelProps) {
  function copySql() {
    if (!sql) return;
    navigator.clipboard.writeText(sql).catch(() => {
      // ignore copy errors
    });
  }

  return (
    <div className="mt-3">
      <div className="latest-sql-header">
        <span className="latest-sql-label">Latest SQL</span>
        <button className="button secondary" type="button" onClick={copySql}>
          Copy
        </button>
      </div>
      <div className="sql-block">{sql}</div>
    </div>
  );
}

interface ComposerProps {
  sessionId: number | null;
  loading: boolean;
  input: string;
  setInput: (v: string) => void;
  onSubmit: (e: FormEvent) => void;
}

function Composer({ sessionId, loading, input, setInput, onSubmit }: ComposerProps) {
  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      // Delegate to form submit
      const form = e.currentTarget.form;
      form?.requestSubmit();
    }
  }

  return (
    <div>
      {sessionId != null && input.length === 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {[
            "Total revenue per day for the last 30 days",
            "Top 10 customers by total spend",
            "Orders by status for the last 90 days",
          ].map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              className="text-xs uppercase tracking-tight border border-border px-2 py-1 bg-background hover:bg-muted"
              onClick={() => setInput(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
      <form className="chat-input-container" onSubmit={onSubmit} aria-label="Ask a question">
        <textarea
          className="text-input min-h-[3rem] max-h-[10rem] resize-none"
          placeholder={
            sessionId ? "Ask a question about your data in natural language..." : "Create a session first"
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sessionId == null || loading}
          aria-label="Ask a question in natural language"
        />
        <button className="button" type="submit" disabled={sessionId == null || loading}>
          {loading ? "Thinking..." : "Send"}
        </button>
      </form>
    </div>
  );
}

