<script lang="ts">
  import Button from "$lib/components/ui/button/button.svelte";
  import { Input } from "../ui/input";
  import { cn } from "$lib/utils.js";
  import { Label } from "../ui/label";
  import { Github, LoaderCircle } from "lucide-svelte";
  import { alertOnFailure } from "$lib/pocketbase/ui";
  import type { AuthProviderInfo } from "pocketbase";
  import { client, login } from "$lib/pocketbase";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";
  import { avatarUrlString } from "$lib/stores/avatar";
  import { avatarUrl } from "$lib/utils/user.utils";
  import { getBaseURL } from "$lib/utils/base";

  let className: string | undefined | null = undefined;
  export { className as class };

  let isLoading = false;

  const DEFAULTS = {
    email: "",
    password: ""
  };

  let user = { ...DEFAULTS };

  async function submit() {
    isLoading = true;

    await alertOnFailure(async function () {
      await login(user.email, user.password);
      toast.success("Logged in successfully!");
      $avatarUrlString = getBaseURL() + avatarUrl();
      goto("/app");
    }).finally(() => {
      isLoading = false;
    });
  }

  let authProviders: AuthProviderInfo[];

  async function getAuthMethods() {
    const response = await client.collection("users").listAuthMethods();
    authProviders = response.authProviders;
  }

  onMount(() => {
    getAuthMethods();
  });

  function handleProviderLogin(provider: AuthProviderInfo) {
    const w = window.open(""); // Eagerly open a new window
    if (!w) {
      toast.error("Failed to open a new window");
      return;
    }

    client
      .collection("users")
      .authWithOAuth2({
        provider: provider.name,
        urlCallback: (url) => {
          w.location.href = url;
        }
      })
      .then(async (response) => {
        const meta: any = response.meta;

        if (meta.isNew) {
          const formData = new FormData();

          const avatarResponse = await fetch(meta.avatarUrl);

          if (avatarResponse.ok && meta.avatarUrl) {
            const file = await avatarResponse.blob();
            formData.append("avatar", file);
          }

          formData.append("name", meta.name);

          await client.collection("users").update(client.authStore.model?.id, formData);
        }

        toast.success("Logged in successfully!");
        $avatarUrlString = getBaseURL() + avatarUrl();
        goto("/app");
      })
      .catch(() => {
        toast.error("Failed to log in");
      });
  }
</script>

<div class={cn("grid gap-6", className)} {...$$restProps}>
  <form on:submit|preventDefault={submit}>
    <div class="grid gap-2">
      <div class="grid gap-1">
        <Label class="sr-only" for="email">Email</Label>
        <Input
          id="email"
          placeholder="name@example.com"
          type="email"
          autocapitalize="none"
          autocomplete="email"
          autocorrect="off"
          bind:value={user.email}
          disabled={isLoading}
        />
        <Label class="sr-only" for="password">Password</Label>
        <Input
          id="password"
          placeholder="password"
          type="password"
          autocapitalize="none"
          autocomplete="current-password"
          autocorrect="off"
          bind:value={user.password}
          disabled={isLoading}
        />
      </div>
      <Button type="submit" disabled={isLoading}>
        {#if isLoading}
          <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
        {/if}
        Log in
      </Button>
    </div>
  </form>
  {#if authProviders?.length > 0}
    <div class="relative">
      <div class="absolute inset-0 flex items-center">
        <span class="w-full border-t" />
      </div>
      <div class="relative flex justify-center text-xs uppercase">
        <span class="bg-background px-2 text-muted-foreground"> Or continue with </span>
      </div>
    </div>
  {/if}
  <div class="grid gap-2 grid-cols-1">
    {#if authProviders?.find((provider) => provider.name === "github")}
      <Button
        variant="outline"
        type="button"
        disabled={isLoading}
        on:click={() => {
          const temp = authProviders.find((provider) => provider.name === "github");
          if (temp) {
            handleProviderLogin(temp);
          }
        }}
      >
        {#if isLoading}
          <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
        {:else}
          <Github class="mr-2" />
        {/if}
        GitHub
      </Button>
    {/if}
    {#if authProviders?.find((provider) => provider.name === "google")}
      <Button
        variant="outline"
        type="button"
        disabled={isLoading}
        on:click={() => {
          const temp = authProviders.find((provider) => provider.name === "google");
          if (temp) {
            handleProviderLogin(temp);
          }
        }}
      >
        {#if isLoading}
          <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
        {:else}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            fill="currentColor"
            class="bi bi-google mr-2"
            viewBox="0 0 16 16"
          >
            <path
              d="M15.545 6.558a9.42 9.42 0 0 1 .139 1.626c0 2.434-.87 4.492-2.384 5.885h.002C11.978 15.292 10.158 16 8 16A8 8 0 1 1 8 0a7.689 7.689 0 0 1 5.352 2.082l-2.284 2.284A4.347 4.347 0 0 0 8 3.166c-2.087 0-3.86 1.408-4.492 3.304a4.792 4.792 0 0 0 0 3.063h.003c.635 1.893 2.405 3.301 4.492 3.301 1.078 0 2.004-.276 2.722-.764h-.003a3.702 3.702 0 0 0 1.599-2.431H8v-3.08h7.545z"
            />
          </svg>
        {/if}
        Google
      </Button>
    {/if}
    {#if authProviders?.find((provider) => provider.name === "microsoft")}
      <Button
        variant="outline"
        type="button"
        disabled={isLoading}
        on:click={() => {
          const temp = authProviders.find((provider) => provider.name === "microsoft");
          if (temp) {
            handleProviderLogin(temp);
          }
        }}
      >
        {#if isLoading}
          <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
        {:else}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            fill="currentColor"
            class="bi bi-microsoft mr-2"
            viewBox="0 0 16 16"
          >
            <path
              d="M7.462 0H0v7.19h7.462V0zM16 0H8.538v7.19H16V0zM7.462 8.211H0V16h7.462V8.211zm8.538 0H8.538V16H16V8.211z"
            />
          </svg>
        {/if}
        Microsoft
      </Button>
    {/if}
  </div>
</div>
