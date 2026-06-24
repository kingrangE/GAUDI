import type { Config } from "tailwindcss";

/*
 * minsu's "judge console" palette is the standard (see globals.css / workspace.module.css).
 * Color KEY names are kept stable (brand/ink/good/bad) so existing components inherit the
 * new look without class churn; only the values are retuned to minsu's tokens.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Light cool-gray chrome.
        paper: "#eceef3",
        surface: "#ffffff",
        line: "#dde1e9",

        // Indigo accent (run button, kickers, focus).
        brand: {
          50: "#eef0fb",
          100: "#dcdef6",
          200: "#b9bdec",
          300: "#9a9ee4",
          500: "#4a47cf",
          600: "#3a36c4",
          700: "#302da6",
        },
        // Dark "ink" code/output well — the only dark zone.
        ink: {
          900: "#14161c", // code-bg
          800: "#1b1e26",
          700: "#23262f", // head border / turn tag bg
          600: "#2a2e38",
          text: "#e6e8ee",
          muted: "#8b91a0",
          soft: "#5b6270",
          faint: "#8b91a0",
        },
        // Verdict colors.
        good: { 50: "#e9f7ef", 100: "#cdebd9", 600: "#1f9d5a", 700: "#178048" },
        bad: { 50: "#fbecec", 100: "#f5d2d2", 600: "#d23b3b", 700: "#b32f2f" },
        warn: { 50: "#f9f1df", 100: "#efdcb4", 600: "#c08218", 700: "#9d6a13" },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"SF Mono"', "ui-monospace", "Menlo", "Consolas", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 2px 0 rgb(20 22 28 / 0.04), 0 1px 3px 0 rgb(20 22 28 / 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
