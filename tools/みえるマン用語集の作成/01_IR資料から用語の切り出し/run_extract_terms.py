from __future__ import annotations

import json
import logging
import re
import shutil
import unicodedata
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from janome.tokenizer import Tokenizer

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except Exception:  # pragma: no cover
    pdfminer_extract_text = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


ROOT_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = ROOT_DIR / "resources"
OUTPUT_DIR = ROOT_DIR / "output"
WORDLIST_DIR = ROOT_DIR / "wordList"
WORKLOG_DIR = ROOT_DIR / "worklog"

MAX_TERMS_PER_COMPANY = 10_000
MAX_TERM_CHARS = 40
MIN_TERM_CHARS = 2

TOKENIZER = Tokenizer()

logging.getLogger("pypdf").setLevel(logging.ERROR)

STOPWORDS = {
    "当社",
    "本書",
    "重要",
    "内容",
    "場合",
    "以下",
    "なお",
    "また",
    "及び",
    "並びに",
    "その他",
    "各",
    "等",
}

CONNECTORS = {"・", "-", "－", "‐", "/", "／"}


RE_ONLY_DIGITS = re.compile(r"^\d+$")
RE_ONLY_NUM_PUNCT = re.compile(r"^[\d,.\-–—ー]+$")
RE_ONLY_HIRAGANA = re.compile(r"^[ぁ-ゖ]+$")
RE_DATE_LIKE = re.compile(
    r"^(?:\d{4}年\d{1,2}月\d{1,2}日|\d{4}/\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2})$"
)
RE_SECTION_LIKE = re.compile(r"^(?:第?\d+(?:章|節|項|期)|\d+(?:章|節|項))$")


@dataclass(frozen=True)
class PdfInfo:
    path: Path
    pages_total: int
    pages_with_text: int


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _clean_text(text: str) -> str:
    text = _nfkc(text)
    text = text.replace("\u00a0", " ").replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\r\n?", "\n", text)
    return text


def extract_pdf_pages_text(pdf_path: Path) -> tuple[list[str], PdfInfo]:
    if pdfminer_extract_text is not None:
        # pdfminer は日本語PDFの抽出精度が高く、抽出禁止メタデータの警告も出るため抑制する
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            raw_all = pdfminer_extract_text(str(pdf_path)) or ""
        pages = [_clean_text(p).strip() for p in raw_all.split("\f")]
        pages_text = [p for p in pages if p is not None]
        pages_with_text = sum(1 for p in pages_text if p)
        return pages_text, PdfInfo(
            path=pdf_path,
            pages_total=len(pages_text),
            pages_with_text=pages_with_text,
        )

    if PdfReader is None:  # pragma: no cover
        raise RuntimeError("PDFテキスト抽出ライブラリが見つかりません（pdfminer.six または pypdf が必要）")

    with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
        reader = PdfReader(str(pdf_path))
    pages_text: list[str] = []
    pages_with_text = 0

    for page in reader.pages:
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            raw = page.extract_text() or ""
        cleaned = _clean_text(raw).strip()
        pages_text.append(cleaned)
        if cleaned:
            pages_with_text += 1

    return pages_text, PdfInfo(
        path=pdf_path,
        pages_total=len(reader.pages),
        pages_with_text=pages_with_text,
    )


def _is_termish_surface(surface: str) -> bool:
    if not surface:
        return False
    if surface in CONNECTORS:
        return True
    if re.fullmatch(r"[A-Za-z0-9]+", surface):
        return True
    return False


def _is_noun_token(token) -> bool:
    pos = token.part_of_speech.split(",")
    pos1 = pos[0] if len(pos) > 0 else ""
    pos2 = pos[1] if len(pos) > 1 else ""

    if pos1 != "名詞":
        return False
    if pos2 in {"数", "非自立", "代名詞", "接尾"}:
        return False
    return True


def _iter_term_sequences(text: str) -> list[list[str]]:
    seq: list[str] = []
    sequences: list[list[str]] = []

    for offset in range(0, len(text), 10_000):
        chunk = text[offset : offset + 10_000]
        for token in TOKENIZER.tokenize(chunk):
            surface = token.surface
            if _is_noun_token(token) or _is_termish_surface(surface):
                seq.append(surface)
                continue

            if seq:
                sequences.append(seq)
                seq = []

    if seq:
        sequences.append(seq)

    return sequences


