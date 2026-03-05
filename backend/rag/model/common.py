# =========== みえるマン AI driven 投資家向け統合データ分析プラットフォーム ===========
# 資料（PDF/HTML/CSV/ニュース等）を読み込んだ後、
# 「根拠(Evidence)つきの投資ドメインモデル」へ変換して保存・検索・推論するための骨格。

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Literal, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ----------------------------
# 基本：識別子・期間・単位
# ----------------------------

Id = str  # 実運用では ULID/UUID 等に置換

class PeriodKind(str, Enum):
    FY = "FY"      # 通期
    Q = "Q"        # 四半期
    H1 = "H1"      # 上期
    H2 = "H2"      # 下期
    TTM = "TTM"    # 過去12ヶ月


class MoneyCurrency(str, Enum):
    JPY = "JPY"
    USD = "USD"
    EUR = "EUR"


class Unit(str, Enum):
    COUNT = "count"
    PERCENT = "percent"
    JPY = "JPY"
    USD = "USD"
    PERSON = "person"
    YEN_MN = "JPY_mn"  # 百万円など必要なら拡張


class Period(BaseModel):
    kind: PeriodKind
    year: int = Field(ge=1900, le=2100)
    quarter: Optional[int] = Field(default=None, ge=1, le=4)

    @field_validator("quarter")
    @classmethod
    def quarter_required_for_q(cls, v, info):
        kind = info.data.get("kind")
        if kind == PeriodKind.Q and v is None:
            raise ValueError("kind=Q の場合 quarter が必要")
        if kind != PeriodKind.Q and v is not None:
            raise ValueError("kind!=Q の場合 quarter は不要")
        return v


class Money(BaseModel):
    amount: Decimal
    currency: MoneyCurrency

    @field_validator("amount")
    @classmethod
    def money_not_nan(cls, v: Decimal):
        # Decimal の NaN は通常使わない前提
        if str(v).lower() == "nan":
            raise ValueError("Money.amount must not be NaN")
        return v


class MetricValue(BaseModel):
    """数値メトリクスの一般形（売上、営業利益率、ユーザー数など）"""
    value: Decimal
    unit: Unit
    # 正規化前後の情報や変換元単位を残したい場合に使う
    raw: Optional[str] = None


# ----------------------------
# 1) 取り込み：資料（ソース）と根拠
# ----------------------------

class SourceKind(str, Enum):
    EDINET = "EDINET"          # 有報
    TDNET = "TDNET"            # 適時開示
    IR_DECK = "IR_DECK"        # 決算説明資料
    TRANSCRIPT = "TRANSCRIPT"  # 決算説明会書き起こし
    NEWS = "NEWS"
    BLOG = "BLOG"
    SNS = "SNS"
    MARKET = "MARKET"          # 株価等（時系列）
    OTHER = "OTHER"


class SourceDocument(BaseModel):
    """読み込んだ「資料」そのもの（メタ情報）"""
    id: Id
    kind: SourceKind
    title: str
    published_at: datetime
    url: Optional[HttpUrl] = None

    # 会社特定ができるなら入れる（あとで解決してもOK）
    company_id: Optional[Id] = None

    # 生データ格納先（S3キーなど）
    blob_ref: Optional[str] = None

    # 解析結果のバージョン管理（抽出器のバージョン）
    extractor_version: Optional[str] = None


class Evidence(BaseModel):
    """モデルの各主張/数値が、どの資料のどこに書いてあったかを追跡するための根拠"""
    doc_id: Id
    # PDFならページ、HTMLならセレクタ、テキストなら行番号など
    locator: Dict[str, Any] = Field(default_factory=dict)
    quote: Optional[str] = None  # 25 words制限等はアプリ側で管理
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)


# ----------------------------
# 2) 中核：Company と市場識別子
# ----------------------------

class Country(str, Enum):
    JP = "JP"
    US = "US"
    EU = "EU"
    OTHER = "OTHER"


