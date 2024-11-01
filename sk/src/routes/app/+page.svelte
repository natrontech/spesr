<script lang="ts">
  import Button from "$lib/components/ui/button/button.svelte";
  import { expenses } from "$lib/stores/data/expenses";
  import { DataHandler, Datatable, Th, ThFilter } from "@vincjo/datatables";
  import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
  import { client } from "$lib/pocketbase";
  import { updateDataStores, UpdateFilterEnum } from "$lib/stores/data/load";
  import { toast } from "svelte-sonner";
  import { Lightbox } from "svelte-lightbox";
  import { getFileUrl } from "$lib/utils/file.utils";
  // @ts-expect-error - expenses type is not null
  import { saveAs } from "file-saver";
  // @ts-expect-error - expenses type is not null
  import Papa from "papaparse";
  import * as Drawer from "$lib/components/ui/drawer/index.js";
  import { writable } from "svelte/store";

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
  }

  let tempExpenses: Expense[] = [];

  $: tempExpenses = $expenses.map((expense) => ({
    collectionId: expense.collectionId,
    id: expense.id,
    // @ts-expect-error - expense type is not null
    customer: expense.expand.customer.name,
    date: new Date(expense.datetime).toLocaleDateString("de-CH", {
      year: "numeric",
      month: "short",
      day: "numeric"
    }),
    // @ts-expect-error - expense type is not null
    type: expense.expand.expense_type.name,
    description: expense.description,
    amount: expense.amount,
    created: new Date(expense.created).toLocaleDateString("de-CH", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "numeric"
    }),
    picture: expense.picture ? getFileUrl(expense.collectionId, expense.id, expense.picture) : "",
    company_credit_card: expense.company_credit_card,
    // @ts-expect-error - expense type is not null
    user: expense.expand.user.name
  }));

  let handler = new DataHandler(tempExpenses, { rowsPerPage: 5 });
  let rows = handler.getRows();

  $: {
    handler.setRows(tempExpenses);
    rows = handler.getRows();
  }

  let selectedRow: Expense | null = null;

  // Get current date
  const currentDate = new Date();

  // Calculate last month and current year
  let lastMonth = currentDate.getMonth(); // getMonth returns 0-11, so this is the previous month
  let currentYear = currentDate.getFullYear();

  if (lastMonth === 0) {
    lastMonth = 12; // December
    currentYear -= 1; // previous year
  }

  let selectedMonth: string = lastMonth.toString().padStart(2, "0"); // Ensure two digits
  let selectedYear: string = currentYear.toString();

  const drawerOpen = writable(false);

  async function handleDeleteClick(row: Expense) {
    selectedRow = row;

    if (!selectedRow) return;

    await client
      .collection("expenses")
      .delete(selectedRow.id)
      .then(() => {
        updateDataStores({
          filter: UpdateFilterEnum.ALL
        }).catch((error) => {
          console.error(error);
        });
        toast.success("Expense deleted successfully!");
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to delete expense!");
      });
  }

  function downloadCSV(): void {
    console.log(selectedMonth, selectedYear);

    // Print the expenses for the selected month and year
    console.log("Expenses for", selectedYear, selectedMonth);

    // Define a mapping for German month abbreviations to full English equivalents
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

    // Replace German month names with English equivalents before parsing
    const normalizedDates = tempExpenses.map((expense: { date: string }) => {
      let dateStr = expense.date;
      Object.keys(germanToEnglishMonths).forEach((germanMonth) => {
        dateStr = dateStr.replace(germanMonth, germanToEnglishMonths[germanMonth]);
      });
      return new Date(dateStr);
    });

    // Filter expenses for the selected month and year
    const filteredExpenses = tempExpenses.filter((expense: { date: string }, index: number) => {
      const date = normalizedDates[index];
      return (
        date.getMonth() + 1 === parseInt(selectedMonth) &&
        date.getFullYear() === parseInt(selectedYear)
      );
    });

    // Convert the filtered expenses to CSV
    const csv = Papa.unparse(filteredExpenses);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    saveAs(blob, `expenses_${selectedYear}-${selectedMonth}.csv`);
  }

  function handleSubmit() {
    downloadCSV();
    drawerOpen.set(false); // Close the drawer
  }
</script>

