<script lang="ts">
  import Button from "$lib/components/ui/button/button.svelte";
  import { expenses } from "$lib/stores/data/expenses";
  import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
  import { client } from "$lib/pocketbase";
  import { updateDataStores, UpdateFilterEnum } from "$lib/stores/data/load";
  import { toast } from "svelte-sonner";
  import { Lightbox } from "svelte-lightbox";
  import { getFileUrl } from "$lib/utils/file.utils";
  import { saveAs } from "file-saver";
  import Papa from "papaparse";
  import * as Drawer from "$lib/components/ui/drawer/index.js";
  import { writable } from "svelte/store";
  import * as Table from "$lib/components/ui/table";
  import { Input } from "$lib/components/ui/input";
  import {
    DateFormatter,
    getLocalTimeZone,
    parseDate,
    type DateValue
  } from "@internationalized/date";
  import { customers } from "$lib/stores/data/customers";
  import { expenseTypes } from "$lib/stores/data/expense_types";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Label } from "$lib/components/ui/label";
  import { Checkbox } from "$lib/components/ui/checkbox";
  import {
    Camera,
    Search,
    ArrowUpDown,
    Calendar as CalendarIcon,
    ChevronDown,
    ChevronUp,
    Edit2,
    Trash2,
    Check
  } from "lucide-svelte";
  import { Card } from "$lib/components/ui/card";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import * as Popover from "$lib/components/ui/popover/index.js";
  import * as Command from "$lib/components/ui/command/index.js";
  import { cn } from "$lib/utils";
  import { tick } from "svelte";
  import { Calendar } from "$lib/components/ui/calendar/index.js";
  import { CaretSort } from "svelte-radix";

  interface Expense {
    collectionId: string;
    id: string;
    customer: string;
    date: string;
    type: string;
    amount: number;
    created: string;
    picture: string;
    company_credit_card: boolean;
    user: string;
    description: string;
    datetime: string;
    expense_type: string;
    customer_id: string;
  }

  type SortableField =
    | "date"
    | "amount"
    | "customer"
    | "type"
    | "description"
    | "company_credit_card"
    | "user";

  let tempExpenses: Expense[] = [];
  let searchQuery = "";
  let sortField: SortableField = "date";
  let sortDirection: "asc" | "desc" = "desc";

  // Get current date for filters and CSV export
  const currentDate = new Date();
  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  let selectedFilterMonth: string = currentMonth.toString();
  let selectedFilterYear: number = currentYear;
  let selectedMonth: string = (currentMonth + 1).toString().padStart(2, "0");
  let selectedYear: string = currentYear.toString();

  const drawerOpen = writable(false);
  let selectedRow: Expense | null = null;
  let editingExpense: Expense | null = null;
  let editDialogOpen = false;
  let deleteDialogOpen = false;
  let expenseToDelete: Expense | null = null;
  let newPicture: File | null = null;
  let editDateOpen = false;
  let editDateValue: DateValue | undefined = undefined;

  // For edit form
  let parsedCustomers: Array<{ value: string; label: string; frequency: number }> = [];
  let parsedExpenseTypes: Array<{ value: string; label: string; frequency: number }> = [];
  let editCustomerOpen = false;
  let editExpenseTypeOpen = false;

  let customerOpen = false;
  let customerValue = "";
  let expenseTypeOpen = false;
  let expenseTypeValue = "";

  // For frequency tracking
  $: {
    // Count frequency of customers in expenses
    const customerFrequency = $expenses.reduce(
      (acc, expense) => {
        const customerId = expense.customer;
        acc[customerId] = (acc[customerId] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    // Count frequency of expense types per customer
    const customerTypeFrequency = $expenses.reduce(
      (acc, expense) => {
        const customerId = expense.customer;
        const typeId = expense.expense_type;
        if (!acc[customerId]) {
          acc[customerId] = {};
        }
        acc[customerId][typeId] = (acc[customerId][typeId] || 0) + 1;
        return acc;
      },
      {} as Record<string, Record<string, number>>
    );

    // Count frequency of customers per type
    const typeCustomerFrequency = $expenses.reduce(
      (acc, expense) => {
        const typeId = expense.expense_type;
        const customerId = expense.customer;
        if (!acc[typeId]) {
          acc[typeId] = {};
        }
        acc[typeId][customerId] = (acc[typeId][customerId] || 0) + 1;
        return acc;
      },
      {} as Record<string, Record<string, number>>
    );

    // Map and sort customers based on context
    parsedCustomers = $customers
      .map((customer) => ({
        value: customer.id,
        label: customer.name,
        frequency: customerFrequency[customer.id] || 0,
        // If a type is selected, use the frequency of this customer with that type
        contextFrequency: expenseTypeValue
          ? typeCustomerFrequency[expenseTypeValue]?.[customer.id] || 0
          : 0
      }))
      .sort((a, b) => {
        // If we have a type selected, sort by context frequency first
        if (expenseTypeValue) {
          const contextDiff = b.contextFrequency - a.contextFrequency;
          if (contextDiff !== 0) return contextDiff;
        }
        // Fall back to overall frequency
        return b.frequency - a.frequency;
      });

    // Map and sort expense types based on context
    parsedExpenseTypes = $expenseTypes
      .map((expenseType) => ({
        value: expenseType.id,
        label: expenseType.name,
        frequency: customerFrequency[expenseType.id] || 0,
        // If a customer is selected, use the frequency of this type with that customer
        contextFrequency: customerValue
          ? customerTypeFrequency[customerValue]?.[expenseType.id] || 0
          : 0
      }))
      .sort((a, b) => {
        // If we have a customer selected, sort by context frequency first
        if (customerValue) {
          const contextDiff = b.contextFrequency - a.contextFrequency;
          if (contextDiff !== 0) return contextDiff;
        }
        // Fall back to overall frequency
        return b.frequency - a.frequency;
      });
  }

  function closeCustomerCombobox(triggerId: string) {
    customerOpen = false;
    tick().then(() => {
      document.getElementById(triggerId)?.focus();
    });
  }

  function closeExpenseTypeCombobox(triggerId: string) {
    expenseTypeOpen = false;
    tick().then(() => {
      document.getElementById(triggerId)?.focus();
    });
  }

  const sortFields: SortableField[] = [
    "customer",
    "date",
    "type",
    "description",
    "amount",
    "company_credit_card"
  ];
  if (client.authStore.model?.admin) {
    sortFields.push("user");
  }

  function handleSort(field: SortableField) {
    if (sortField === field) {
      // If clicking the same field, toggle direction
      sortDirection = sortDirection === "asc" ? "desc" : "asc";
    } else {
      // If clicking a new field, set it as sort field and default to desc
      sortField = field;
      sortDirection = "desc";
    }
  }

  $: tempExpenses = $expenses.map((expense) => ({
    collectionId: expense.collectionId,
    id: expense.id,
    // @ts-expect-error - expense type is not null
    customer: expense.expand.customer.name,
    customer_id: expense.customer,
    date: new Date(expense.datetime).toLocaleDateString("de-CH", {
      year: "numeric",
      month: "short",
      day: "numeric"
    }),
    // @ts-expect-error - expense type is not null
    type: expense.expand.expense_type.name,
    expense_type: expense.expense_type,
    description: expense.description,
    amount: expense.amount,
    created: new Date(expense.created).toLocaleDateString("de-CH", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "numeric"
    }),
    datetime: expense.datetime,
    picture: expense.picture ? getFileUrl(expense.collectionId, expense.id, expense.picture) : "",
    company_credit_card: expense.company_credit_card,
    // @ts-expect-error - expense type is not null
    user: expense.expand.user.name
  }));

  $: filteredByMonthExpenses = tempExpenses.filter((expense) => {
    if (selectedFilterMonth === "all") return true;
    const expenseDate = new Date(expense.datetime);
    return expenseDate.getMonth() === parseInt(selectedFilterMonth);
  });

  $: sortedAndFilteredExpenses = filteredByMonthExpenses
    .filter((expense) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        expense.customer.toLowerCase().includes(query) ||
        expense.type.toLowerCase().includes(query) ||
        expense.description?.toLowerCase().includes(query) ||
        expense.amount.toString().includes(query) ||
        expense.date.toLowerCase().includes(query) ||
        (expense.company_credit_card ? "company card" : "").includes(query) ||
        expense.user?.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      if (!sortField) return 0;

      const direction = sortDirection === "asc" ? 1 : -1;

      switch (sortField) {
        case "amount":
          return (a.amount - b.amount) * direction;
        case "company_credit_card":
          return (Number(a.company_credit_card) - Number(b.company_credit_card)) * direction;
        case "date":
          return (new Date(a.datetime).getTime() - new Date(b.datetime).getTime()) * direction;
        case "customer":
          return a.customer.localeCompare(b.customer) * direction;
        case "type":
          return a.type.localeCompare(b.type) * direction;
        case "description":
          return (a.description || "").localeCompare(b.description || "") * direction;
        case "user":
          return (a.user || "").localeCompare(b.user || "") * direction;
        default:
          return 0;
      }
    });

  function handleDeleteClick(expense: Expense) {
    expenseToDelete = expense;
    deleteDialogOpen = true;
  }

  async function confirmDelete() {
    if (!expenseToDelete) return;

    try {
      await client.collection("expenses").delete(expenseToDelete.id);
      await updateDataStores({
        filter: UpdateFilterEnum.ALL
      });
      toast.success("Expense deleted successfully!");
      deleteDialogOpen = false;
      expenseToDelete = null;
    } catch (error) {
      console.error(error);
      toast.error("Failed to delete expense!");
    }
  }

  function handleEditClick(expense: Expense) {
    editingExpense = { ...expense };
    editDateValue = parseDate(new Date(expense.datetime).toISOString().split("T")[0]);
    editDialogOpen = true;
  }

  function handleFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input?.files?.length) {
      newPicture = input.files[0];
    }
  }

  async function handleEditSubmit() {
    if (!editingExpense || !editDateValue) return;

    const formData = new FormData();
    formData.append("datetime", editDateValue.toDate(getLocalTimeZone()).toISOString());
    formData.append("customer", editingExpense.customer_id);
    formData.append("expense_type", editingExpense.expense_type);
    formData.append("description", editingExpense.description);
    formData.append("amount", editingExpense.amount.toString());
    formData.append("company_credit_card", editingExpense.company_credit_card.toString());

    if (newPicture) {
      formData.append("picture", newPicture);
    }

    try {
      await client.collection("expenses").update(editingExpense.id, formData);
      await updateDataStores({
        filter: UpdateFilterEnum.ALL
      });
      toast.success("Expense updated successfully!");
      editDialogOpen = false;
      editingExpense = null;
      editDateValue = undefined;
      newPicture = null;
    } catch (error) {
      console.error(error);
      toast.error("Failed to update expense!");
    }
  }

  function downloadCSV(): void {
    const germanToEnglishMonths: { [key: string]: string } = {
      "Jan.": "Jan",
      "Feb.": "Feb",
      März: "Mar",
      "Apr.": "Apr",
      Mai: "May",
      Juni: "Jun",
      Juli: "Jul",
      "Aug.": "Aug",
      "Sept.": "Sep",
      "Okt.": "Oct",
      "Nov.": "Nov",
      "Dez.": "Dec"
    };

    const normalizedDates = tempExpenses.map((expense: { date: string }) => {
      let dateStr = expense.date;
      Object.keys(germanToEnglishMonths).forEach((germanMonth) => {
        dateStr = dateStr.replace(germanMonth, germanToEnglishMonths[germanMonth]);
      });
      return new Date(dateStr);
    });

    const filteredExpenses = tempExpenses.filter((expense: { date: string }, index: number) => {
      const date = normalizedDates[index];
      return (
        date.getMonth() + 1 === parseInt(selectedMonth) &&
        date.getFullYear() === parseInt(selectedYear)
      );
    });

    const csv = Papa.unparse(filteredExpenses);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    saveAs(blob, `expenses_${selectedYear}-${selectedMonth}.csv`);
  }

  function handleSubmit() {
    downloadCSV();
    drawerOpen.set(false);
  }
