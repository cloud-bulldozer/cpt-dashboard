import { defineConfig } from "cypress";


export default defineConfig({
  e2e: {
    baseUrl: process.env.GUI_BASE_URL || "http://localhost:3000",
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },

  component: {
    devServer: {
      framework: "react",
      bundler: "vite",
    },
  },
});
