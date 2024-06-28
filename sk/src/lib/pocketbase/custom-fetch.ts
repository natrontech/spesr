// src/lib/custom-fetch.ts
export const createFetchWithAuth = (authToken: string) => {
  return async (input: RequestInfo, init?: RequestInit): Promise<Response> => {
    const headers = new Headers(init?.headers || {});
    headers.set("Authorization", `Bearer ${authToken}`);

    const updatedInit: RequestInit = {
      ...init,
      headers: headers
    };

    return fetch(input, updatedInit);
  };
};
