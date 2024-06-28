<script lang="ts">
  import { cn } from "$lib/utils.js";
  import { page } from "$app/stores";

  let className: string | undefined | null = undefined;
  export { className as class };

  console.log($page.url.pathname);
</script>

<nav class={cn("", className)}>
  <a
    href="/app/analytics"
    class={cn(
      "transition-colors active:text-foreground/80",
      $page.url.pathname === "/app/analytics/" ? "text-foreground" : "text-foreground/60"
    )}
  >
    Analytics
  </a>
</nav>
