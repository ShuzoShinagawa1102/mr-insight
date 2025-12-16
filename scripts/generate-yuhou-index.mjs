import fs from "node:fs";
import path from "node:path";

const EDINET_BASE = "https://disclosure.edinet-fsa.go.jp/api/v2";
const SUBSCRIPTION_KEY_HEADER = "Ocp-Apim-Subscription-Key";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function readDotEnv(filePath) {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    const out = {};
    for (const line of raw.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eq = trimmed.indexOf("=");
      if (eq < 0) continue;
      const k = trimmed.slice(0, eq).trim();
      const v = trimmed.slice(eq + 1).trim();
      out[k] = v;
    }
    return out;
  } catch {
    return {};
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function toIsoDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function datesBetweenInclusive(fromIso, toIso) {
  const from = new Date(`${fromIso}T00:00:00`);
  const to = new Date(`${toIso}T00:00:00`);
  if (Number.isNaN(from.getTime()) || Number.isNaN(to.getTime())) return [];
  if (from > to) return [];
  const out = [];
  const cursor = new Date(from);
  while (cursor <= to) {
    out.push(toIsoDate(cursor));
    cursor.setDate(cursor.getDate() + 1);
  }
  return out;
}

function isYuhou(doc, includeCorrections) {
  const description = doc.docDescription ?? "";
  const byDescription =
    description.includes("有価証券報告書") ||
    (includeCorrections && description.includes("訂正有価証券報告書"));
  const formCode = doc.formCode ?? "";
  const byFormCode =
    formCode === "030000" || (includeCorrections && formCode === "030001");
  return byDescription || byFormCode;
}

function parseYearList(value) {
  if (!value) return [];
  const parts = String(value)
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const years = new Set();
  for (const p of parts) {
    const m = p.match(/^(\d{4})\s*-\s*(\d{4})$/);
    if (m) {
      const a = Number(m[1]);
      const b = Number(m[2]);
      const from = Math.min(a, b);
      const to = Math.max(a, b);
      for (let y = from; y <= to; y += 1) years.add(y);
      continue;
    }
    if (/^\d{4}$/.test(p)) {
      years.add(Number(p));
    }
  }
  return Array.from(years.values()).sort((a, b) => b - a);
}

function resolveDateForYear(templateOrDate, year, multiYear) {
  if (!templateOrDate) return null;
  const s = String(templateOrDate).trim();
  if (!s) return null;
  if (s.includes("{year}")) return s.replaceAll("{year}", String(year));
  if (/^\d{4}-\d{2}-\d{2}$/.test(s) && multiYear) return `${year}-${s.slice(5)}`;
  return s;
}

function resolveRangeForYear(args, year, multiYear) {
  const fromMd = args.fromMD ? String(args.fromMD).trim() : null;
  const toMd = args.toMD ? String(args.toMD).trim() : null;
  if (
    fromMd &&
    /^\d{2}-\d{2}$/.test(fromMd) &&
    toMd &&
    /^\d{2}-\d{2}$/.test(toMd)
  ) {
    return { from: `${year}-${fromMd}`, to: `${year}-${toMd}` };
  }

  const defaultFrom = `${year}-06-01`;
  const defaultTo = `${year}-07-31`;
  const from = resolveDateForYear(args.from, year, multiYear) ?? defaultFrom;
  const to = resolveDateForYear(args.to, year, multiYear) ?? defaultTo;
  return { from, to };
}

async function edinetListDocumentsByDate(date, apiKey) {
  const url = `${EDINET_BASE}/documents.json?date=${date}&type=2`;
  const res = await fetch(url, {
    headers: { [SUBSCRIPTION_KEY_HEADER]: apiKey },
  });
  const json = await res.json();
  if (json && typeof json === "object" && "statusCode" in json && "message" in json) {
    throw new Error(`EDINET: ${json.statusCode} ${json.message}`);
  }
  return json;
}

async function withRetry(fn, { retries, baseDelayMs, maxDelayMs }) {
  let attempt = 0;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      return await fn();
    } catch (e) {
      if (attempt >= retries) throw e;
      const backoff = Math.min(maxDelayMs, baseDelayMs * 2 ** attempt);
      await sleep(backoff);
      attempt += 1;
    }
  }
}

