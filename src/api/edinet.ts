import type { EdinetDocument } from "../types";

const EDINET_BASE = import.meta.env.DEV
  ? "/edinet/api/v2"
  : "https://disclosure.edinet-fsa.go.jp/api/v2";
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
  const url = import.meta.env.DEV
    ? `${EDINET_BASE}/documents/${docID}?type=${type}`
    : `${EDINET_BASE}/documents/${docID}?type=${type}&subscription-key=${encodeURIComponent(apiKey)}`;
  const headers = import.meta.env.DEV
    ? { [SUBSCRIPTION_KEY_HEADER]: apiKey }
    : undefined;
  const response = await fetch(url, { headers, signal });
  if (!response.ok) {
    throw new Error(`EDINET: HTTP ${response.status}`);
  }
  return response.blob();
}

export function documentDownloadUrl(docID: string, type: 1 | 2, apiKey: string): string {
  return import.meta.env.DEV
    ? `${EDINET_BASE}/documents/${docID}?type=${type}`
    : `${EDINET_BASE}/documents/${docID}?type=${type}&subscription-key=${encodeURIComponent(apiKey)}`;
}