class Listing(BaseModel):
    """上場情報（銘柄コード等）"""
    country: Country
    exchange: str                 # TSE, NASDAQ など
    ticker: str                   # 7203, AAPL など
    isin: Optional[str] = None
    currency: Optional[MoneyCurrency] = None


class Industry(BaseModel):
    """業種分類（複数体系を持てるようにする）"""
    scheme: str                   # e.g. "GICS", "東証33業種"
    code: Optional[str] = None
    name: str


class Company(BaseModel):
    id: Id
    name: str
    name_en: Optional[str] = None

    listings: List[Listing] = Field(default_factory=list)
    industries: List[Industry] = Field(default_factory=list)

    homepage: Optional[HttpUrl] = None
    description: Optional[str] = None

    # 競合や親子などの関係は Graph で表現する前提で、ID参照だけに留める案
    parent_company_id: Optional[Id] = None
    subsidiary_company_ids: List[Id] = Field(default_factory=list)


# ----------------------------
# 3) 抽出された「事実」：イベント・主張・数値
# ----------------------------

class FactType(str, Enum):
    METRIC = "METRIC"        # 数値（売上、利益、ARPU…）
    EVENT = "EVENT"          # 事象（M&A, リコール, 訴訟…）
    STATEMENT = "STATEMENT"  # 文章主張（戦略、見通し、定性）
    RISK = "RISK"            # リスク項目


class FactBase(BaseModel):
    id: Id
    company_id: Id
    fact_type: FactType
    asof: datetime                      # その事実が成立する時点
    evidences: List[Evidence] = Field(default_factory=list)

    # 統合・重複排除用（同一性判定やクラスタリング）
    fingerprint: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class MetricFact(FactBase):
    fact_type: Literal[FactType.METRIC] = FactType.METRIC

    name: str                           # "revenue", "op_income", "MAU" 等（辞書化推奨）
    period: Optional[Period] = None     # 財務系は period 付与が多い
    value: MetricValue
    # 前期比・前年差など派生値は計算で出すか、明示的に保持
    yoy: Optional[Decimal] = None       # % ではなく 0.12 などで統一してもよい
    qoq: Optional[Decimal] = None


class EventKind(str, Enum):
    M_AND_A = "M_AND_A"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"
    REGULATION = "REGULATION"
    LAWSUIT = "LAWSUIT"
    GUIDANCE_CHANGE = "GUIDANCE_CHANGE"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    INCIDENT = "INCIDENT"
    OTHER = "OTHER"


class EventFact(FactBase):
    fact_type: Literal[FactType.EVENT] = FactType.EVENT

    kind: EventKind
    title: str
    summary: str
    impact: Optional[str] = None  # "売上増の可能性", "コスト増" 等を定性で
    severity: Optional[int] = Field(default=None, ge=1, le=5)


class StatementKind(str, Enum):
    STRATEGY = "STRATEGY"
    OUTLOOK = "OUTLOOK"
    COMPETITIVE_ADVANTAGE = "COMPETITIVE_ADVANTAGE"
    MANAGEMENT_COMMENT = "MANAGEMENT_COMMENT"
    OTHER = "OTHER"


class StatementFact(FactBase):
    fact_type: Literal[FactType.STATEMENT] = FactType.STATEMENT

    kind: StatementKind
    text: str
    # 「誰が言ったか」（社長、CFO、記事筆者）
    speaker: Optional[str] = None


class RiskKind(str, Enum):
    MARKET = "MARKET"
    OPERATION = "OPERATION"
    LEGAL = "LEGAL"
    FINANCIAL = "FINANCIAL"
    GEO = "GEO"
    TECHNOLOGY = "TECHNOLOGY"
    OTHER = "OTHER"


class RiskFact(FactBase):
    fact_type: Literal[FactType.RISK] = FactType.RISK

    kind: RiskKind
    title: str
    description: str
    likelihood: Optional[int] = Field(default=None, ge=1, le=5)
    impact: Optional[int] = Field(default=None, ge=1, le=5)


