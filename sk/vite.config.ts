import adapter from "@sveltejs/adapter-static";

import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";
import { sveltekit } from "@sveltejs/kit/vite";
import type { UserConfig } from "vite";
import fs from "fs";

// Route backend requests to the Compose service when running inside Docker
const pocketbase_url = fs.existsSync("/.dockerenv") ? "http://pb:8090" : "http://localhost:8090";

const config: UserConfig = {
  resolve: { alias: { "@": import.meta.dirname + "/src" } },
  plugins: [
    tailwindcss(),
    sveltekit({
      preprocess: vitePreprocess(),
      adapter: adapter({
        fallback: "index.html" /* enable SPA mode */
      }),

      onwarn: (warning, handler) => {
        if (warning.code.startsWith("a11y_")) return;
        handler(warning);
      }
    })
  ],
  server: {
    proxy: {
      "/api": pocketbase_url,
      "^/_(?:/|$)": pocketbase_url
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
