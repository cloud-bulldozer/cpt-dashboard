import { defineConfig, loadEnv } from "vite";
import path from "path";
import react from "@vitejs/plugin-react";
// https://vitejs.dev/config/

export default ({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_")

  return defineConfig({
    plugins: [react()],
    esbuild: {
      jsxFactory: "React.createElement",
      jsxFragment: "React.Fragment",
    },
    resolve: {
      alias: [{ find: "@", replacement: path.resolve(__dirname, "src") }],
      extensions: [".js", ".json", ".jsx", ".mjs"],
    },
    server: {
      port: 3000,
      open: false,
      fs: {
        cachedChecks: false,
      },
      proxy: {
        "/api": {
          target: env.VITE_API_PROXY_TARGET,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, "/api"),
        }
      }
    },
    test: {
      includeSource: ["src/**/*.{js}"],
    },
    defined: {
      // allows bundler eliminate dead code
      "import.meta.vistest": "defined"
    }
  });
}


