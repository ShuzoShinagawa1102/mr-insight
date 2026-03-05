# =========== みえるマン ドメイン用語集 ===========
# 各CSVファイル（assets/glossary/）から取り込んだ用語を
# ドメインモデルで使う正式名称として定義する。
#
# DDD の「ユビキタス言語」として、コード上でもこの用語集を参照できるようにする。

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ----------------------------
# 用語カテゴリ
# ----------------------------

class GlossaryCategory(str, Enum):
    """用語集のカテゴリ分類"""

    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"    # 財務諸表関連
    KPI = "KPI"                                    # 重要業績評価指標
    VALUATION = "VALUATION"                        # バリュエーション指標
    GOVERNANCE = "GOVERNANCE"                      # コーポレートガバナンス
    MA = "MA"                                      # M&A 関連
    ESG = "ESG"                                    # ESG・サステナビリティ
    CONSULTING = "CONSULTING"                      # 経営コンサルティング
    RISK = "RISK"                                  # リスク管理
    ACCOUNTING = "ACCOUNTING"                      # 会計・税務
    IR = "IR"                                      # IR・投資家関連
    HUMAN_CAPITAL = "HUMAN_CAPITAL"               # 人的資本
    STRATEGY = "STRATEGY"                          # 経営戦略
    OTHER = "OTHER"                                # その他


# ----------------------------
# 用語エントリ（Pydantic モデル）
# ----------------------------

class GlossaryTermEntry(BaseModel):
    """用語集の1エントリ"""

    ja_name: str                                   # 日本語名
    en_name: Optional[str] = None                  # 英語名
    category: GlossaryCategory = GlossaryCategory.OTHER
    description: Optional[str] = None             # 補足説明（任意）


# ----------------------------
# MetricName：MetricFact.name で使う正式な指標名
# （用語集から主要なものを抽出・英語化した定数）
# ----------------------------

