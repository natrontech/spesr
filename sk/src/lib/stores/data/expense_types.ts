import type { ExpenseTypesResponse } from "$lib/pocketbase/generated-types";
import { writable } from "svelte/store";

// Generic type for expandable responses
type ExpandableResponse<T, U> = T & { expand?: U };

// Generic writable store
function createWritableStore<T>(initialValue: T) {
  return writable<T>(initialValue);
}

export type Texpand = {};

export const expenseTypes = createWritableStore<
  ExpandableResponse<ExpenseTypesResponse[], Texpand>
>([]);