</script>

<div class="container mx-auto py-6 px-4">
  <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
    <div class="flex gap-2 w-full sm:w-auto">
      <div class="relative w-full sm:w-auto sm:min-w-[300px]">
        <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input type="text" placeholder="Search expenses..." class="pl-8" bind:value={searchQuery} />
      </div>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild let:builder>
          <Button variant="outline" builders={[builder]} class="w-[180px]">
            {#if selectedFilterMonth === "all"}
              All Expenses
            {:else}
              {new Date(selectedFilterYear, parseInt(selectedFilterMonth), 1).toLocaleDateString(
                "de-CH",
                { month: "long", year: "numeric" }
              )}
            {/if}
            <ChevronDown class="ml-2 h-4 w-4" />
          </Button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end">
          <DropdownMenu.Label>Filter by Month</DropdownMenu.Label>
          <DropdownMenu.Separator />
          <DropdownMenu.RadioGroup bind:value={selectedFilterMonth}>
            <DropdownMenu.RadioItem value="all">All Expenses</DropdownMenu.RadioItem>
            <DropdownMenu.RadioItem value={currentMonth.toString()}>
              {new Date(currentYear, currentMonth).toLocaleDateString("de-CH", { month: "long" })}
            </DropdownMenu.RadioItem>
            <DropdownMenu.RadioItem
              value={(currentMonth - 1 >= 0 ? currentMonth - 1 : 11).toString()}
            >
              {new Date(
                currentYear,
                currentMonth - 1 >= 0 ? currentMonth - 1 : 11
              ).toLocaleDateString("de-CH", { month: "long" })}
            </DropdownMenu.RadioItem>
          </DropdownMenu.RadioGroup>
        </DropdownMenu.Content>
      </DropdownMenu.Root>
    </div>
    {#if client.authStore.model && client.authStore.model.admin}
      <Button variant="outline" on:click={() => drawerOpen.set(true)}>Download CSV</Button>
    {/if}
  </div>

  <!-- Desktop Table View -->
  <div class="hidden md:block rounded-md border overflow-x-auto">
    <Table.Root>
      <Table.Header>
        <Table.Row>
          {#each sortFields as field}
            <Table.Head class="min-w-[150px] cursor-pointer select-none hover:bg-muted/50">
              <button
                class="flex items-center gap-1 w-full text-left"
                on:click|stopPropagation={() => handleSort(field)}
              >
                <span class="capitalize">{field.replace(/_/g, " ")}</span>
                {#if sortField === field}
                  <span class="text-primary">
                    {#if sortDirection === "asc"}
                      <ChevronUp class="h-4 w-4" />
                    {:else}
                      <ChevronDown class="h-4 w-4" />
                    {/if}
                  </span>
                {:else}
                  <ArrowUpDown class="h-4 w-4 opacity-0 group-hover:opacity-100" />
                {/if}
              </button>
            </Table.Head>
          {/each}
          <Table.Head class="w-[150px]">Actions</Table.Head>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {#each sortedAndFilteredExpenses as expense}
          <Table.Row>
            <Table.Cell>{expense.customer}</Table.Cell>
            <Table.Cell>{expense.date}</Table.Cell>
            <Table.Cell>{expense.type}</Table.Cell>
            <Table.Cell>{expense.description}</Table.Cell>
            <Table.Cell class="text-right font-medium">{expense.amount.toFixed(2)} CHF</Table.Cell>
            <Table.Cell>
              {#if expense.company_credit_card}
                <span
                  class="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100 text-xs px-2 py-0.5 rounded"
                  >Company Card</span
                >
              {:else}
                <span
                  class="bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-100 text-xs px-2 py-0.5 rounded"
                  >Self Paid</span
                >
              {/if}
            </Table.Cell>
            {#if client.authStore.model?.admin}
              <Table.Cell>{expense.user}</Table.Cell>
            {/if}
            <Table.Cell>
              <div class="flex justify-end gap-2">
                {#if expense.picture}
                  <Lightbox>
                    <div slot="thumbnail">
                      <Button variant="ghost" size="icon">
                        <Camera class="h-4 w-4" />
                      </Button>
                    </div>
                    <div>
                      <img src={expense.picture} alt="Expense receipt" class="max-h-[80vh]" />
                    </div>
                  </Lightbox>
                {/if}
                <Button variant="ghost" size="icon" on:click={() => handleEditClick(expense)}>
                  <Edit2 class="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" on:click={() => handleDeleteClick(expense)}>
                  <Trash2 class="h-4 w-4" />
                </Button>
              </div>
            </Table.Cell>
          </Table.Row>
        {/each}
      </Table.Body>
    </Table.Root>
  </div>

  <!-- Mobile Card View -->
  <div class="block md:hidden space-y-4">
    {#each sortedAndFilteredExpenses as expense}
      <Card class="p-4">
        <div class="space-y-2 mb-2">
          <div class="flex items-center justify-between">
            <span class="font-medium">{expense.customer}</span>
            <div class="text-right font-medium">
              {expense.amount.toFixed(2)} CHF
            </div>
          </div>
          <div>
            {#if expense.company_credit_card}
              <span
                class="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100 text-xs px-2 py-0.5 rounded"
                >Company Card</span
              >
            {:else}
              <span
                class="bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-100 text-xs px-2 py-0.5 rounded"
                >Self Paid</span
              >
            {/if}
          </div>
        </div>

        {#if expense.picture}
          <div class="mb-3 w-full">
            <Lightbox>
              <div slot="thumbnail">
                <img
                  src={expense.picture}
                  alt="Expense receipt"
                  class="w-full h-20 object-cover rounded-lg"
                />
              </div>
              <div>
                <img src={expense.picture} alt="Expense receipt" class="max-h-[80vh]" />
              </div>
            </Lightbox>
          </div>
        {/if}

        <div class="grid grid-cols-2 gap-2 text-sm mb-3">
          <div class="flex items-center gap-1 text-muted-foreground">
            <CalendarIcon class="h-4 w-4" />
            {expense.date}
          </div>
          <div class="text-right text-muted-foreground">
            {expense.type}
          </div>
        </div>

        {#if expense.description}
          <p class="text-sm text-muted-foreground mb-3">
            {expense.description}
          </p>
        {/if}

        <div class="flex justify-end gap-2">
          <Button variant="ghost" size="icon" on:click={() => handleEditClick(expense)}>
            <Edit2 class="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" on:click={() => handleDeleteClick(expense)}>
            <Trash2 class="h-4 w-4" />
          </Button>
        </div>
      </Card>
    {/each}
  </div>
</div>

<!-- Dialogs and Drawers -->
<Dialog.Root bind:open={editDialogOpen}>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>Edit Expense</Dialog.Title>
      <Dialog.Description>Make changes to the expense entry</Dialog.Description>
    </Dialog.Header>

    {#if editingExpense}
      <form class="grid gap-4" on:submit|preventDefault={handleEditSubmit}>
        <Popover.Root bind:open={editDateOpen} let:ids>
          <Popover.Trigger asChild let:builder>
            <Button
              variant="outline"
              class={cn("w-full justify-start text-left font-normal")}
              builders={[builder]}
            >
              <CalendarIcon class="mr-2 h-4 w-4" />
              {editDateValue
                ? editDateValue
                    .toDate(getLocalTimeZone())
                    .toLocaleDateString("de-CH", { dateStyle: "long" })
                : "Select date"}
            </Button>
          </Popover.Trigger>
          <Popover.Content class="w-auto p-0" align="center">
            <Calendar bind:value={editDateValue} />
          </Popover.Content>
        </Popover.Root>

        <Popover.Root bind:open={editCustomerOpen} let:ids>
          <Popover.Trigger asChild let:builder>
            <Button
              builders={[builder]}
              variant="outline"
              role="combobox"
              aria-expanded={editCustomerOpen}
              class="w-full justify-between"
            >
              {editingExpense.customer || "Select customer"}
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
                      if (editingExpense) {
                        editingExpense.customer_id = customer.value;
                        editingExpense.customer = customer.label;
                        closeCustomerCombobox(ids.trigger);
                      }
                    }}
                  >
                    <Check
                      class={cn(
                        "mr-2 h-4 w-4",
                        editingExpense.customer_id !== customer.value && "text-transparent"
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

        <Popover.Root bind:open={editExpenseTypeOpen} let:ids>
          <Popover.Trigger asChild let:builder>
            <Button
              builders={[builder]}
              variant="outline"
              role="combobox"
              aria-expanded={editExpenseTypeOpen}
              class="w-full justify-between"
            >
              {editingExpense.type || "Select type"}
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
                      if (editingExpense) {
                        editingExpense.expense_type = expenseType.value;
                        editingExpense.type = expenseType.label;
                        closeExpenseTypeCombobox(ids.trigger);
                      }
                    }}
                  >
                    <Check
                      class={cn(
                        "mr-2 h-4 w-4",
                        editingExpense.expense_type !== expenseType.value && "text-transparent"
                      )}
                    />
                    <span class="flex-1">{expenseType.label}</span>
                    {#if expenseType.frequency > 0}
                      <span class="text-xs text-muted-foreground ml-2"
                        >{expenseType.frequency}x</span
                      >
                    {/if}
                  </Command.Item>
                {/each}
              </Command.Group>
            </Command.Root>
          </Popover.Content>
        </Popover.Root>

        <div class="grid gap-2">
          <Label for="edit-description">Description</Label>
          <Input id="edit-description" bind:value={editingExpense.description} />
        </div>
        <div class="grid gap-2">
          <Label for="edit-amount">Amount (CHF)</Label>
          <Input id="edit-amount" type="number" step="0.01" bind:value={editingExpense.amount} />
        </div>
        <div class="grid gap-2">
          <Label for="edit-picture">Receipt Picture</Label>
          {#if editingExpense.picture && !newPicture}
            <div class="mb-2">
              <img src={editingExpense.picture} alt="Current receipt" class="max-h-32 rounded-lg" />
            </div>
          {/if}
          {#if newPicture}
            <div class="mb-2">
              <img
                src={URL.createObjectURL(newPicture)}
                alt="New receipt"
                class="max-h-32 rounded-lg"
              />
            </div>
          {/if}
          <div class="file-input-wrapper">
            <input
              id="edit-picture"
              type="file"
              class="file-input"
              accept="image/*"
              on:change={(event) => {
                if (event.target) {
                  // @ts-expect-error - event.target.files is a FileList
                  newPicture = event.target.files[0];
                }
              }}
            />
            <label
              for="edit-picture"
              class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 w-full"
            >
              <Camera class="h-4 w-4 mr-2" />
              Upload New Picture
            </label>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <Checkbox id="edit-company-card" bind:checked={editingExpense.company_credit_card} />
          <Label for="edit-company-card">Company credit card used</Label>
        </div>
        <div class="flex justify-end gap-2">
          <Dialog.Close asChild let:builder>
            <Button variant="outline" builders={[builder]}>Cancel</Button>
          </Dialog.Close>
          <Button type="submit">Save changes</Button>
        </div>
      </form>
    {/if}
  </Dialog.Content>
</Dialog.Root>

<AlertDialog.Root bind:open={deleteDialogOpen}>
  <AlertDialog.Content>
    <AlertDialog.Header>
      <AlertDialog.Title>Are you sure?</AlertDialog.Title>
      <AlertDialog.Description>
        This action cannot be undone. This will permanently delete the expense
        {#if expenseToDelete}
          for {expenseToDelete.amount.toFixed(2)} CHF from {expenseToDelete.customer}.
        {/if}
      </AlertDialog.Description>
    </AlertDialog.Header>
    <AlertDialog.Footer>
      <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
      <AlertDialog.Action on:click={confirmDelete}>Delete</AlertDialog.Action>
    </AlertDialog.Footer>
  </AlertDialog.Content>
</AlertDialog.Root>

{#if client.authStore.model && client.authStore.model.admin}
  <Drawer.Root open={$drawerOpen}>
    <Drawer.Content>
      <div class="mx-auto w-full max-w-sm">
        <Drawer.Header>
          <Drawer.Title>Select Month and Year</Drawer.Title>
          <Drawer.Description>Select the month and year for the CSV export.</Drawer.Description>
        </Drawer.Header>
        <div class="p-4 pb-0">
          <div class="grid gap-4">
            <div class="grid gap-2">
              <Label for="month">Month</Label>
              <Input
                id="month"
                type="number"
                bind:value={selectedMonth}
                min="1"
                max="12"
                placeholder="MM"
              />
            </div>
            <div class="grid gap-2">
              <Label for="year">Year</Label>
              <Input
                id="year"
                type="number"
                bind:value={selectedYear}
                min="2000"
                max="2100"
                placeholder="YYYY"
              />
            </div>
          </div>
        </div>
        <Drawer.Footer>
          <Button on:click={handleSubmit}>Download</Button>
          <Drawer.Close asChild let:builder>
            <Button builders={[builder]} variant="outline">Cancel</Button>
          </Drawer.Close>
        </Drawer.Footer>
      </div>
    </Drawer.Content>
  </Drawer.Root>
{/if}

<style>
  .file-input-wrapper {
    position: relative;
    display: inline-block;
    width: 100%;
  }
  .file-input {
    display: none; /* Hide the actual file input */
  }
  .file-input-button {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
    background-color: var(--background);
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: pointer;
    width: 100%;
    color: var(--foreground);
  }
  .file-input-button:hover {
    background-color: var(--muted);
  }
</style>