def _join_surfaces(surfaces: list[str]) -> str:
    return "".join(surfaces).strip()


def extract_candidates(text: str) -> list[str]:
    candidates: list[str] = []

    def flush_segment(segment: list[str], kinds: list[str]) -> None:
        if not segment:
            return

        max_tokens = 6
        for i, (surface, kind) in enumerate(zip(segment, kinds, strict=True)):
            if kind == "noun" and surface not in CONNECTORS:
                candidates.append(surface)

            noun_count = 0
            phrase_parts: list[str] = []
            for j in range(i, min(len(segment), i + max_tokens)):
                phrase_parts.append(segment[j])
                if kinds[j] == "noun":
                    noun_count += 1

                phrase = _join_surfaces(phrase_parts).strip("・-－‐/／")
            if noun_count >= 2 and phrase and len(phrase) <= MAX_TERM_CHARS:
                candidates.append(phrase)

    segment: list[str] = []
    kinds: list[str] = []

    for offset in range(0, len(text), 10_000):
        chunk = text[offset : offset + 10_000]
        for token in TOKENIZER.tokenize(chunk):
            surface = token.surface
            kind = None
            if _is_noun_token(token):
                kind = "noun"
            elif _is_termish_surface(surface):
                kind = "noun" if re.fullmatch(r"[A-Za-z0-9]+", surface) else "connector"

            if kind is None:
                flush_segment(segment, kinds)
                segment = []
                kinds = []
                continue

            segment.append(surface)
            kinds.append(kind)

    flush_segment(segment, kinds)
    return candidates


def _looks_bad(term: str, company: str) -> bool:
    if not term:
        return True

    term = term.strip()
    if not term:
        return True

    if len(term) < MIN_TERM_CHARS or len(term) > MAX_TERM_CHARS:
        return True

    if term in STOPWORDS:
        return True

    if RE_ONLY_DIGITS.fullmatch(term):
        return True

    if RE_ONLY_NUM_PUNCT.fullmatch(term):
        return True

    if RE_ONLY_HIRAGANA.fullmatch(term):
        return True

    if RE_DATE_LIKE.fullmatch(term):
        return True

    if RE_SECTION_LIKE.fullmatch(term):
        return True

    if "http" in term.lower():
        return True

    if "株式会社" in term:
        return True

    company_nfkc = _nfkc(company)
    if term == company_nfkc:
        return True
    if company_nfkc and company_nfkc in term and len(term) <= len(company_nfkc) + 4:
        return True

    if re.fullmatch(r"[\W_]+", term):
        return True

    return False


def _extract_context(text: str, term: str) -> str | None:
    idx = text.find(term)
    if idx < 0:
        return None

    left = max(0, idx - 80)
    right = min(len(text), idx + len(term) + 140)
    window = text[left:right]

    window = re.sub(r"\s+", " ", window).strip()
    if not window:
        return None

    before = window.rfind("。", 0, window.find(term))
    after = window.find("。", window.find(term) + len(term))

    if before != -1:
        window = window[before + 1 :]
    if after != -1:
        window = window[: after + 1]

    window = window.strip()
    if len(window) < 6:
        return None
    if len(window) > 160:
        window = window[:160].rstrip() + "…"
    return window


def _concept_type(term: str) -> str:
    metric_markers = (
        "高",
        "額",
        "利益",
        "損失",
        "収益",
        "売上",
        "費",
        "コスト",
        "率",
        "比率",
        "件数",
        "人数",
        "数量",
        "単価",
        "KPI",
        "ROE",
        "ROA",
        "EBITDA",
        "EPS",
        "PER",
        "PBR",
        "CF",
        "FCF",
    )
    event_markers = ("減損", "買収", "合併", "取得", "売却", "訴訟", "計上", "発生", "適用")
    structure_markers = (
        "セグメント",
        "方針",
        "戦略",
        "計画",
        "モデル",
        "システム",
        "プロセス",
        "体制",
        "ガバナンス",
        "内部統制",
    )
    entity_markers = ("委員会", "グループ", "子会社", "連結子会社", "部", "本部", "室", "会")

    if any(m in term for m in metric_markers):
        return "Metric"
    if any(m in term for m in event_markers):
        return "Event"
    if any(m in term for m in structure_markers):
        return "Structure"
    if any(m in term for m in entity_markers):
        return "Entity"
    return "Other"


