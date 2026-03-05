"""
管理コマンド: import_glossary

assets/glossary/ 以下の CSV ファイルを読み込み、GlossaryTerm モデルに
取り込む（upsert）。

使い方::

    python manage.py import_glossary

オプション::

    --file PATH   特定の CSV ファイルのみインポートする（省略時は全ファイル）
    --dry-run     DB への書き込みを行わずに内容を確認する
"""

from __future__ import annotations

import csv
import os
import uuid
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError

from rag.models import GlossaryCategory, GlossaryTerm

# リポジトリルートからの assets/glossary/ パス
GLOSSARY_DIR = (
    Path(__file__).resolve().parents[4] / "assets" / "glossary"
)

# ファイル名 → (エンコード, デフォルトカテゴリ) のマッピング
# カテゴリは後で ja_name に基づいてより詳細に分類することも可能。
FILE_CONFIG: dict[str, tuple[str, str]] = {
    "みえるマンドメイン辞書_企業経営.csv": ("utf-8-sig", GlossaryCategory.FINANCIAL_STATEMENT),
    "みえるマン_コンサル.csv": ("cp932", GlossaryCategory.CONSULTING),
    "みえるマン用語辞書.csv": ("cp932", GlossaryCategory.OTHER),
}

# 日本語名に含まれるキーワードでカテゴリを推定するルール（優先順位順）
_CATEGORY_RULES: list[tuple[list[str], str]] = [
    (
        ["売上", "営業利益", "経常利益", "純利益", "EPS", "BPS", "EBITDA",
         "EBIT", "減価償却", "のれん", "損益", "財務諸表", "貸借対照表",
         "キャッシュフロー", "資産", "負債", "純資産", "株主資本"],
        GlossaryCategory.FINANCIAL_STATEMENT,
    ),
    (
        ["ROE", "ROA", "ROIC", "ROI", "PER", "PBR", "EV/EBITDA",
         "時価総額", "バリュエーション", "株価", "配当"],
        GlossaryCategory.VALUATION,
    ),
    (
        ["KPI", "KGI", "CAGR", "NPS", "CAC", "LTV", "解約率",
         "継続率", "稼働率", "市場シェア", "顧客満足"],
        GlossaryCategory.KPI,
    ),
    (
        ["ガバナンス", "取締役", "監査", "CEO", "CFO", "COO", "CTO",
         "社長", "会長", "委員会", "コンプライアンス", "株主総会"],
        GlossaryCategory.GOVERNANCE,
    ),
    (
        ["M&A", "合併", "買収", "TOB", "MBO", "LBO", "PMI",
         "デューデリジェンス", "シナジー"],
        GlossaryCategory.MA,
    ),
    (
        ["ESG", "SDGs", "CSR", "サステナ", "カーボン", "GHG",
         "気候変動", "生物多様性", "TCFD", "TNFD", "SBT"],
        GlossaryCategory.ESG,
    ),
    (
        ["リスク", "BCP", "事業継続"],
        GlossaryCategory.RISK,
    ),
    (
        ["会計", "税", "IFRS", "J-GAAP", "監査意見", "引当金",
         "繰延税金", "減損", "棚卸資産", "評価方法", "償却方法"],
        GlossaryCategory.ACCOUNTING,
    ),
    (
        ["IR", "投資家", "アナリスト", "機関投資家", "株式公開",
         "上場", "証券取引所", "決算説明"],
        GlossaryCategory.IR,
    ),
    (
        ["従業員", "人材", "採用", "育児", "ダイバーシティ",
         "女性管理職", "エンゲージメント", "健康経営", "ウェルビーイング"],
        GlossaryCategory.HUMAN_CAPITAL,
    ),
    (
        ["戦略", "DX", "デジタル", "ポートフォリオ", "コンサル",
         "バリューチェーン", "ビジネスモデル", "アジャイル"],
        GlossaryCategory.STRATEGY,
    ),
]


def _infer_category(ja_name: str, default: str) -> str:
    """日本語名から用語カテゴリを推定する。"""
    for keywords, category in _CATEGORY_RULES:
        if any(kw in ja_name for kw in keywords):
            return category
    return default


class Command(BaseCommand):
    help = "assets/glossary/ の CSV ファイルを GlossaryTerm モデルに取り込む"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            metavar="PATH",
            help="特定の CSV ファイルのみインポートする（省略時は全ファイル）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="DB への書き込みを行わずに内容を確認する",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        target_file: Optional[str] = options.get("file")

        if not GLOSSARY_DIR.exists():
            raise CommandError(
                f"用語集ディレクトリが見つかりません: {GLOSSARY_DIR}"
            )

        files_to_process = (
            [Path(target_file)]
            if target_file
            else [GLOSSARY_DIR / fname for fname in FILE_CONFIG]
        )

        total_created = 0
        total_updated = 0

        for file_path in files_to_process:
            if not file_path.exists():
                self.stderr.write(self.style.WARNING(f"スキップ: {file_path} が見つかりません"))
                continue

            fname = file_path.name
            encoding, default_category = FILE_CONFIG.get(fname, ("utf-8-sig", GlossaryCategory.OTHER))

            created, updated = self._import_file(
                file_path, encoding, default_category, dry_run
            )
            total_created += created
            total_updated += updated
            self.stdout.write(
                self.style.SUCCESS(
                    f"{fname}: 作成={created} 更新={updated}"
                    + (" [dry-run]" if dry_run else "")
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n合計: 作成={total_created} 更新={total_updated}"
                + (" [dry-run]" if dry_run else "")
            )
        )

    def _import_file(
        self,
        file_path: Path,
        encoding: str,
        default_category: str,
        dry_run: bool,
    ) -> tuple[int, int]:
        """1 ファイル分のインポートを行い (created, updated) を返す。"""
        created = 0
        updated = 0
        source = file_path.stem

        with open(file_path, encoding=encoding, newline="", errors="replace") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ja_name = (row.get("日本語名") or "").strip()
                en_name = (row.get("英語名") or "").strip()

                if not ja_name:
                    continue

                category = _infer_category(ja_name, default_category)

                # term_id をソースファイル名＋日本語名のスラッグから生成
                term_id = _make_term_id(source, ja_name)

                if dry_run:
                    self.stdout.write(f"  [{category}] {ja_name} / {en_name}")
                    created += 1
                    continue

                _, was_created = GlossaryTerm.objects.update_or_create(
                    term_id=term_id,
                    defaults={
                        "ja_name": ja_name,
                        "en_name": en_name,
                        "category": category,
                        "source": source,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        return created, updated


def _make_term_id(source: str, ja_name: str) -> str:
    """ソースとja_nameから再現可能な一意IDを生成する（最大64文字）。"""
    raw = f"{source}:{ja_name}"
    # UUID5（名前空間 DNS）を使って安定した ID を生成
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw))
