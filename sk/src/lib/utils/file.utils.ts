import { getBaseURL } from "./base";

export function getFileUrl(collectionId: string, recordId: string, filename: string): string {
  return getBaseURL() + "/api/files/" + collectionId + "/" + recordId + "/" + filename;
}
