import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    css: false,
    // Shared setup (jest-dom + cleanup) plus each minsu feature's own setup file.
    setupFiles: [
      "./vitest.setup.ts",
      "./feature_dev_prompting/test-setup.ts",
      "./feature_spec_design/test-setup.ts",
      "./feature_context_engineering/test-setup.ts",
    ],
  },
});
