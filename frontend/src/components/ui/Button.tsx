import { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "outline" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  const base =
    "inline-flex items-center justify-center uppercase tracking-tighter font-bold h-14 px-8 text-xs transition-transform duration-200 active:scale-95 disabled:opacity-60 disabled:pointer-events-none";

  const variants: Record<Variant, string> = {
    primary: "bg-accent text-accent-foreground border-2 border-accent hover:scale-105",
    outline: "bg-transparent text-foreground border-2 border-border hover:bg-foreground hover:text-black",
    ghost: "bg-transparent text-foreground border-none hover:text-accent",
  };

  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />;
}