def _category(term: str) -> str | None:
    if any(k in term for k in ("売上", "利益", "収益", "費用", "原価", "営業", "経常")):
        return "PL"
    if any(k in term for k in ("資産", "負債", "純資産", "のれん", "株主資本")):
        return "BS"
    if "キャッシュ" in term or term.endswith("CF") or "キャッシュ・フロー" in term:
        return "CF"
    if "リスク" in term:
        return "Risk"
    if any(k in term for k in ("ガバナンス", "内部統制", "コンプライアンス")):
        return "Governance"
    if any(k in term for k in ("セグメント", "KPI", "事業", "顧客", "戦略")):
        return "Business"
    return None


def _pos(term: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9]+", term):
        return "名詞"
    if any(ch.isalpha() for ch in term):
        return "名詞"
    return "名詞"


def _company_name_from_dirname(dirname: str) -> str:
    m = re.match(r"^\d+_(.+)$", dirname)
    return m.group(1) if m else dirname


def process_company_dir(company_dir: Path) -> dict:
    company = _company_name_from_dirname(company_dir.name)
    pdfs = sorted(company_dir.glob("*.pdf"))
    if not pdfs:
        return {
            "company": company,
            "pdfs": [],
            "terms": [],
            "pdf_infos": [],
            "notes": ["PDFが見つかりませんでした。"],
        }

    counter: Counter[str] = Counter()
    first_context: dict[str, str] = {}
    pdf_infos: list[PdfInfo] = []
    notes: list[str] = []

    for pdf in pdfs:
        pages_text, info = extract_pdf_pages_text(pdf)
        pdf_infos.append(info)
        if info.pages_with_text == 0:
            notes.append(f"{pdf.name}: テキスト抽出できたページが0でした（スキャンPDFの可能性）。")
            continue

        for page_text in pages_text:
            if not page_text:
                continue
            for raw_term in extract_candidates(page_text):
                term = _nfkc(raw_term).strip()
                term = term.strip("・-－‐/／")
                if _looks_bad(term, company):
                    continue
                counter[term] += 1
                if term not in first_context:
                    ctx = _extract_context(page_text, term)
                    if ctx:
                        first_context[term] = ctx

    if len(counter) > MAX_TERMS_PER_COMPANY:
        cutoff_count = counter.most_common(MAX_TERMS_PER_COMPANY)[-1][1]
        if cutoff_count <= 1:
            notes.append(
                f"候補語が {len(counter)} 語と多いため、出現2回以上の語に絞り込みました。"
            )
            counter = Counter({t: c for t, c in counter.items() if c >= 2})

    terms_sorted = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    top_terms = [t for t, _ in terms_sorted[:MAX_TERMS_PER_COMPANY]]

    entries = []
    for term in top_terms:
        entry = {
            "word": term,
            "description": first_context.get(term),
            "metadata": {
                "pos": _pos(term),
                "conceptType": _concept_type(term),
                "category": _category(term),
                "source": "有価証券報告書",
                "company": company,
            },
        }
        if entry["metadata"]["category"] is None:
            entry["metadata"].pop("category")
        if entry["description"] is None:
            entry.pop("description")
        entries.append(entry)

    return {
        "company": company,
        "pdfs": [p.name for p in pdfs],
        "pdf_infos": pdf_infos,
        "terms": top_terms,
        "entries": entries,
        "stats": {
            "unique_terms": len(counter),
            "selected_terms": len(top_terms),
        },
        "notes": notes,
    }


