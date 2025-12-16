import type { EdinetDocument } from "../types";

const EDINET_BASE = "/edinet/api/v2";
const SUBSCRIPTION_KEY_HEADER = "Ocp-Apim-Subscription-Key";

type EdinetErrorResponse = { statusCode: number; message: string };

function isEdinetError(value: unknown): value is EdinetErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "statusCode" in value &&
    "message" in value
  );
}

async function edinetGetJson<T>(
  pathAndQuery: string,
  apiKey: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${EDINET_BASE}${pathAndQuery}`, {
    headers: {
      [SUBSCRIPTION_KEY_HEADER]: apiKey,
    },
    signal,
  });
  const json = (await response.json()) as unknown;
  if (isEdinetError(json)) {
    throw new Error(`EDINET: ${json.statusCode} ${json.message}`);
  }
  return json as T;
}

export async function listDocumentsByDate(
  date: string,
  apiKey: string,
  signal?: AbortSignal,
): Promise<{ results?: EdinetDocument[] }> {
  return edinetGetJson(`/documents.json?date=${date}&type=2`, apiKey, signal);
}

export async function downloadDocumentBlob(
  docID: string,
  type: 1 | 2,
  apiKey: string,
  signal?: AbortSignal,
): Promise<Blob> {
  const response = await fetch(`${EDINET_BASE}/documents/${docID}?type=${type}`, {
    headers: {
      [SUBSCRIPTION_KEY_HEADER]: apiKey,
    },
    signal,
  });
  if (!response.ok) {
    throw new Error(`EDINET: HTTP ${response.status}`);
  }
  return response.blob();
}
