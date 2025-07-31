import codeCoverageTask from "@cypress/code-coverage/task.js";
import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: process.env.GUI_BASE_URL || "http://localhost:3000",
    setupNodeEvents(on, config) {
      // implement node event listeners here
      codeCoverageTask(on, config);
      return config;
    },
  },

  component: {
    devServer: {
      framework: "react",
      bundler: "vite",
    },
  },
});
