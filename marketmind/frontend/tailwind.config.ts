import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: "#0a0e12",
          panel: "#10161c",
          border: "#1e2833",
          text: "#c8d3dc",
          muted: "#5c6b78",
        },
        up: "#26d07c",
        down: "#f0554b",
        accent: "#3ba7ff",
        warn: "#e8b339",
      },
      fontFamily: {
        mono: ["'IBM Plex Mono'", "'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["'Inter'", "ui-sans-serif", "system-ui"],
      },
      fontSize: {
        tick: ["0.8125rem", { lineHeight: "1.1rem", letterSpacing: "0.01em" }],
      },
    },
  },
  plugins: [],
};

export default config;
