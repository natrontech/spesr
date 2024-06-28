import { browser } from "$app/environment";
import { client } from "$lib/pocketbase";
import { goto } from "$app/navigation";

// turn off SSR - we're JAMstack here
export const ssr = false;
// Prerendering turned off. Turn it on if you know what you're doing.
export const prerender = false;
// trailing slashes make relative paths much easier
export const trailingSlash = "always";

export const load = async ({ url }) => {
  const { pathname } = url;

  if (browser) {
    if (client.authStore.model && client.authStore.isValid) {
      if (pathname === "/login/" || pathname === "/signup/" || pathname === "/") {
        goto("/app/");
      }
    } else {
      // if pathname contains "/app" and user is not logged in, redirect to login
      client.authStore.clear();
      if (pathname.includes("/app")) {
        goto("/login/");
      }
    }
  }

  return {
    pathname
  };
};
