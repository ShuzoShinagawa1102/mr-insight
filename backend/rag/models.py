"""
Django ORM models for the rag application.

These models provide the persistence layer for the domain entities defined in
``rag.model.common``.  Complex embedded value-objects (Evidence, Period,
Money, MetricValue, Listing, Industry, …) are stored as JSONField so that the
schema stays flexible while the higher-level relations remain queryable.
"""

from django.db import models


# ---------------------------------------------------------------------------
# Choice constants (mirrors rag.model.common enums)
# ---------------------------------------------------------------------------

class PeriodKind(models.TextChoices):
    FY = "FY", "通期"
    Q = "Q", "四半期"
    H1 = "H1", "上期"
    H2 = "H2", "下期"
    TTM = "TTM", "過去12ヶ月"


class SourceKind(models.TextChoices):
    EDINET = "EDINET", "有価証券報告書 (EDINET)"
    TDNET = "TDNET", "適時開示 (TDnet)"
    IR_DECK = "IR_DECK", "決算説明資料"
    TRANSCRIPT = "TRANSCRIPT", "決算説明会書き起こし"
    NEWS = "NEWS", "ニュース"
    BLOG = "BLOG", "ブログ"
    SNS = "SNS", "SNS"
    MARKET = "MARKET", "市場データ"
    OTHER = "OTHER", "その他"


class FactType(models.TextChoices):
    METRIC = "METRIC", "数値"
    EVENT = "EVENT", "事象"
    STATEMENT = "STATEMENT", "主張"
    RISK = "RISK", "リスク"


class EventKind(models.TextChoices):
    M_AND_A = "M_AND_A", "M&A"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH", "製品発表"
    REGULATION = "REGULATION", "規制"
    LAWSUIT = "LAWSUIT", "訴訟"
    GUIDANCE_CHANGE = "GUIDANCE_CHANGE", "業績予想修正"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE", "経営陣変更"
    INCIDENT = "INCIDENT", "インシデント"
    OTHER = "OTHER", "その他"


class StatementKind(models.TextChoices):
    STRATEGY = "STRATEGY", "戦略"
    OUTLOOK = "OUTLOOK", "見通し"
    COMPETITIVE_ADVANTAGE = "COMPETITIVE_ADVANTAGE", "競争優位"
    MANAGEMENT_COMMENT = "MANAGEMENT_COMMENT", "経営コメント"
    OTHER = "OTHER", "その他"


class RiskKind(models.TextChoices):
    MARKET = "MARKET", "市場リスク"
    OPERATION = "OPERATION", "オペレーションリスク"
    LEGAL = "LEGAL", "法的リスク"
    FINANCIAL = "FINANCIAL", "財務リスク"
    GEO = "GEO", "地政学リスク"
    TECHNOLOGY = "TECHNOLOGY", "技術リスク"
    OTHER = "OTHER", "その他"


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------

class Company(models.Model):
    """上場企業・発行体の基本情報"""

    company_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="外部IDまたはシステム生成ID（ULID/UUID推奨）",
    )
    name = models.CharField(max_length=255, help_text="会社名（日本語）")
    name_en = models.CharField(max_length=255, blank=True, null=True, help_text="会社名（英語）")

    # 上場情報・業種は柔軟な構造なのでJSONFieldで保持
    # 例: [{"country": "JP", "exchange": "TSE", "ticker": "7203"}]
    listings = models.JSONField(default=list, blank=True)
    # 例: [{"scheme": "GICS", "code": "2510", "name": "自動車"}]
    industries = models.JSONField(default=list, blank=True)

    homepage = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    parent_company = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subsidiaries",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "会社"
        verbose_name_plural = "会社一覧"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.company_id})"


# ---------------------------------------------------------------------------
# SourceDocument
# ---------------------------------------------------------------------------

class SourceDocument(models.Model):
    """取り込んだ資料のメタ情報"""

    doc_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="外部IDまたはシステム生成ID",
    )
    kind = models.CharField(max_length=32, choices=SourceKind.choices)
    title = models.CharField(max_length=512)
    published_at = models.DateTimeField()
    url = models.URLField(blank=True, null=True)

    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="source_documents",
    )

    # 生データの格納先（S3キーなど）
    blob_ref = models.CharField(max_length=512, blank=True, null=True)
    extractor_version = models.CharField(max_length=64, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "資料"
        verbose_name_plural = "資料一覧"
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return f"{self.title} [{self.kind}]"


# ---------------------------------------------------------------------------
# Fact (abstract base) + concrete subtypes
# ---------------------------------------------------------------------------

class Fact(models.Model):
    """抽出された事実の基底モデル（抽象）"""

    fact_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="外部IDまたはfingerprint由来のID",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="%(class)s_facts",
    )
    fact_type = models.CharField(max_length=16, choices=FactType.choices)
    asof = models.DateTimeField(help_text="その事実が成立する時点")

    # Evidence リスト（JSONField: List[Evidence]）
    # 例: [{"doc_id": "doc_123", "locator": {"page": 5}, "quote": "...", "confidence": 0.9}]
    evidences = models.JSONField(default=list, blank=True)

    # 重複排除・統合用
    fingerprint = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class MetricFact(Fact):
    """数値系ファクト（売上、営業利益、MAUなど）"""

    name = models.CharField(max_length=128, help_text="指標名（例: revenue, op_income, MAU）")

    # Period（埋め込み）
    period_kind = models.CharField(
        max_length=8, choices=PeriodKind.choices, blank=True, null=True
    )
    period_year = models.IntegerField(blank=True, null=True)
    period_quarter = models.IntegerField(blank=True, null=True)

    # MetricValue（埋め込み）
    metric_value = models.DecimalField(max_digits=24, decimal_places=6)
    metric_unit = models.CharField(max_length=32)
    metric_raw = models.TextField(blank=True, null=True)

    # 前期比・前年比
    yoy = models.DecimalField(max_digits=12, decimal_places=6, blank=True, null=True)
    qoq = models.DecimalField(max_digits=12, decimal_places=6, blank=True, null=True)

    class Meta:
        verbose_name = "数値ファクト"
        verbose_name_plural = "数値ファクト一覧"

    def __str__(self) -> str:
        return f"{self.name}={self.metric_value} {self.metric_unit} (fp={self.fingerprint})"


