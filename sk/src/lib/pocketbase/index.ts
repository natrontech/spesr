import PocketBase from "pocketbase";
import { writable } from "svelte/store";
import { goto } from "$app/navigation";
import type { TypedPocketBase } from "./generated-types";
import { toast } from "svelte-sonner";
import { getBaseURL } from "$lib/utils/base";

// if localhost, use the default port then use http://localhost:8090 as the base URL if not use the current URL
export const client = new PocketBase(getBaseURL()) as TypedPocketBase;

export const currentUser = writable(client.authStore.model);

export async function login(
  email: string,
  password: string,
  register = false,
  rest: { [key: string]: unknown } = {}
) {
  if (register) {
    const user = { ...rest, email, password, confirmPassword: password };
    await client.collection("users").create(user);
  }
  await client.collection("users").authWithPassword(email, password);
}

export function logout() {
  client.authStore.clear();
  currentUser.set(null);
  goto("/login/");
  toast.success("Successfully logged out.");
}
