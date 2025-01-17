<script lang="ts">
  import LogoLight from "$lib/img/logo/logo_frame.png";
  import LogoDark from "$lib/img/logo/logo_frame_white.png";
  import { site } from "$lib/config.js";
  import { UserNav } from "$lib/components/dashboard";
  import { mode, resetMode, setMode } from "mode-watcher";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Checkbox } from "$lib/components/ui/checkbox/index.js";
  import { CalendarIcon, Camera, Moon, Plus, Sun } from "lucide-svelte";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import * as Popover from "$lib/components/ui/popover/index.js";
  import { DateFormatter, type DateValue, getLocalTimeZone } from "@internationalized/date";
  import { Calendar } from "$lib/components/ui/calendar/index.js";
  import { cn } from "$lib/utils";
  import * as Command from "$lib/components/ui/command";
  import { tick } from "svelte";
  import { CaretSort, Check } from "svelte-radix";
  import { customers } from "$lib/stores/data/customers";
  import { expenseTypes } from "$lib/stores/data/expense_types";
  import { client } from "$lib/pocketbase";
  import { toast } from "svelte-sonner";
  import { updateDataStores, UpdateFilterEnum } from "$lib/stores/data/load";
  import * as Dialog from "$lib/components/ui/dialog";
  import { expenses } from "$lib/stores/data/expenses";

  interface ParsedItem {
    value: string;
    label: string;
    frequency: number;
    contextFrequency: number;
  }

  let open = false;
  let dateOpen = false;

  // Swiss German Calendar
  const df = new DateFormatter("de-CH", {
    dateStyle: "long"
  });

  let dateValue: DateValue | undefined = undefined;

  let customerOpen = false;
  let customerValue = "";

  // map $customers id to value and name to label
  let parsedCustomers: ParsedItem[] = [];
  let parsedExpenseTypes: ParsedItem[] = [];

  $: {
    // Count frequency of customers in expenses
    const customerFrequency = $expenses.reduce((acc: Record<string, number>, expense) => {
      const customerId = expense.customer;
      acc[customerId] = (acc[customerId] || 0) + 1;
      return acc;
    }, {});

    // Count frequency of expense types per customer
    const customerTypeFrequency = $expenses.reduce((acc: Record<string, Record<string, number>>, expense) => {
      const customerId = expense.customer;
      const typeId = expense.expense_type;
      if (!acc[customerId]) {
        acc[customerId] = {};
      }
      acc[customerId][typeId] = (acc[customerId][typeId] || 0) + 1;
      return acc;
    }, {});

    // Count frequency of customers per type
    const typeCustomerFrequency = $expenses.reduce((acc: Record<string, Record<string, number>>, expense) => {
      const typeId = expense.expense_type;
      const customerId = expense.customer;
      if (!acc[typeId]) {
        acc[typeId] = {};
      }
      acc[typeId][customerId] = (acc[typeId][customerId] || 0) + 1;
      return acc;
    }, {});

    // Map and sort customers based on context
    parsedCustomers = $customers.map((customer) => ({
      value: customer.id,
      label: customer.name,
      frequency: customerFrequency[customer.id] || 0,
      // If a type is selected, use the frequency of this customer with that type
      contextFrequency: expenseTypeValue ? (typeCustomerFrequency[expenseTypeValue]?.[customer.id] || 0) : 0
    })).sort((a, b) => {
      // If we have a type selected, sort by context frequency first
      if (expenseTypeValue) {
        const contextDiff = b.contextFrequency - a.contextFrequency;
        if (contextDiff !== 0) return contextDiff;
      }
      // Fall back to overall frequency
      return b.frequency - a.frequency;
    });

    // Map and sort expense types based on context
    parsedExpenseTypes = $expenseTypes.map((expenseType) => ({
      value: expenseType.id,
      label: expenseType.name,
      frequency: customerFrequency[expenseType.id] || 0,
      // If a customer is selected, use the frequency of this type with that customer
      contextFrequency: customerValue ? (customerTypeFrequency[customerValue]?.[expenseType.id] || 0) : 0
    })).sort((a, b) => {
      // If we have a customer selected, sort by context frequency first
      if (customerValue) {
        const contextDiff = b.contextFrequency - a.contextFrequency;
        if (contextDiff !== 0) return contextDiff;
      }
      // Fall back to overall frequency
      return b.frequency - a.frequency;
    });
  }

  $: selectedCustomerValue =
    parsedCustomers.find((f) => f.value === customerValue)?.label ?? "Select a customer...";

  function closeCustomerCombobox(triggerId: string) {
    customerOpen = false;
    tick().then(() => {
      document.getElementById(triggerId)?.focus();
    });
  }

  let expenseTypeOpen = false;
  let expenseTypeValue = "";

  $: selectedExpenseTypeValue =
    parsedExpenseTypes.find((f) => f.value === expenseTypeValue)?.label ??
    "Select an expense type...";

  function closeExpenseTypeCombobox(triggerId: string) {
    expenseTypeOpen = false;
    tick().then(() => {
      document.getElementById(triggerId)?.focus();
    });
  }

  let description = "";
  let picture: string | null = null;
  let pictureFile: File;
  let amount = 0;
  let companyCreditCard = false;

  async function handleSubmit(event: Event) {
    event.preventDefault();

    if (!dateValue || !customerValue || !expenseTypeValue || !description || !amount) {
      toast.error("Please fill in all fields.");
      return;
    }

    let formData = new FormData();
    if (pictureFile) {
      formData.append("picture", pictureFile);
    }
    formData.append("datetime", dateValue.toDate(getLocalTimeZone()).toISOString());
    formData.append("customer", customerValue);
    formData.append("expense_type", expenseTypeValue);
    formData.append("description", description);
    formData.append("amount", amount.toString());
    formData.append("company_credit_card", companyCreditCard.toString());
    formData.append("user", client.authStore.model?.id);

    await client
      .collection("expenses")
      .create(formData)
      .then((response) => {
        toast.success("Expense added successfully!");
        dateValue = undefined;
        customerValue = "";
        expenseTypeValue = "";
        description = "";
        picture = null;
        amount = 0;
        companyCreditCard = false;

        // close the drawer
        open = false;

        updateDataStores({
          filter: UpdateFilterEnum.ALL
        }).catch((error) => {
          console.error(error);
        });
      })
      .catch((error) => {
        toast.error("Failed to add expense.");
      });
  }
