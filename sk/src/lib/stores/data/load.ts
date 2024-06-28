import { client } from "$lib/pocketbase";
import type { Writable } from "svelte/store";
import { customers } from "./customers";
import { expenseTypes } from "./expense_types";
import { expenses } from "./expenses";

export enum UpdateFilterEnum {
  ALL = "ALL"
}

export interface UpdateFilter {
  filter: UpdateFilterEnum;
  expenseId?: string;
}

export async function updateDataStore<T, U>(
  collectionName: string,
  store: Writable<T[]>,
  filterFunc?: (item: T) => boolean,
  filter?: UpdateFilter,
  expand?: string
) {
  try {
    const queryOptions = {
      sort: "-created",
      expand: expand
    };

    const response = await client.collection(collectionName).getFullList<U>(queryOptions);

    if (filterFunc) {
      // @ts-expect-error filterFunc is defined
      store.set(response.filter(filterFunc) as T[]);
    } else {
      store.set(response as unknown as T[]);
    }
  } catch (error) {
    // Handle error
  }
}

export async function updateDataStores(filter: UpdateFilter = { filter: UpdateFilterEnum.ALL }) {
  if (filter.filter === UpdateFilterEnum.ALL) {
    await updateDataStore(
      "customers",
      customers,
      (customer) => !filter.expenseId || customer.id === filter.expenseId,
      filter
    );
    await updateDataStore(
      "expense_types",
      expenseTypes,
      (expenseType) => !filter.expenseId || expenseType.id === filter.expenseId,
      filter
    );
    await updateDataStore(
      "expenses",
      expenses,
      (expense) => !filter.expenseId || expense.id === filter.expenseId,
      filter,
      "user,expense_type,customer"
    );
  }
}
