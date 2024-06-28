import { getBaseURL } from "$lib/utils/base";
import { createFetchWithAuth } from "./custom-fetch";
import type { paths } from "./generated-sdk";
import createClient from "openapi-fetch";

let authToken: string | null = null;

// Check if running in the browser before accessing localStorage
if (typeof window !== "undefined") {
  const storedAuth = localStorage.getItem("pocketbase_auth");
  if (storedAuth) {
    authToken = JSON.parse(storedAuth).token;
  }
}

const customFetch = createFetchWithAuth(authToken || "");

export let { GET, POST, PATCH, PUT, DELETE, HEAD, TRACE, OPTIONS } = createClient<paths>({
  baseUrl: getBaseURL(),
  fetch: customFetch
});
