import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        background: "#09090B",
        foreground: "#FAFAFA",
        muted: "#27272A",
        "muted-foreground": "#A1A1AA",
        accent: "#DFE104",
        "accent-foreground": "#000000",
        border: "#3F3F46",
      },
      fontFamily: {
        sans: ["Space Grotesk", "system-ui", "sans-serif"],
      },
      fontSize: {
        hero: "clamp(3rem,12vw,14rem)",
      },
      maxWidth: {
        "screen-kinetic": "95vw",
      },
    },
  },
  plugins: [],
};

export default config;

