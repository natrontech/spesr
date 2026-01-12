import { sveltekit } from "@sveltejs/kit/vite";
import type { UserConfig } from "vite";
import fs from "fs";

// detect if we're running inside docker and set the backend accordingly
const pocketbase_url = fs.existsSync("/.dockerenv")
  ? "http://pb:8090" // docker-to-docker
  : "http://localhost:8090"; // localhost-to-localhost

const config: UserConfig = {
  resolve: {
    alias: {
      "@": __dirname + "/src"
    }
  },
  plugins: [sveltekit()],
  server: {
    proxy: {
      "/api": pocketbase_url,
      "/_": pocketbase_url
    },
    headers: {
      "Cross-Origin-Embedder-Policy": "require-corp",
      "Cross-Origin-Opener-Policy": "same-origin"
    },
    hmr: {
      protocol: "ws",
      host: "localhost"
    },
    watch: {
      usePolling: false,
      interval: 100
    }
  }
};

export default config;
