<script lang="ts">
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Table from "$lib/components/ui/table";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { customers } from "$lib/stores/data/customers";
  import { client } from "$lib/pocketbase";
  import { toast } from "svelte-sonner";
  import { updateDataStores, UpdateFilterEnum } from "$lib/stores/data/load";
  import { Edit2, Save, X, Search } from "lucide-svelte";
  import type { CustomersResponse } from "$lib/pocketbase/generated-types";

  export let open = false;

  let newCustomerName = "";
  let editingCustomerId: string | null = null;
  let editingCustomerName = "";
  let searchQuery = "";

  $: filteredCustomers = $customers.filter((customer) => {
    if (!searchQuery.trim()) return true;
    const name = (customer.name || "").toLowerCase();
    return name.includes(searchQuery.toLowerCase().trim());
  });

  async function handleCreate() {
    if (!newCustomerName.trim()) {
      toast.error("Customer name cannot be empty");
      return;
    }

    try {
      await client.collection("customers").create({
        name: newCustomerName.trim()
      });
      toast.success("Customer created successfully!");
      newCustomerName = "";
      await updateDataStores({ filter: UpdateFilterEnum.ALL });
    } catch (error) {
      console.error(error);
      toast.error("Failed to create customer");
    }
  }

  function startEdit(customer: CustomersResponse) {
    editingCustomerId = customer.id;
    editingCustomerName = customer.name || "";
  }

  function cancelEdit() {
    editingCustomerId = null;
    editingCustomerName = "";
  }

  async function handleUpdate(customerId: string) {
    if (!editingCustomerName.trim()) {
      toast.error("Customer name cannot be empty");
      return;
    }

    try {
      await client.collection("customers").update(customerId, {
        name: editingCustomerName.trim()
      });
      toast.success("Customer updated successfully!");
      editingCustomerId = null;
      editingCustomerName = "";
      await updateDataStores({ filter: UpdateFilterEnum.ALL });
    } catch (error) {
      console.error(error);
      toast.error("Failed to update customer");
    }
  }
</script>

<Dialog.Root bind:open>
  <Dialog.Content
    class="max-w-2xl w-[calc(100vw-2rem)] sm:w-full max-h-[90vh] sm:max-h-[85vh] flex flex-col"
  >
    <Dialog.Header class="flex-shrink-0">
      <Dialog.Title>Manage Customers</Dialog.Title>
      <Dialog.Description>Create and edit customer entries</Dialog.Description>
    </Dialog.Header>

    <div class="flex-1 overflow-y-auto min-h-0 space-y-4 sm:space-y-6">
      <div class="space-y-2 flex-shrink-0">
        <Label for="new-customer-name">Add New Customer</Label>
        <div class="flex flex-col sm:flex-row gap-2">
          <Input
            id="new-customer-name"
            placeholder="Enter customer name"
            bind:value={newCustomerName}
            class="flex-1"
            on:keydown={(e) => {
              if (e.key === "Enter") {
                handleCreate();
              }
            }}
          />
          <Button on:click={handleCreate} class="w-full sm:w-auto">Add</Button>
        </div>
      </div>

      <div class="space-y-2 flex-shrink-0">
        <Label for="search-customers">Search Customers</Label>
        <div class="relative">
          <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            id="search-customers"
            type="text"
            placeholder="Search customers..."
            class="pl-8"
            bind:value={searchQuery}
          />
        </div>
      </div>

      <div class="rounded-md border overflow-hidden flex-1 min-h-0 flex flex-col">
        <div class="overflow-auto flex-1">
          <Table.Root>
            <Table.Header class="sticky top-0 bg-background z-10">
              <Table.Row>
                <Table.Head class="min-w-[150px]">Name</Table.Head>
                <Table.Head class="w-[100px] sm:w-[120px]">Actions</Table.Head>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {#if filteredCustomers.length === 0}
                <Table.Row>
                  <Table.Cell colspan={2} class="text-center text-muted-foreground py-8">
                    {#if searchQuery.trim()}
                      No customers found matching "{searchQuery}"
                    {:else}
                      No customers found
                    {/if}
                  </Table.Cell>
                </Table.Row>
              {:else}
                {#each filteredCustomers as customer}
                  <Table.Row>
                    <Table.Cell class="min-w-[150px]">
                      {#if editingCustomerId === customer.id}
                        <Input
                          bind:value={editingCustomerName}
                          on:keydown={(e) => {
                            if (e.key === "Enter") {
                              handleUpdate(customer.id);
                            } else if (e.key === "Escape") {
                              cancelEdit();
                            }
                          }}
                          class="w-full"
                        />
                      {:else}
                        <span class="break-words">{customer.name || ""}</span>
                      {/if}
                    </Table.Cell>
                    <Table.Cell>
                      <div class="flex justify-end gap-1 sm:gap-2">
                        {#if editingCustomerId === customer.id}
                          <Button
                            variant="ghost"
                            size="icon"
                            class="h-9 w-9 sm:h-10 sm:w-10"
                            on:click={() => handleUpdate(customer.id)}
                          >
                            <Save class="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            class="h-9 w-9 sm:h-10 sm:w-10"
                            on:click={cancelEdit}
                          >
                            <X class="h-4 w-4" />
                          </Button>
                        {:else}
                          <Button
                            variant="ghost"
                            size="icon"
                            class="h-9 w-9 sm:h-10 sm:w-10"
                            on:click={() => startEdit(customer)}
                          >
                            <Edit2 class="h-4 w-4" />
                          </Button>
                        {/if}
                      </div>
                    </Table.Cell>
                  </Table.Row>
                {/each}
              {/if}
            </Table.Body>
          </Table.Root>
        </div>
      </div>
    </div>

    <Dialog.Footer class="flex-shrink-0 flex-col sm:flex-row gap-2 mt-4">
      <Dialog.Close asChild let:builder>
        <Button variant="outline" builders={[builder]} class="w-full sm:w-auto">Close</Button>
      </Dialog.Close>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
