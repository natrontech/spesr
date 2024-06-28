<script context="module">
  import "../app.css";
  import "../grid.css";
  import { beforeNavigate } from "$app/navigation";
  import { metadata } from "$lib/app/stores";
  import { site } from "$lib/config";
  import { Toaster } from "svelte-sonner";
</script>

<script lang="ts">
  import { ModeWatcher } from "mode-watcher";
  import { onMount } from "svelte";

  $: title = $metadata.title ? $metadata.title + " | " + site.name : site.name;
  $: description = $metadata.description ?? site.description;
  // reset metadata on navigation so that the new page inherits nothing from the old page
  beforeNavigate(() => {
    $metadata = {};
  });

  onMount(() => {
    document.addEventListener(
      "touchstart",
      function (event) {
        if (event.touches.length > 1) {
          event.preventDefault();
        }
      },
      { passive: false }
    );
  });
</script>

<svelte:head>
  <title>{title}</title>
  <meta name="description" content={description} />
</svelte:head>

<main class="h-[calc(100dvh)] overscroll-none">
  <ModeWatcher />
  <Toaster richColors position="top-right" />
  <slot />
</main>
