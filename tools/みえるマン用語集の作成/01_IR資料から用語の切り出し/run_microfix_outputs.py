from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"


GENERIC_STOPWORDS = {
    "会社",
    "期間",
    "事項",
    "可能",
    "状況",
    "方法",
    "当該",
    "上記",
    "記載",
    "提出",
    "書類",
    "年度",
    "月",
    "日",
    "時点",
    "現在",
    "当期",
    "当社",
}

FORM_TERMS = {
    "EDINET",
    "EDINET提出書類",
    "提出書類",
    "有価証券報告書",
    "有価証券報告",
    "証券報告",
}

RE_EDINET_CODE = re.compile(r"E\d{5}")
RE_HAS_BRACKETS = re.compile(r"[【】]")
RE_ONLY_NUM_PUNCT = re.compile(r"^[\d,.\-–—/]+$")
RE_FOOTNOTE = re.compile(r"^(?:\(\d+\)|\d+\))$")
RE_DATE_FRAGMENT = re.compile(
    r"(?:\d{4}年|\d{1,2}月\d{0,2}(?:日)?|\d{4}/\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2})"
)
RE_MONTH_LEADING = re.compile(r"^月\d+(?:日)?$")
RE_MONTH_TRAILING = re.compile(r"^\d+月$")
RE_PAGE_FRACTION = re.compile(r"^\d+\s*/\s*\d+$")
RE_SECTION = re.compile(r"^(?:第?\d+(?:章|節|項|期)|\d+(?:章|節|項))$")
RE_UNIT_FRAGMENT = re.compile(r"(?:単位|百万円|千円|円|株|％|%|回|人|件|台|社|日|月|年)")
RE_PARENS = re.compile(r"[()（）]")

RE_PHONE = re.compile(r"\b0\d{1,4}-\d{1,4}-\d{3,4}\b")
RE_ADDRESS_LIKE = re.compile(
    r"(?:東京都|北海道|(?:京都|大阪)府|.{2,3}県).*(?:市|区|町|村).*(?:丁目|番|号|\d{1,4}-\d{1,4})"
)


@dataclass(frozen=True)
class FixStats:
    words_in: int
    words_out: int
    jsonl_in: int
    jsonl_out: int
    desc_dropped: int
    words_dropped: int


def _now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _company_name_from_dirname(dirname: str) -> str:
    m = re.match(r"^\d+_(.+)$", dirname)
    return m.group(1) if m else dirname


def _is_noisy_word(word: str, company: str) -> bool:
    w = word.strip()
    if not w:
        return True

    if w in FORM_TERMS:
        return True

    if w in GENERIC_STOPWORDS:
        return True

    if RE_EDINET_CODE.search(w):
        return True

    if RE_HAS_BRACKETS.search(w):
        return True

    if RE_ONLY_NUM_PUNCT.fullmatch(w):
        return True

    if RE_FOOTNOTE.fullmatch(w):
        return True

    if RE_PAGE_FRACTION.fullmatch(w):
        return True

    if RE_SECTION.fullmatch(w):
        return True

    if RE_DATE_FRAGMENT.search(w):
        return True

    if RE_MONTH_LEADING.fullmatch(w) or RE_MONTH_TRAILING.fullmatch(w):
        return True

    # 括弧の片割れだけ残る断片を除去（例: "(新規公開"）
    if ("(" in w or ")" in w or "（" in w or "）" in w) and (
        w.count("(") != w.count(")") or w.count("（") != w.count("）")
    ):
        return True

    # 単位や注記の断片（括弧付き/末尾括弧など）は原則ノイズ
    if RE_PARENS.search(w) and RE_UNIT_FRAGMENT.search(w):
        return True
    if (w.endswith(")") or w.endswith("）")) and RE_UNIT_FRAGMENT.search(w):
        return True
    if w.endswith(":") and "単位" in w:
        return True

    # 会社名そのものは削除（再利用性が低い）
    if w == company:
        return True

    return False


def _is_noisy_description(desc: str) -> bool:
    d = desc.strip()
    if not d:
        return True

    # 提出フォーム/表紙由来の強いシグナル
    if "EDINET提出書類" in d or "【表紙】" in d or "【提出" in d:
        return True
    if "財務局長" in d or "電話番号" in d:
        return True
    if RE_PHONE.search(d):
        return True
    if "【会社名】" in d or "【英訳名】" in d or "【代表者" in d:
        return True

    # 住所っぽい記述（用語の説明ではない）
    if RE_ADDRESS_LIKE.search(d):
        return True

    # 数字・記号だらけの断片
    digits = sum(ch.isdigit() for ch in d)
    if digits / max(1, len(d)) > 0.35 and len(d) < 120:
        return True

    # 文として短すぎる断片
    if len(d) < 10:
        return True

    return False