</script>

<div class="flex-col flex absolute top-0 left-0 right-0 bottom-0 overflow-hidden">
  <div class="border-b">
    <div class="flex h-16 items-center px-8">
      <a class="relative z-20 flex items-center text-lg font-medium mr-6" href="/app">
        {#if $mode === "light"}
          <img src={LogoLight} alt="flexmox logo" class="h-6 w-6 mr-2" />
        {:else}
          <img src={LogoDark} alt="flexmox logo" class="h-6 w-6 mr-2" />
        {/if}
        {site.name}
      </a>
      <!-- <span>
        <DashboardMainNav class="mx-6" />
      </span> -->

      <div class="ml-auto flex items-center space-x-4">
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild let:builder>
            <Button builders={[builder]} variant="outline" size="icon">
              <Sun
                class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0"
              />
              <Moon
                class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100"
              />
              <span class="sr-only">Toggle theme</span>
            </Button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Content align="end">
            <DropdownMenu.Item on:click={() => setMode("light")}>Light</DropdownMenu.Item>
            <DropdownMenu.Item on:click={() => setMode("dark")}>Dark</DropdownMenu.Item>
            <DropdownMenu.Item on:click={() => resetMode()}>System</DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Root>
        <UserNav />
      </div>
    </div>
  </div>
  <div class="absolute top-16 bottom-20 left-0 right-0 overflow-auto overscroll-auto">
    <slot />
  </div>
</div>

<Dialog.Root bind:open>
  <div class="fixed bottom-6 right-1/2 translate-x-1/2">
    <Dialog.Trigger asChild let:builder>
      <Button variant="default" size="lg" builders={[builder]}>
        <Plus class="h-6 w-6" />
        Add Expense
      </Button>
    </Dialog.Trigger>
  </div>
  <Dialog.Content>
    <Dialog.Header class="text-left">
      <Dialog.Title>Add Expense</Dialog.Title>
      <Dialog.Description>Add a new expense to your project</Dialog.Description>
    </Dialog.Header>

    <form class="grid items-start gap-4 px-4" on:submit|preventDefault={handleSubmit}>
      <Popover.Root bind:open={dateOpen} let:ids>
        <Popover.Trigger asChild let:builder>
          <Button
            variant="outline"
            class={cn(
              "w-full justify-start text-left font-normal",
              !dateValue && "text-muted-foreground"
            )}
            builders={[builder]}
          >
            <CalendarIcon class="mr-2 h-4 w-4" />
            {dateValue ? df.format(dateValue.toDate(getLocalTimeZone())) : "Pick a date"}
          </Button>
        </Popover.Trigger>
        <Popover.Content class="w-auto p-0" align="center">
          <Calendar bind:value={dateValue} />
        </Popover.Content>
      </Popover.Root>

      <Popover.Root bind:open={customerOpen} let:ids>
        <Popover.Trigger asChild let:builder>
          <Button
            builders={[builder]}
            variant="outline"
            role="combobox"
            aria-expanded={customerOpen}
            class="w-full justify-between"
          >
            {selectedCustomerValue}
            <CaretSort class="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </Popover.Trigger>
        <Popover.Content class="w-[200px] p-0">
          <Command.Root>
            <Command.Input placeholder="Search customers..." class="h-9" />
            <Command.Empty>No customer found.</Command.Empty>
            <Command.Group>
              {#each parsedCustomers as customer}
                <Command.Item
                  value={customer.label}
                  onSelect={() => {
                    customerValue = customer.value;
                    closeCustomerCombobox(ids.trigger);
                  }}
                >
                  <Check
                    class={cn(
                      "mr-2 h-4 w-4",
                      customerValue !== customer.value && "text-transparent"
                    )}
                  />
                  <span class="flex-1">{customer.label}</span>
                  {#if customer.frequency > 0}
                    <span class="text-xs text-muted-foreground ml-2">{customer.frequency}x</span>
                  {/if}
                </Command.Item>
              {/each}
            </Command.Group>
          </Command.Root>
        </Popover.Content>
      </Popover.Root>

      <Popover.Root bind:open={expenseTypeOpen} let:ids>
        <Popover.Trigger asChild let:builder>
          <Button
            builders={[builder]}
            variant="outline"
            role="combobox"
            aria-expanded={expenseTypeOpen}
            class="w-full justify-between"
          >
            {selectedExpenseTypeValue}
            <CaretSort class="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </Popover.Trigger>
        <Popover.Content class="w-[200px] p-0">
          <Command.Root>
            <Command.Input placeholder="Search expense type..." class="h-9" />
            <Command.Empty>No expense type found.</Command.Empty>
            <Command.Group>
              {#each parsedExpenseTypes as expenseType}
                <Command.Item
                  value={expenseType.label}
                  onSelect={() => {
                    expenseTypeValue = expenseType.value;
                    closeExpenseTypeCombobox(ids.trigger);
                  }}
                >
                  <Check
                    class={cn(
                      "mr-2 h-4 w-4",
                      expenseTypeValue !== expenseType.value && "text-transparent"
                    )}
                  />
                  <span class="flex-1">{expenseType.label}</span>
                  {#if expenseType.frequency > 0}
                    <span class="text-xs text-muted-foreground ml-2">{expenseType.frequency}x</span>
                  {/if}
                </Command.Item>
              {/each}
            </Command.Group>
          </Command.Root>
        </Popover.Content>
      </Popover.Root>
      <div class="grid gap-2">
        <Label for="description">Description</Label>
        <Input id="description" bind:value={description} />
      </div>
      <div class="grid w-full items-center gap-1.5">
        <Label for="picture">Picture</Label>
        <div class="file-input-wrapper">
          <input
            id="picture"
            type="file"
            class="file-input"
            bind:value={picture}
            on:change={(event) => {
              if (event.target) {
                // @ts-expect-error - event.target.files is a FileList
                pictureFile = event.target.files[0];
              }
            }}
          />
          <label for="picture" class="file-input-button">
            <Camera class="h-6 w-6 mr-2" /> Upload Picture
          </label>
        </div>
      </div>
      <div class="grid gap-2">
        <Label for="amount">Amount (KM / CHF)</Label>
        <Input id="amount" type="number" step="0.01" bind:value={amount} />
      </div>
      <div class="items-top flex space-x-2">
        <Checkbox id="terms1" bind:checked={companyCreditCard} />
        <div class="grid gap-1.5 leading-none">
          <Label
            for="terms1"
            class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Company credit card used?
          </Label>
          <p class="text-sm text-muted-foreground">
            If you used your company credit card, please check this box.
          </p>
        </div>
      </div>
      <Button type="submit" class="w-full">Add Expense</Button>
      <Dialog.Close asChild let:builder>
        <Button variant="outline" builders={[builder]}>Cancel</Button>
      </Dialog.Close>
    </form>
  </Dialog.Content>
</Dialog.Root>

<style>
  .file-input-wrapper {
    position: relative;
    display: inline-block;
  }
  .file-input {
    display: none; /* Hide the actual file input */
  }
  .file-input-button {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
  }
</style>
