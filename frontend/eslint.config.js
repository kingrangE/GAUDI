import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["node_modules", ".next", "dist", "coverage", "next-env.d.ts"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    // TS already verifies identifiers; core no-undef would false-flag browser/node globals.
    files: ["**/*.{ts,tsx}"],
    rules: { "no-undef": "off" },
  },
);