def _load_words(wordlist_path: Path) -> list[str]:
    return [
        line.strip()
        for line in wordlist_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_words(wordlist_path: Path, words: list[str]) -> None:
    wordlist_path.write_text("\n".join(words) + "\n", encoding="utf-8")


def _load_jsonl(jsonl_path: Path) -> list[dict]:
    items: list[dict] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        items.append(json.loads(s))
    return items


def _write_jsonl(jsonl_path: Path, items: list[dict]) -> None:
    lines = [json.dumps(item, ensure_ascii=False) for item in items]
    jsonl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def microfix_company(company_out_dir: Path) -> FixStats:
    company = _company_name_from_dirname(company_out_dir.name)
    wordlist_path = company_out_dir / "wordList" / "wordList.txt"
    jsonl_path = company_out_dir / "metadata" / "wordList.jsonl"
    worklog_path = company_out_dir / "worklog.md"

    if not wordlist_path.exists():
        raise FileNotFoundError(wordlist_path)
    if not jsonl_path.exists():
        raise FileNotFoundError(jsonl_path)

    words_in = _load_words(wordlist_path)
    keep_words: list[str] = []
    seen = set()
    for w in words_in:
        if _is_noisy_word(w, company):
            continue
        if w in seen:
            continue
        seen.add(w)
        keep_words.append(w)

    items_in = _load_jsonl(jsonl_path)
    items_out: list[dict] = []
    desc_dropped = 0

    keep_set = set(keep_words)
    for item in items_in:
        word = (item.get("word") or "").strip()
        if not word or word not in keep_set:
            continue
        desc = item.get("description")
        if isinstance(desc, str) and _is_noisy_description(desc):
            item = dict(item)
            item.pop("description", None)
            desc_dropped += 1
        items_out.append(item)

    # jsonl の順序を wordList に揃える（同一wordは最初の1件のみ採用）
    by_word: dict[str, dict] = {}
    for item in items_out:
        w = item["word"]
        if w not in by_word:
            by_word[w] = item
    items_out_ordered = [by_word[w] for w in keep_words if w in by_word]

    _write_words(wordlist_path, keep_words)
    _write_jsonl(jsonl_path, items_out_ordered)

    # worklog に追記（存在しない場合は新規作成）
    removed = len(words_in) - len(keep_words)
    log_lines = []
    if worklog_path.exists():
        log_lines.append(worklog_path.read_text(encoding="utf-8").rstrip())
        log_lines.append("")
    else:
        log_lines.append(f"# 作業ログ: {company}")
        log_lines.append("")

    log_lines.append("## 微修正（バリ取り）")
    log_lines.append(f"- 実行日時: {_now_local()}")
    log_lines.append("- 対象: `wordList/wordList.txt`, `metadata/wordList.jsonl`")
    log_lines.append(f"- 用語: {len(words_in)} → {len(keep_words)}（削除 {removed}）")
    log_lines.append(f"- jsonl: {len(items_in)} → {len(items_out_ordered)}")
    log_lines.append(f"- description削除: {desc_dropped}")
    log_lines.append(
        "- ルール要旨: EDINET/提出フォーム/EDINETコード/日付断片/脚注/単位断片/汎用語/会社名そのものを除去"
    )
    log_lines.append("")
    worklog_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    return FixStats(
        words_in=len(words_in),
        words_out=len(keep_words),
        jsonl_in=len(items_in),
        jsonl_out=len(items_out_ordered),
        desc_dropped=desc_dropped,
        words_dropped=removed,
    )


def main() -> None:
    if not OUTPUT_DIR.exists():
        raise SystemExit(f"output が見つかりません: {OUTPUT_DIR}")

    company_dirs = sorted([d for d in OUTPUT_DIR.iterdir() if d.is_dir()])
    if not company_dirs:
        raise SystemExit(f"企業ディレクトリがありません: {OUTPUT_DIR}")

    total_words_in = total_words_out = 0
    total_desc_dropped = 0
    for d in company_dirs:
        stats = microfix_company(d)
        total_words_in += stats.words_in
        total_words_out += stats.words_out
        total_desc_dropped += stats.desc_dropped
        print(
            f"[OK] {d.name}: words {stats.words_in}->{stats.words_out}, jsonl {stats.jsonl_in}->{stats.jsonl_out}, desc_drop {stats.desc_dropped}"
        )

    print(
        f"[DONE] companies={len(company_dirs)}, words_total {total_words_in}->{total_words_out}, desc_drop_total={total_desc_dropped}"
    )


if __name__ == "__main__":
    main()
