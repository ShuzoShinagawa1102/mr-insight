import type { EdinetDocument } from "../types";

export function isYuhou(doc: EdinetDocument, includeCorrections: boolean): boolean {
  const description = doc.docDescription ?? "";
  const byDescription =
    description.includes("有価証券報告書") ||
    (includeCorrections && description.includes("訂正有価証券報告書"));

  const formCode = doc.formCode ?? "";
  const byFormCode =
    formCode === "030000" || (includeCorrections && formCode === "030001");

  return byDescription || byFormCode;
}