async function buildIndexForYear(options) {
  const { year, from, to, includeCorrections, minIntervalMs, retries, apiKey, secCodeSet, force } =
    options;

  const outPath = path.resolve(`src/data/yuhou_index_${year}.json`);
  if (!force && fs.existsSync(outPath)) {
    console.log(`Skip ${year} (already exists): ${outPath}`);
    return { year, skipped: true, outPath };
  }

  const dates = datesBetweenInclusive(from, to);
  console.log(
    `Indexing year=${year} range=${from}..${to} days=${dates.length} includeCorrections=${includeCorrections}`,
  );

  const bySecCode = {};
  let lastCall = 0;
  for (let i = 0; i < dates.length; i += 1) {
    const date = dates[i];
    const wait = Math.max(0, minIntervalMs - (Date.now() - lastCall));
    if (wait > 0) await sleep(wait);
    lastCall = Date.now();

    const data = await withRetry(() => edinetListDocumentsByDate(date, apiKey), {
      retries,
      baseDelayMs: 500,
      maxDelayMs: 6000,
    });

    const results = data.results ?? [];
    for (const doc of results) {
      if (!isYuhou(doc, includeCorrections)) continue;
      const secCode = String(doc.secCode ?? "").trim();
      if (!secCode || !secCodeSet.has(secCode)) continue;
      if (!bySecCode[secCode]) bySecCode[secCode] = [];
      bySecCode[secCode].push({
        docID: doc.docID,
        secCode: doc.secCode ?? null,
        submitDateTime: doc.submitDateTime ?? null,
        docDescription: doc.docDescription ?? null,
        formCode: doc.formCode ?? null,
      });
    }

    if ((i + 1) % 10 === 0 || i === dates.length - 1) {
      const codes = Object.keys(bySecCode).length;
      const docs = Object.values(bySecCode).reduce((a, v) => a + v.length, 0);
      console.log(`  ${i + 1}/${dates.length} ${date} codes=${codes} docs=${docs}`);
    }
  }

  for (const [k, v] of Object.entries(bySecCode)) {
    const uniq = new Map();
    for (const d of v) uniq.set(d.docID, d);
    bySecCode[k] = Array.from(uniq.values());
  }

  const out = {
    version: 1,
    year,
    generatedAt: new Date().toISOString(),
    bySecCode,
  };

  fs.writeFileSync(outPath, JSON.stringify(out, null, 2), "utf8");
  console.log(`Wrote ${outPath}`);

  return { year, skipped: false, outPath };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const force = Boolean(args.force);

  const yearArg = args.year ? Number(args.year) : null;
  const yearsFromList = parseYearList(args.years);
  const fromYear = args.fromYear ? Number(args.fromYear) : args.startYear ? Number(args.startYear) : null;
  const toYear = args.toYear ? Number(args.toYear) : args.endYear ? Number(args.endYear) : null;

  let years;
  if (yearsFromList.length > 0) {
    years = yearsFromList;
  } else if (fromYear && toYear && Number.isFinite(fromYear) && Number.isFinite(toYear)) {
    years = parseYearList(`${fromYear}-${toYear}`);
  } else if (yearArg && Number.isFinite(yearArg)) {
    years = [yearArg];
  } else {
    years = [new Date().getFullYear() - 1];
  }

  const multiYear = years.length > 1;
  const includeCorrections = args.includeCorrections !== "false";
  const minIntervalMs = Number(args.minIntervalMs ?? 200);
  const retries = Number(args.retries ?? 3);

  const env = {
    ...process.env,
    ...readDotEnv(path.resolve(".env.local")),
  };
  const apiKey = env.VITE_EDINET_API_KEY || env.EDINET_API_KEY;
  if (!apiKey) {
    throw new Error("Missing API key. Set VITE_EDINET_API_KEY in .env.local or EDINET_API_KEY in env.");
  }

  const companiesPath = path.resolve("src/data/tse_companies.json");
  const companies = JSON.parse(fs.readFileSync(companiesPath, "utf8"));
  const secCodeSet = new Set();
  for (const c of companies) {
    if (c.secCode5) secCodeSet.add(String(c.secCode5));
    if (c.secCode4) secCodeSet.add(String(c.secCode4));
  }

  console.log(`Years: ${years.join(", ")} (force=${force})`);
  console.log(
    `Window: ${
      args.fromMD && args.toMD
        ? `fromMD=${args.fromMD} toMD=${args.toMD}`
        : `from=${args.from ?? "{year}-06-01"} to=${args.to ?? "{year}-07-31"}`
    }`,
  );

  const results = [];
  const failures = [];
  for (const year of years) {
    const { from, to } = resolveRangeForYear(args, year, multiYear);
    try {
      // eslint-disable-next-line no-await-in-loop
      const r = await buildIndexForYear({
        year,
        from,
        to,
        includeCorrections,
        minIntervalMs,
        retries,
        apiKey,
        secCodeSet,
        force,
      });
      results.push(r);
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      failures.push({ year, message });
      console.error(`Failed year=${year}: ${message}`);
      if (args.stopOnError) break;
    }
  }

  const done = results.filter((r) => !r.skipped);
  const skipped = results.filter((r) => r.skipped);
  console.log(`Done: ${done.length}, Skipped: ${skipped.length}, Failed: ${failures.length}`);
  if (failures.length > 0) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