# ----------------------------
# 4) 財務：FS（簡易版） + セグメント
# ----------------------------

class FinancialStatement(BaseModel):
    """FSは正規化済みの主要科目だけ保持（詳細は別テーブル/別モデルへ）"""
    id: Id
    company_id: Id
    period: Period

    revenue: Optional[Money] = None
    gross_profit: Optional[Money] = None
    operating_income: Optional[Money] = None
    net_income: Optional[Money] = None

    # B/S
    total_assets: Optional[Money] = None
    total_liabilities: Optional[Money] = None
    equity: Optional[Money] = None

    # C/F
    cfo: Optional[Money] = None
    cfi: Optional[Money] = None
    cff: Optional[Money] = None

    evidences: List[Evidence] = Field(default_factory=list)


class SegmentMetric(BaseModel):
    segment_name: str
    period: Period
    revenue: Optional[Money] = None
    operating_income: Optional[Money] = None
    evidences: List[Evidence] = Field(default_factory=list)


# ----------------------------
# 5) 予想（ガイダンス）・コンセンサス・バリュエーション
# ----------------------------

class Guidance(BaseModel):
    id: Id
    company_id: Id
    period: Period
    metric_name: str                       # "revenue", "op_income" など
    forecast: MetricValue
    updated_at: datetime
    evidences: List[Evidence] = Field(default_factory=list)


class ValuationSnapshot(BaseModel):
    id: Id
    company_id: Id
    asof: date

    market_cap: Optional[Money] = None
    enterprise_value: Optional[Money] = None

    per: Optional[Decimal] = None
    pbr: Optional[Decimal] = None
    ev_ebitda: Optional[Decimal] = None

    evidences: List[Evidence] = Field(default_factory=list)


# ----------------------------
# 6) 集約ビュー：投資家が見たい「会社の現在地」
# ----------------------------

class CompanyProfileView(BaseModel):
    """
    UI/回答用の集約（ドメインの“読みモデル”）
    - 生成物なので、永続化はキャッシュ扱いでもよい
    """
    company: Company
    latest_financials: Optional[FinancialStatement] = None
    latest_valuation: Optional[ValuationSnapshot] = None

    recent_events: List[EventFact] = Field(default_factory=list)
    key_risks: List[RiskFact] = Field(default_factory=list)
    key_statements: List[StatementFact] = Field(default_factory=list)

    # 重要KPI（会社ごとに変わるので辞書形式）
    kpis: Dict[str, MetricFact] = Field(default_factory=dict)


# ----------------------------
# 7) 変換（資料 -> モデル）で必要になる「抽出結果」中間表現
# ----------------------------

class ExtractedItemType(str, Enum):
    TABLE_ROW = "TABLE_ROW"
    SENTENCE = "SENTENCE"
    KEY_VALUE = "KEY_VALUE"


class ExtractedItem(BaseModel):
    """
    OCR / PDFパース / HTML抽出 で得た最小単位
    ここから正規化して Fact / FS / Guidance に落とす
    """
    id: Id
    doc_id: Id
    item_type: ExtractedItemType

    text: str
    # 表の行/列など構造情報
    structure: Dict[str, Any] = Field(default_factory=dict)

    evidence: Evidence


class NormalizationResult(BaseModel):
    """
    変換パイプラインの「出力」まとめ
    - ここから永続化へ
    """
    company_id: Id

    facts: List[Union[MetricFact, EventFact, StatementFact, RiskFact]] = Field(default_factory=list)
    financials: List[FinancialStatement] = Field(default_factory=list)
    segment_metrics: List[SegmentMetric] = Field(default_factory=list)
    guidances: List[Guidance] = Field(default_factory=list)
    valuations: List[ValuationSnapshot] = Field(default_factory=list)

    # 追跡用
    source_doc_ids: List[Id] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)