import type { Company, EdinetDocument } from "../types";
import { isYuhou } from "../lib/yuhou";

export type IndexedDoc = Pick<
  EdinetDocument,
  "docID" | "submitDateTime" | "docDescription" | "formCode" | "secCode"
>;

export type YuhouIndexFile = {
  version: 1;
  year: number;
  generatedAt: string;
  bySecCode: Record<string, IndexedDoc[]>;
};

const modules = import.meta.glob("./yuhou_index_*.json");
const indexByYear = new Map<number, () => Promise<YuhouIndexFile>>();

for (const [path, loader] of Object.entries(modules)) {
  const match = path.match(/yuhou_index_(\d{4})\.json$/);
  if (!match) continue;
  const year = Number(match[1]);
  indexByYear.set(year, async () => {
    const mod = (await (loader as () => Promise<{ default: YuhouIndexFile }>)()) as {
      default: YuhouIndexFile;
    };
    return mod.default;
  });
}

export function availableYears(): number[] {
  return Array.from(indexByYear.keys()).sort((a, b) => b - a);
}

export function hasIndexYear(year: number): boolean {
  return indexByYear.has(year);
}

export async function getIndexedDocs(options: {
  company: Company;
  year: number;
  includeCorrections: boolean;
}): Promise<IndexedDoc[]> {
  const loader = indexByYear.get(options.year);
  if (!loader) return [];
  const file = await loader();

  const secCodes = [options.company.secCode5, options.company.secCode4].filter(Boolean);
  const docs: IndexedDoc[] = [];
  for (const code of secCodes) {
    const items = file.bySecCode[code];
    if (items && items.length > 0) docs.push(...items);
  }
  const uniq = new Map<string, IndexedDoc>();
  for (const d of docs) uniq.set(d.docID, d);
  return Array.from(uniq.values()).filter((d) => isYuhou(d, options.includeCorrections));
}
