<script lang="ts">
  import { Drawer as DrawerPrimitive } from "vaul-svelte";
  import { cn } from "#lib/utils.js";
  import type { WithoutChildrenOrChild } from "#lib/utils.js";
  import DrawerOverlay from "./drawer-overlay.svelte";
  const DrawerPortal = DrawerPrimitive.Portal;
  import type { ComponentProps } from "svelte";

  let {
    ref = $bindable(null),
    class: className,
    portalProps,
    children,
    ...restProps
  }: DrawerPrimitive.ContentProps & {
    portalProps?: WithoutChildrenOrChild<ComponentProps<typeof DrawerPortal>>;
  } = $props();
</script>

<DrawerPortal {...portalProps}>
  <DrawerOverlay />
  <DrawerPrimitive.Content
    bind:ref
    data-slot="drawer-content"
    class={cn(
      "fixed inset-x-0 bottom-0 z-50 mt-24 flex h-auto flex-col rounded-t-[10px] border bg-background",
      className
    )}
    {...restProps}
  >
    <div
      class="bg-muted mx-auto mt-4 hidden h-1 w-[100px] shrink-0 rounded-full mx-auto hidden shrink-0 group-data-[vaul-drawer-direction=bottom]/drawer-content:block"
    ></div>
    {@render children?.()}
  </DrawerPrimitive.Content>
</DrawerPortal>
