import type {
  CustomersResponse,
  ExpenseTypesResponse,
  ExpensesResponse,
  UsersResponse
} from "$lib/pocketbase/generated-types";
import { writable } from "svelte/store";

// Generic type for expandable responses
type ExpandableResponse<T, U> = T & { expand?: U };

// Generic writable store
function createWritableStore<T>(initialValue: T) {
  return writable<T>(initialValue);
}

export type Eexpand = {
  user: UsersResponse;
  expense_type: ExpenseTypesResponse;
  customer: CustomersResponse;
};

export const expenses = createWritableStore<ExpandableResponse<ExpensesResponse[], Eexpand>>([]);
