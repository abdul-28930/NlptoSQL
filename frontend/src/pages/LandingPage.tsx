import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <section className="w-full max-w-screen-kinetic space-y-10">
          <div className="space-y-6">
            <h1 className="text-hero font-bold uppercase tracking-tighter leading-[0.8]">
              Speak SQL
            </h1>
            <p className="max-w-2xl text-lg md:text-2xl text-muted-foreground">
              Turn natural language into schema-aware SQL. Keep your data where it is—
              just change how you talk to it.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/signup" className="button h-14 text-sm flex items-center justify-center">
                Get started
              </Link>
              <Link
                to="/login"
                className="button secondary h-14 text-sm flex items-center justify-center uppercase tracking-tight"
              >
                Log in
              </Link>
            </div>
          </div>

          <div className="border-t border-border pt-6 grid md:grid-cols-3 gap-6 text-xs uppercase tracking-[0.2em] text-muted-foreground">
            <div>
              <div className="text-2xl md:text-4xl font-bold text-foreground mb-1">Natural</div>
              <div>Questions, not joins</div>
            </div>
            <div>
              <div className="text-2xl md:text-4xl font-bold text-foreground mb-1">Schema</div>
              <div>Inline context aware</div>
            </div>
            <div>
              <div className="text-2xl md:text-4xl font-bold text-foreground mb-1">Local</div>
              <div>Small model, big queries</div>
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t border-border px-4 py-4 text-[0.7rem] text-muted-foreground flex justify-between">
        <span>NL → SQL ENGINE</span>
        <span>Built for people who think in questions</span>
      </footer>
    </div>
  );
}