def write_outputs(result: dict) -> None:
    company: str = result["company"]
    company_dirname = result.get("company_dir", company)

    # New layout (requested): output/<company_dirname>/{PDFs, wordList/wordList.txt, metadata/wordList.jsonl, worklog.md}
    company_out_dir = OUTPUT_DIR / company_dirname
    (company_out_dir / "wordList").mkdir(parents=True, exist_ok=True)
    (company_out_dir / "metadata").mkdir(parents=True, exist_ok=True)

    # Copy PDFs only (resources-like)
    for pdf_name in result.get("pdfs", []):
        src = RESOURCES_DIR / company_dirname / pdf_name
        dst = company_out_dir / pdf_name
        if src.exists():
            shutil.copy2(src, dst)

    out_txt_path = company_out_dir / "wordList" / "wordList.txt"
    out_jsonl_path = company_out_dir / "metadata" / "wordList.jsonl"
    out_log_path = company_out_dir / "worklog.md"

    out_txt_path.write_text("\n".join(result["terms"]) + "\n", encoding="utf-8")
    jsonl_lines = [json.dumps(e, ensure_ascii=False) for e in result["entries"]]
    out_jsonl_path.write_text("\n".join(jsonl_lines) + "\n", encoding="utf-8")

    # Legacy layout (keep): wordList/<company>_wordList.(txt|jsonl), worklog/<company>_worklog.md
    WORDLIST_DIR.mkdir(parents=True, exist_ok=True)
    WORKLOG_DIR.mkdir(parents=True, exist_ok=True)
    legacy_txt_path = WORDLIST_DIR / f"{company}_wordList.txt"
    legacy_jsonl_path = WORDLIST_DIR / f"{company}_wordList.jsonl"
    legacy_log_path = WORKLOG_DIR / f"{company}_worklog.md"

    legacy_txt_path.write_text("\n".join(result["terms"]) + "\n", encoding="utf-8")
    legacy_jsonl_path.write_text("\n".join(jsonl_lines) + "\n", encoding="utf-8")

    pdf_infos: list[PdfInfo] = result.get("pdf_infos", [])
    total_pages = sum(i.pages_total for i in pdf_infos)
    text_pages = sum(i.pages_with_text for i in pdf_infos)
    notes = result.get("notes", [])

    lines = []
    lines.append(f"# 作業ログ: {company}")
    lines.append("")
    lines.append(f"- 実行日時: {_now_iso()}")
    lines.append(f"- 情報源: `resources/{company_dirname}`（有価証券報告書PDFのみ）")
    lines.append(f"- 入力PDF: {', '.join(result.get('pdfs', [])) if result.get('pdfs') else 'なし'}")
    lines.append(f"- PDFページ数: 合計{total_pages}頁（テキスト抽出できた頁: {text_pages}）")
    lines.append(f"- 用語候補（ユニーク）: {result.get('stats', {}).get('unique_terms', 0)}")
    lines.append(f"- 出力語数: {result.get('stats', {}).get('selected_terms', 0)}（上限 {MAX_TERMS_PER_COMPANY}）")
    lines.append("")
    lines.append("## 処理手順（要約）")
    lines.append("- PDFからテキスト抽出し、名詞中心に候補語を抽出")
    lines.append("- 除外ルール（一般語・助詞等・数値/日付/章番号・会社名・URL等）でフィルタ")
    lines.append("- 重複排除し、出現頻度順に最大10,000語を採用")
    lines.append("- `wordList/*.txt` と `wordList/*.jsonl` を生成（jsonlは最低限のメタデータ付与）")
    lines.append("")
    if notes:
        lines.append("## 例外・メモ")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")
    out_log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    legacy_log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not RESOURCES_DIR.exists():
        raise SystemExit(f"resources が見つかりません: {RESOURCES_DIR}")

    company_dirs = sorted([d for d in RESOURCES_DIR.iterdir() if d.is_dir()])
    if not company_dirs:
        raise SystemExit(f"企業フォルダが見つかりません: {RESOURCES_DIR}")

    for company_dir in company_dirs:
        result = process_company_dir(company_dir)
        result["company_dir"] = company_dir.name
        write_outputs(result)
        print(f"[OK] {result['company']}: {result.get('stats', {}).get('selected_terms', 0)} terms")


if __name__ == "__main__":
    main()
