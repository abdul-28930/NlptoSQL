import { FormEvent, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthLayout } from "../layouts/AuthLayout";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/app");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Log Back In"
      subtitle="Pick up your last conversation with your data. Context and SQL are right where you left them."
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label
            htmlFor="login-email"
            className="text-[0.7rem] uppercase tracking-[0.2em] text-muted-foreground"
          >
            Email
          </label>
          <input
            type="email"
            id="login-email"
            className="w-full bg-transparent border-b-2 border-border focus:border-accent outline-none text-xl md:text-2xl py-3"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </div>
        <div className="space-y-2">
          <label
            htmlFor="login-password"
            className="text-[0.7rem] uppercase tracking-[0.2em] text-muted-foreground"
          >
            Password
          </label>
          <input
            type="password"
            id="login-password"
            className="w-full bg-transparent border-b-2 border-border focus:border-accent outline-none text-xl md:text-2xl py-3"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>
        {error && <div className="error-text-small">{error}</div>}
        <button className="button w-full h-14 text-sm" type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
        <p className="text-muted-small">
          Need an account?{" "}
          <Link to="/signup" className="underline">
            Create one
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}