class MetricName(str, Enum):
    """財務・KPI指標の正式名称（MetricFact.name に使う推奨値）

    各値は英語スネークケース。対応する日本語名はコメントに記載。
    これ以外の指標を扱う場合は自由文字列でも可だが、
    標準指標については本 Enum を使うことを推奨する。
    """

    # ===== 損益計算書 (P/L) =====
    REVENUE = "revenue"                          # 売上高
    COST_OF_SALES = "cost_of_sales"              # 売上原価
    GROSS_PROFIT = "gross_profit"                # 売上総利益
    SGA = "sga"                                  # 販売費及び一般管理費
    OPERATING_INCOME = "operating_income"        # 営業利益
    NON_OPERATING_INCOME = "non_operating_income"    # 営業外収益
    NON_OPERATING_EXPENSES = "non_operating_expenses"  # 営業外費用
    ORDINARY_INCOME = "ordinary_income"          # 経常利益
    EXTRAORDINARY_INCOME = "extraordinary_income"  # 特別利益
    EXTRAORDINARY_LOSS = "extraordinary_loss"    # 特別損失
    INCOME_BEFORE_TAX = "income_before_tax"      # 税引前当期純利益
    INCOME_TAXES = "income_taxes"                # 法人税等
    NET_INCOME = "net_income"                    # 当期純利益
    NET_INCOME_ATTRIBUTABLE = "net_income_attributable"  # 親会社株主に帰属する当期純利益
    COMPREHENSIVE_INCOME = "comprehensive_income"  # 包括利益
    EBITDA = "ebitda"                            # EBITDA
    EBIT = "ebit"                                # EBIT
    RD_EXPENSES = "rd_expenses"                  # 研究開発費
    DEPRECIATION_AMORTIZATION = "depreciation_amortization"  # 減価償却費
    GOODWILL_AMORTIZATION = "goodwill_amortization"  # のれん償却額
    FOREX_GAIN_LOSS = "forex_gain_loss"          # 為替差損益

    # ===== 貸借対照表 (B/S) =====
    TOTAL_ASSETS = "total_assets"                # 総資産
    CURRENT_ASSETS = "current_assets"            # 流動資産
    NON_CURRENT_ASSETS = "non_current_assets"    # 固定資産
    CASH_AND_EQUIVALENTS = "cash_and_equivalents"  # 現金及び現金同等物
    ACCOUNTS_RECEIVABLE = "accounts_receivable"  # 売掛金
    INVENTORIES = "inventories"                  # 棚卸資産
    PP_AND_E = "pp_and_e"                        # 有形固定資産
    INTANGIBLE_ASSETS = "intangible_assets"      # 無形固定資産
    GOODWILL = "goodwill"                        # のれん
    INVESTMENT_SECURITIES = "investment_securities"  # 投資有価証券
    DEFERRED_TAX_ASSETS = "deferred_tax_assets"  # 繰延税金資産
    TOTAL_LIABILITIES = "total_liabilities"      # 総負債
    CURRENT_LIABILITIES = "current_liabilities"  # 流動負債
    ACCOUNTS_PAYABLE = "accounts_payable"        # 買掛金
    SHORT_TERM_DEBT = "short_term_debt"          # 短期借入金
    CORPORATE_BONDS = "corporate_bonds"          # 社債
    LONG_TERM_DEBT = "long_term_debt"            # 長期借入金
    RETIREMENT_BENEFIT_LIABILITY = "retirement_benefit_liability"  # 退職給付引当金
    DEFERRED_TAX_LIABILITIES = "deferred_tax_liabilities"  # 繰延税金負債
    NET_ASSETS = "net_assets"                    # 純資産
    EQUITY = "equity"                            # 株主資本
    RETAINED_EARNINGS = "retained_earnings"      # 利益剰余金
    TREASURY_STOCK = "treasury_stock"            # 自己株式
    INTEREST_BEARING_DEBT = "interest_bearing_debt"  # 有利子負債

    # ===== キャッシュフロー計算書 (C/F) =====
    CFO = "cfo"                                  # 営業活動によるキャッシュフロー
    CFI = "cfi"                                  # 投資活動によるキャッシュフロー
    CFF = "cff"                                  # 財務活動によるキャッシュフロー
    FREE_CASH_FLOW = "free_cash_flow"            # フリーキャッシュフロー
    CAPEX = "capex"                              # 設備投資
    WORKING_CAPITAL = "working_capital"          # 運転資本

    # ===== 収益性指標 =====
    ROE = "roe"                                  # ROE（自己資本利益率）
    ROA = "roa"                                  # ROA（総資産利益率）
    ROIC = "roic"                                # ROIC（投下資本利益率）
    OPERATING_PROFIT_MARGIN = "operating_profit_margin"  # 売上高営業利益率
    ORDINARY_INCOME_MARGIN = "ordinary_income_margin"    # 売上高経常利益率
    NET_PROFIT_MARGIN = "net_profit_margin"      # 売上高純利益率
    GROSS_PROFIT_MARGIN = "gross_profit_margin"  # 売上高総利益率

    # ===== 株式・バリュエーション指標 =====
    EPS = "eps"                                  # 1株当たり当期純利益
    BPS = "bps"                                  # 1株当たり純資産
    DPS = "dps"                                  # 1株当たり配当金
    PER = "per"                                  # 株価収益率
    PBR = "pbr"                                  # 株価純資産倍率
    DIVIDEND_PAYOUT_RATIO = "dividend_payout_ratio"  # 配当性向
    DIVIDEND_YIELD = "dividend_yield"            # 配当利回り
    MARKET_CAP = "market_cap"                    # 時価総額
    ENTERPRISE_VALUE = "enterprise_value"        # エンタープライズバリュー
    EV_EBITDA = "ev_ebitda"                      # EV/EBITDA

    # ===== 安全性・効率性指標 =====
    EQUITY_RATIO = "equity_ratio"                # 自己資本比率
    CURRENT_RATIO = "current_ratio"              # 流動比率
    QUICK_RATIO = "quick_ratio"                  # 当座比率
    DE_RATIO = "de_ratio"                        # D/Eレシオ
    INTEREST_COVERAGE_RATIO = "interest_coverage_ratio"  # インタレスト・カバレッジ・レシオ
    TOTAL_ASSET_TURNOVER = "total_asset_turnover"  # 総資本回転率
    INVENTORY_TURNOVER = "inventory_turnover"    # 棚卸資産回転率
    RECEIVABLES_TURNOVER = "receivables_turnover"  # 売上債権回転率
    WACC = "wacc"                                # WACC（加重平均資本コスト）

    # ===== 成長率 =====
    REVENUE_GROWTH_RATE = "revenue_growth_rate"  # 売上成長率
    PROFIT_GROWTH_RATE = "profit_growth_rate"    # 利益成長率
    CAGR = "cagr"                                # CAGR（年平均成長率）

    # ===== 事業 KPI =====
    MARKET_SHARE = "market_share"                # 市場シェア
    CUSTOMER_SATISFACTION = "customer_satisfaction"  # 顧客満足度
    NPS = "nps"                                  # NPS（ネット・プロモーター・スコア）
    CAC = "cac"                                  # 顧客獲得コスト
    LTV = "ltv"                                  # 顧客生涯価値
    CHURN_RATE = "churn_rate"                    # 解約率
    RETENTION_RATE = "retention_rate"            # 継続率
    UTILIZATION_RATE = "utilization_rate"        # 稼働率
    CAPACITY_UTILIZATION_RATE = "capacity_utilization_rate"  # 設備稼働率

    # ===== ESG・人的資本 =====
    NUMBER_OF_EMPLOYEES = "number_of_employees"  # 従業員数
    FEMALE_MANAGER_RATIO = "female_manager_ratio"  # 女性管理職比率
    TURNOVER_RATE = "turnover_rate"              # 離職率
    CHILDCARE_LEAVE_RATE = "childcare_leave_rate"  # 育児休業取得率
    PAID_LEAVE_UTILIZATION_RATE = "paid_leave_utilization_rate"  # 有給休暇取得率
    GHG_EMISSIONS = "ghg_emissions"              # GHG排出量
