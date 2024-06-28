<script lang="ts">
  import Button from "$lib/components/ui/button/button.svelte";
  import { expenses } from "$lib/stores/data/expenses";
  import { DataHandler, Datatable, Th, ThFilter } from "@vincjo/datatables";
  import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
  import { client } from "$lib/pocketbase";
  import { updateDataStores, UpdateFilterEnum } from "$lib/stores/data/load";
  import { toast } from "svelte-sonner";

  interface Expense {
    id: string;
    customer: string;
    date: string;
    type: string;
    amount: number;
  }
  let tempExpenses: Expense[] = [];

  $: tempExpenses = $expenses.map((expense) => ({
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
    amount: expense.amount
  }));

  let handler = new DataHandler(tempExpenses, { rowsPerPage: 10 });
  let rows = handler.getRows();

  $: {
    handler.setRows(tempExpenses);
    rows = handler.getRows();
  }

  let selectedRow: Expense | null = null;

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
        <th>Delete</th>
      </tr>
      <tr>
        <ThFilter {handler} filterBy="id" />
        <ThFilter {handler} filterBy="customer" />
        <ThFilter {handler} filterBy="date" />
        <ThFilter {handler} filterBy="type" />
        <ThFilter {handler} filterBy="amount" />
        <th></th>
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

<style>
  thead {
    background: #fff;
  }
  tbody td {
    border: 1px solid #f5f5f5;
    padding: 4px 20px;
  }
  tbody tr {
    transition: all, 0.2s;
  }
  tbody tr:hover {
    background: #f5f5f5;
  }
</style>
