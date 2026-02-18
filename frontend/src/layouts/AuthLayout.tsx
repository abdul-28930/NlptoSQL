import { ReactNode } from "react";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-4">
      <div className="max-w-screen-kinetic w-full grid md:grid-cols-2 gap-12 py-16">
        <div className="flex flex-col justify-center">
          <h1 className="text-hero font-bold uppercase tracking-tighter leading-[0.8]">
            {title}
          </h1>
          <p className="mt-4 text-lg md:text-xl text-muted-foreground max-w-2xl">
            {subtitle}
          </p>
        </div>
        <div className="border-2 border-border p-8 md:p-10 flex flex-col gap-6 bg-background">
          {children}
        </div>
      </div>
    </div>
  );
}

