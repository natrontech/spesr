<script lang="ts">
  import { DropdownMenu as DropdownMenuPrimitive } from "bits-ui";
  import CheckIcon from "@lucide/svelte/icons/check";
  import { cn, type WithoutChild } from "#lib/utils.js";

  let {
    ref = $bindable(null),
    class: className,
    children: childrenProp,
    closeOnSelect = false,
    ...restProps
  }: WithoutChild<DropdownMenuPrimitive.RadioItemProps> = $props();
</script>

<DropdownMenuPrimitive.RadioItem
  bind:ref
  {closeOnSelect}
  data-slot="dropdown-menu-radio-item"
  class={cn(
    "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none data-[disabled]:pointer-events-none data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground data-[disabled]:opacity-50",
    className
  )}
  {...restProps}
>
  {#snippet children({ checked })}
    <span
      class="absolute right-2 flex items-center justify-center pointer-events-none"
      data-slot="dropdown-menu-radio-item-indicator"
    >
      {#if checked}
        <CheckIcon />
      {/if}
    </span>
    {@render childrenProp?.({ checked })}
  {/snippet}
</DropdownMenuPrimitive.RadioItem>
