import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Blue primary accent (mockup's run button).
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          500: "#5b73e8",
          600: "#3b5bdb",
          700: "#314bbd",
        },
        // Dark "ink" surface — the only dark zone (code / agent output).
        ink: {
          900: "#0f1115",
          800: "#181b22",
          700: "#20242e",
          600: "#2a2f3a",
          text: "#e7e9ee",
          muted: "#9aa3b2",
        },
        good: {
          50: "#ecfdf5",
          100: "#d1fae5",
          600: "#059669",
          700: "#047857",
        },
        bad: {
          50: "#fef2f2",
          100: "#fee2e2",
          600: "#dc2626",
          700: "#b91c1c",
        },
      },
      boxShadow: {
        panel: "0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
