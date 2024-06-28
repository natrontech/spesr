/**
 * This file was @generated using pocketbase-typegen
 */

import type PocketBase from "pocketbase";
import type { RecordService } from "pocketbase";

export enum Collections {
  Customers = "customers",
  ExpenseTypes = "expense_types",
  Expenses = "expenses",
  Users = "users"
}

// Alias types for improved usability
export type IsoDateString = string;
export type RecordIdString = string;
export type HTMLString = string;

// System fields
export type BaseSystemFields<T = never> = {
  id: RecordIdString;
  created: IsoDateString;
  updated: IsoDateString;
  collectionId: string;
  collectionName: Collections;
  expand?: T;
};

export type AuthSystemFields<T = never> = {
  email: string;
  emailVisibility: boolean;
  username: string;
  verified: boolean;
} & BaseSystemFields<T>;

// Record types for each collection

export type CustomersRecord = {
  name?: string;
};

export type ExpenseTypesRecord = {
  name?: string;
};

export type ExpensesRecord = {
  amount: number;
  company_credit_card?: boolean;
  customer: RecordIdString;
  datetime: IsoDateString;
  description?: string;
  expense_type: RecordIdString;
  picture?: string;
  user: RecordIdString;
};

export type UsersRecord = {
  avatar?: string;
  name?: string;
};

// Response types include system fields and match responses from the PocketBase API
export type CustomersResponse<Texpand = unknown> = Required<CustomersRecord> &
  BaseSystemFields<Texpand>;
export type ExpenseTypesResponse<Texpand = unknown> = Required<ExpenseTypesRecord> &
  BaseSystemFields<Texpand>;
export type ExpensesResponse<Texpand = unknown> = Required<ExpensesRecord> &
  BaseSystemFields<Texpand>;
export type UsersResponse<Texpand = unknown> = Required<UsersRecord> & AuthSystemFields<Texpand>;

// Types containing all Records and Responses, useful for creating typing helper functions

export type CollectionRecords = {
  customers: CustomersRecord;
  expense_types: ExpenseTypesRecord;
  expenses: ExpensesRecord;
  users: UsersRecord;
};

export type CollectionResponses = {
  customers: CustomersResponse;
  expense_types: ExpenseTypesResponse;
  expenses: ExpensesResponse;
  users: UsersResponse;
};

// Type for usage with type asserted PocketBase instance
// https://github.com/pocketbase/js-sdk#specify-typescript-definitions

export type TypedPocketBase = PocketBase & {
  collection(idOrName: "customers"): RecordService<CustomersResponse>;
  collection(idOrName: "expense_types"): RecordService<ExpenseTypesResponse>;
  collection(idOrName: "expenses"): RecordService<ExpensesResponse>;
  collection(idOrName: "users"): RecordService<UsersResponse>;
};
