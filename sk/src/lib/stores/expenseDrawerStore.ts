// src/stores/expenseDrawerStore.ts
import { writable } from "svelte/store";

export const drawerOpen = writable(false);
export const selectedExpense = writable(null);

export function openDrawer(expense = null) {
  selectedExpense.set(expense);
  drawerOpen.set(true);
}

export function closeDrawer() {
  drawerOpen.set(false);
}
