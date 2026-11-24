import { getBaseURL } from "#lib/utils/base.ts";
import { avatarUrl } from "#lib/utils/user.utils.ts";
import { writable } from "svelte/store";

export const avatarUrlString = writable<string>(getBaseURL() + avatarUrl());
