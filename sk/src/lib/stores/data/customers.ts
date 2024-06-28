import type { CustomersResponse } from "$lib/pocketbase/generated-types";
import { writable } from "svelte/store";

// Generic type for expandable responses
type ExpandableResponse<T, U> = T & { expand?: U };

// Generic writable store
function createWritableStore<T>(initialValue: T) {
  return writable<T>(initialValue);
}

export type Cexpand = {};

export const customers = createWritableStore<ExpandableResponse<CustomersResponse[], Cexpand>>([]);
