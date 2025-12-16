export function normalizeToken(input: string): string {
  return input
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\u3000\s]+/g, "") // spaces (incl. full-width)
    .replace(/[・･]/g, "")
    .replace(/[()（）［］【】\[\]{}]/g, "")
    .replace(/[‐‑–—−ー\-]/g, "");
}

export function tokenizeQuery(input: string): string[] {
  const raw = input
    .normalize("NFKC")
    .toLowerCase()
    .split(/[\u3000\s]+/g)
    .map((t) => t.trim())
    .filter(Boolean);
  const tokens = raw.map(normalizeToken).filter(Boolean);
  return Array.from(new Set(tokens));
}

export function buildSearchKey(parts: string[]): string {
  return normalizeToken(parts.filter(Boolean).join(" "));
}