class EventFact(Fact):
    """事象系ファクト（M&A、製品発表など）"""

    kind = models.CharField(max_length=32, choices=EventKind.choices)
    title = models.CharField(max_length=512)
    summary = models.TextField()
    impact = models.TextField(blank=True, null=True, help_text="定性的な影響説明")
    severity = models.IntegerField(blank=True, null=True, help_text="1〜5のスコア")

    class Meta:
        verbose_name = "事象ファクト"
        verbose_name_plural = "事象ファクト一覧"

    def __str__(self) -> str:
        return f"{self.title} [{self.kind}]"


class StatementFact(Fact):
    """主張・定性コメント系ファクト"""

    kind = models.CharField(max_length=32, choices=StatementKind.choices)
    text = models.TextField()
    speaker = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = "主張ファクト"
        verbose_name_plural = "主張ファクト一覧"

    def __str__(self) -> str:
        return f"[{self.kind}] {self.text[:80]}"


class RiskFact(Fact):
    """リスク系ファクト"""

    kind = models.CharField(max_length=32, choices=RiskKind.choices)
    title = models.CharField(max_length=512)
    description = models.TextField()
    likelihood = models.IntegerField(blank=True, null=True, help_text="発生可能性 1〜5")
    impact = models.IntegerField(blank=True, null=True, help_text="影響度 1〜5")

    class Meta:
        verbose_name = "リスクファクト"
        verbose_name_plural = "リスクファクト一覧"

    def __str__(self) -> str:
        return f"{self.title} [{self.kind}]"


# ---------------------------------------------------------------------------
# FinancialStatement
# ---------------------------------------------------------------------------

class FinancialStatement(models.Model):
    """正規化済み財務諸表（主要科目のみ）"""

    fs_id = models.CharField(max_length=64, unique=True, db_index=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="financial_statements",
    )

    # Period（埋め込み）
    period_kind = models.CharField(max_length=8, choices=PeriodKind.choices)
    period_year = models.IntegerField()
    period_quarter = models.IntegerField(blank=True, null=True)

    # P/L（JSONField: {"amount": "1234567890", "currency": "JPY"}）
    revenue = models.JSONField(blank=True, null=True)
    gross_profit = models.JSONField(blank=True, null=True)
    operating_income = models.JSONField(blank=True, null=True)
    net_income = models.JSONField(blank=True, null=True)

    # B/S
    total_assets = models.JSONField(blank=True, null=True)
    total_liabilities = models.JSONField(blank=True, null=True)
    equity = models.JSONField(blank=True, null=True)

    # C/F
    cfo = models.JSONField(blank=True, null=True)
    cfi = models.JSONField(blank=True, null=True)
    cff = models.JSONField(blank=True, null=True)

    evidences = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "財務諸表"
        verbose_name_plural = "財務諸表一覧"
        unique_together = [("company", "period_kind", "period_year", "period_quarter")]

    def __str__(self) -> str:
        return f"{self.company} {self.period_kind}{self.period_year}"


# ---------------------------------------------------------------------------
# Guidance
# ---------------------------------------------------------------------------

class Guidance(models.Model):
    """業績予想（ガイダンス）"""

    guidance_id = models.CharField(max_length=64, unique=True, db_index=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="guidances",
    )

    # Period（埋め込み）
    period_kind = models.CharField(max_length=8, choices=PeriodKind.choices)
    period_year = models.IntegerField()
    period_quarter = models.IntegerField(blank=True, null=True)

    metric_name = models.CharField(max_length=128)

    # MetricValue（埋め込み）
    forecast_value = models.DecimalField(max_digits=24, decimal_places=6)
    forecast_unit = models.CharField(max_length=32)
    forecast_raw = models.TextField(blank=True, null=True)

    updated_at = models.DateTimeField()
    evidences = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "業績予想"
        verbose_name_plural = "業績予想一覧"

    def __str__(self) -> str:
        return f"{self.company} {self.metric_name} {self.period_kind}{self.period_year}"


# ---------------------------------------------------------------------------
# ValuationSnapshot
# ---------------------------------------------------------------------------

class ValuationSnapshot(models.Model):
    """バリュエーション（時価総額・PER・PBRなど）のスナップショット"""

    snapshot_id = models.CharField(max_length=64, unique=True, db_index=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="valuation_snapshots",
    )
    asof = models.DateField()

    # Money value objects as JSON: {"amount": "1234567890", "currency": "JPY"}
    market_cap = models.JSONField(blank=True, null=True)
    enterprise_value = models.JSONField(blank=True, null=True)

    per = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    pbr = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    ev_ebitda = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    evidences = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "バリュエーション"
        verbose_name_plural = "バリュエーション一覧"
        ordering = ["-asof"]

    def __str__(self) -> str:
        return f"{self.company} @ {self.asof}"
