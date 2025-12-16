import fs from "node:fs";
import path from "node:path";
import xlsx from "xlsx";

const OUTPUT = path.resolve("src/data/tse_companies.json");
const CACHE_DIR = path.resolve("scripts/cache");
const CACHE_XLS = path.join(CACHE_DIR, "data_j.xls");

const JPX_LIST_URL =
  "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls";

function normalizeMarket(value) {
  return String(value ?? "").trim();
}

function normalizeSecCode4(code) {
  const s = String(code ?? "").trim();
  if (!s) return "";
  if (/^\d{4}$/.test(s)) return s;
  if (/^\d+$/.test(s)) return s.padStart(4, "0").slice(-4);
  if (/^\d{3}[A-Z]$/.test(s)) return s;
  if (/^\d{4}[A-Z]$/.test(s)) return s;
  return "";
}

function isTseMarket(market) {
  const m = normalizeMarket(market);
  // “東証上場企業”に寄せる（ETF/REIT等を除外し、株式上場を対象にする）
  if (m.includes("PRO Market")) return true;
  if (m.includes("内国株式") || m.includes("外国株式")) return true;
  return false;
}

async function downloadToCache() {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
  const res = await fetch(JPX_LIST_URL);
  if (!res.ok) throw new Error(`JPX download failed: HTTP ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  fs.writeFileSync(CACHE_XLS, buf);
}

function readWorkbookRows(filePath) {
  const wb = xlsx.readFile(filePath, { cellDates: false });
  const sheetName = wb.SheetNames[0];
  const sheet = wb.Sheets[sheetName];
  return xlsx.utils.sheet_to_json(sheet, { defval: "" });
}

function pick(obj, candidates) {
  for (const key of candidates) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) return obj[key];
  }
  return "";
}

function buildCompanies(rows) {
  const out = [];
  for (const row of rows) {
    const code = normalizeSecCode4(pick(row, ["コード", "code", "Code"]));
    const name = String(pick(row, ["銘柄名", "会社名", "name", "Name"])).trim();
    const market = normalizeMarket(
      pick(row, ["市場・商品区分", "市場区分", "market", "Market"]),
    );
    if (!code || !name) continue;
    if (!isTseMarket(market)) continue;
    out.push({
      secCode4: code,
      secCode5: `${code}0`,
      name,
      market: market || "東証",
    });
  }

  const unique = new Map();
  for (const c of out) unique.set(c.secCode4, c);
  return Array.from(unique.values()).sort((a, b) =>
    a.secCode4.localeCompare(b.secCode4),
  );
}

async function main() {
  if (!fs.existsSync(CACHE_XLS)) {
    console.log("Downloading JPX listed companies…");
    await downloadToCache();
  }
  const rows = readWorkbookRows(CACHE_XLS);
  const companies = buildCompanies(rows);
  fs.writeFileSync(OUTPUT, JSON.stringify(companies, null, 2), "utf8");
  console.log(`Wrote ${companies.length} companies to ${OUTPUT}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
