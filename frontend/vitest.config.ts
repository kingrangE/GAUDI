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
    // Both foundations' setups: shared (jest-dom + cleanup) and minsu's feature setup.
    setupFiles: ["./vitest.setup.ts", "./feature_dev_prompting/test-setup.ts"],
  },
});
