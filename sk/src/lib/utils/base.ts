export function getBaseURL(): string | undefined {
  let baseUrl = undefined;

  if (typeof window !== "undefined") {
    baseUrl = import.meta.env.DEV ? "http://localhost:8090" : window.location.origin;
  }

  return baseUrl;
}