<Datatable {handler}>
  <table>
    <thead>
      <tr>
        <Th {handler} orderBy="id">ID</Th>
        <Th {handler} orderBy="customer">Customer</Th>
        <Th {handler} orderBy="date">Date</Th>
        <Th {handler} orderBy="type">Type</Th>
        <Th {handler} orderBy="amount">Amount</Th>
        <Th {handler} orderBy="created">Created</Th>
        <Th {handler} orderBy="picture">Picture</Th>
        <Th {handler} orderBy="company_credit_card">Company Credit Card</Th>
        {#if client.authStore.model && client.authStore.model.admin}
          <Th {handler} orderBy="user">User</Th>
        {/if}
        <th>Delete</th>
      </tr>
      <tr>
        <ThFilter {handler} filterBy="id" />
        <ThFilter {handler} filterBy="customer" />
        <ThFilter {handler} filterBy="date" />
        <ThFilter {handler} filterBy="type" />
        <ThFilter {handler} filterBy="amount" />
        <ThFilter {handler} filterBy="created" />
        <ThFilter {handler} filterBy="picture" />
        <ThFilter {handler} filterBy="company_credit_card" />
        {#if client.authStore.model && client.authStore.model.admin}
          <ThFilter {handler} filterBy="user" />
        {/if}
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each $rows as row}
        <tr>
          <td>{row.id}</td>
          <td>{row.customer}</td>
          <td>{row.date}</td>
          <td>{row.type}</td>
          <td>{row.amount}</td>
          <td>{row.created}</td>
          <td>
            {#if row.picture}
              <Lightbox>
                <img width="50px" src={row.picture} alt="" />
              </Lightbox>
            {:else}
              No picture
            {/if}
          </td>
          <td>{row.company_credit_card ? "Yes" : "No"}</td>
          {#if client.authStore.model && client.authStore.model.admin}
            <td>{row.user}</td>
          {/if}
          <td>
            <AlertDialog.Root>
              <AlertDialog.Trigger asChild let:builder>
                <Button builders={[builder]} variant="destructive" size="sm">Delete</Button>
              </AlertDialog.Trigger>
              <AlertDialog.Content>
                <AlertDialog.Header>
                  <AlertDialog.Title>Are you absolutely sure?</AlertDialog.Title>
                  <AlertDialog.Description>
                    This action cannot be undone. This will permanently delete the expense.
                  </AlertDialog.Description>
                </AlertDialog.Header>
                <AlertDialog.Footer>
                  <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
                  <AlertDialog.Action on:click={() => handleDeleteClick(row)}>
                    Continue
                  </AlertDialog.Action>
                </AlertDialog.Footer>
              </AlertDialog.Content>
            </AlertDialog.Root>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</Datatable>

{#if client.authStore.model && client.authStore.model.admin}
  <Drawer.Root open={$drawerOpen}>
    <div class="fixed top-3 right-1/2 translate-x-1/2">
      <Drawer.Trigger asChild let:builder>
        <Button builders={[builder]} variant="outline" on:click={() => drawerOpen.set(true)}
          >Download CSV</Button
        >
      </Drawer.Trigger>
    </div>
    <Drawer.Content>
      <div class="mx-auto w-full max-w-sm">
        <Drawer.Header>
          <Drawer.Title>Select Month and Year</Drawer.Title>
          <Drawer.Description>Select the month and year for the CSV export.</Drawer.Description>
        </Drawer.Header>
        <div class="p-4 pb-0">
          <div class="mb-4">
            <label>
              Month:
              <input type="number" bind:value={selectedMonth} min="1" max="12" placeholder="MM" />
            </label>
          </div>
          <div class="mb-4">
            <label>
              Year:
              <input
                type="number"
                bind:value={selectedYear}
                min="2000"
                max="2100"
                placeholder="YYYY"
              />
            </label>
          </div>
        </div>
        <Drawer.Footer>
          <Button on:click={handleSubmit}>Submit</Button>
          <Drawer.Close asChild let:builder>
            <Button builders={[builder]} variant="outline" on:click={() => drawerOpen.set(false)}
              >Cancel</Button
            >
          </Drawer.Close>
        </Drawer.Footer>
      </div>
    </Drawer.Content>
  </Drawer.Root>
{/if}

<style>
  /* thead {
    background: #fff;
  } */
  tbody td {
    border: 1px solid #f5f5f5;
    padding: 4px 20px;
  }
  tbody tr {
    transition: all, 0.2s;
  }
</style>
