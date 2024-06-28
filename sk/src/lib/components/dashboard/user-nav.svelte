<script lang="ts">
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/";
  import * as Avatar from "$lib/components/ui/avatar/";
  import { Button } from "$lib/components/ui/button";
  import { client, logout } from "$lib/pocketbase";
  import { avatarUrlString } from "$lib/stores/avatar";
  import { getBaseURL } from "$lib/utils/base";

  // if avatarUrlString is not set, fetch it from the server
  export function getAvatarUrl() {
    if (client.authStore.model?.avatar === "") {
      return getBaseURL() + "/pb/avatar/" + client.authStore.model?.name + ".png";
    }
    return $avatarUrlString;
  }
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger asChild let:builder>
    <Button variant="ghost" builders={[builder]} class="relative h-8 w-8 rounded-full">
      <Avatar.Root class="h-8 w-8">
        <Avatar.Image src={getAvatarUrl()} alt="@shadcn" />
        <Avatar.Fallback>
          {client.authStore.model?.name}
        </Avatar.Fallback>
      </Avatar.Root>
    </Button>
  </DropdownMenu.Trigger>
  <DropdownMenu.Content class="w-56" align="end">
    <DropdownMenu.Label class="font-normal">
      <div class="flex flex-col space-y-1">
        <p class="text-sm font-medium leading-none">
          {client.authStore.model?.name}
        </p>
        <p class="text-xs leading-none text-muted-foreground">
          {client.authStore.model?.email}
        </p>
      </div>
    </DropdownMenu.Label>
    <!-- <DropdownMenu.Separator /> -->
    <!-- <DropdownMenu.Group>
      <DropdownMenu.Item>Profile</DropdownMenu.Item>
      <DropdownMenu.Item>Settings</DropdownMenu.Item>
    </DropdownMenu.Group> -->
    <DropdownMenu.Separator />
    <DropdownMenu.Item
      on:click={() => {
        logout();
      }}
    >
      Log out
    </DropdownMenu.Item>
  </DropdownMenu.Content>
</DropdownMenu.Root>
