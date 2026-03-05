# ドメインロジック仕様

プラットフォームが「稼げる」判断を支援するために必要な，**評価ロジック・計算ロジック・判断ルール**を定義する．
各ロジックは，ドメインモデルの属性・関係を入力とし，MetricObservation / ValuationOutput / Recommendation を出力する．

---

## 1. 評価ロジック（Evaluation Logic）

### 1-1. 企業品質スコア（Company Quality Score）

企業の本質的な強さを 0〜100 のスコアで表現する複合指標．

```
QualityScore = w1 * ProfitabilityScore
             + w2 * GrowthScore
             + w3 * BalanceSheetScore
             + w4 * GovernanceScore
             + w5 * ESGScore
```

| 構成要素 | デフォルトウェイト | 主な入力メトリクス |
|---|---|---|
| ProfitabilityScore | 30% | ROE, ROA, ROIC, 営業利益率, EBITDA マージン |
| GrowthScore | 25% | 売上成長率（CAGR 3yr）, EPS 成長率, FCF 成長率 |
| BalanceSheetScore | 20% | Net Debt / EBITDA, 流動比率, インタレスト・カバレッジ |
| GovernanceScore | 15% | 独立取締役比率, 監査意見, 関連当事者取引開示度 |
| ESGScore | 10% | ESG フレームワーク別スコア（TCFD 等） |

各構成要素は 0〜100 に正規化（業種別ピア比較による偏差値換算）．
外れ値は IQR ベースでウィンソライズする．

---

### 1-2. 投資魅力度評価（Investment Attractiveness）

バリュエーション・モメンタム・カタリストを組み合わせた多面評価．

```
AttractiveScore = ValuationAttractiveness
                * GrowthMomentum
                * CatalystPotential
                * (1 - RiskDiscount)
```

| 要素 | 評価方法 |
|---|---|
| ValuationAttractiveness | P/E, EV/EBITDA, P/FCF の対ピア割引率（≥ 20% 割安で高評価） |
| GrowthMomentum | 直近 2Q の売上 / EPS の上方サプライズ率 |
| CatalystPotential | 未解決 Hypothesis のうち thesis-positive な割合 |
| RiskDiscount | RiskItem の likelihoodScore × impactScore の加重平均（0〜1 に正規化） |

---

### 1-3. ガバナンス評価（Governance Score Calculation）

```
GovernanceScore = (独立取締役比率 × w_board)
                + (監査意見ポジティブ × w_audit)
                + (開示品質スコア × w_disclosure)

デフォルト: w_board = 0.4, w_audit = 0.3, w_disclosure = 0.3
```

各ウェイト（`w_board`, `w_audit`, `w_disclosure`）は `Assumption` エンティティとして管理し，
規制環境や投資方針に応じて上書き可能とする．

- **独立取締役比率**: `独立 BoardSeat 数 / 全 BoardSeat 数`
- **監査意見ポジティブ**: 適正意見 = 1.0, 限定付適正 = 0.5, 不適正 / 意見拒絶 = 0.0
- **開示品質スコア**: Filing の `accountingStandard` と DataQualityIssue 件数から算出（DataQualityIssue が 0 = 1.0, n 件増加ごとに -0.1）

---

### 1-4. リスク評価（Risk Score Calculation）

```
RiskScore(company) = Σ [ RiskItem.likelihoodScore × RiskItem.impactScore ]
                   / (全 RiskItem 数 × max_likelihood × max_impact)
```

- スコアが 0.7 以上の企業は「高リスク」フラグ
- 個別 RiskItem の `impactScore ≥ 4 AND likelihoodScore ≥ 4` の場合，`CRITICAL` としてアラート

---

## 2. 計算ロジック（Calculation Logic）

### 2-1. 財務メトリクス計算

以下はすべて `MetricDefinition.formula` として管理し，`ReportedValue` から `MetricObservation` を生成する際に適用する．

| メトリクス名 | 計算式 | 対応 StatementLineItem |
|---|---|---|
| 売上成長率（YoY） | `(Revenue_t - Revenue_t-1) / Revenue_t-1` | 売上高 |
| 営業利益率 | `OperatingIncome / Revenue` | 売上高・営業利益 |
| EBITDA | `OperatingIncome + DA` | 営業利益・減価償却費 |
| EBITDA マージン | `EBITDA / Revenue` | - |
| ROE | `NetIncome / AverageEquity` | 当期純利益・自己資本 |
| ROA | `NetIncome / AverageTotalAssets` | 総資産 |
| ROIC | `NOPAT / InvestedCapital` | - |
| EPS | `NetIncome / WeightedAvgSharesOutstanding` | - |
| FCF | `OperatingCashFlow - Capex` | 営業 CF・設備投資額 |
| Net Debt | `TotalDebt - CashAndEquivalents` | 有利子負債・現預金 |
| Net Debt / EBITDA | `NetDebt / EBITDA` | - |
| インタレスト・カバレッジ | `EBIT / InterestExpense` | - |

**正規化ルール（NormalizedValue 生成時）**:
1. 非継続事業損益を除外
2. 一時損益（Restatement 対象含む）を除外
3. 為替換算は `ReportingPeriod.endDate` 時点の中間レートを使用
4. スケール（百万円 / 千ドル等）は `ReportedValue.scale` を参照して統一

---

### 2-2. バリュエーション計算

#### DCF（Discounted Cash Flow）

```
IntrinsicValue = Σ [FCF_t / (1 + WACC)^t]  (t = 1..n)
               + TerminalValue / (1 + WACC)^n

TerminalValue = FCF_n × (1 + g) / (WACC - g)
```

- `WACC` は `Assumption` エンティティとして管理（デフォルト：リスクフリーレート + ベータ × エクイティリスクプレミアム）
- `g`（永続成長率）は `Assumption` として各 `Scenario` に紐付け
- 出力は `ValuationOutput.equityValue`, `ValuationOutput.targetPrice` に記録

#### 比較倍率法（Comparable Multiples）

```
TargetPrice_EV = Median(PeerGroup EV/EBITDA) × Company_EBITDA
TargetPrice_PE = Median(PeerGroup P/E) × Company_EPS
TargetPrice    = (TargetPrice_EV + TargetPrice_PE) / 2
```

- PeerGroup は `CompetitorRelation.relationType = peer` で定義
- アウトライアー除去：P/E が負またはデータなしの企業は除外

---

### 2-3. マーケットシェア計算

```
MarketShare_i = Company_i_Revenue / Σ(All_Companies_Revenue in Market)
```

- `MarketShareObservation.sharePct` に記録
- 集計基準（Revenue / Units / Volume）は `MarketShareObservation.methodology` で指定
- 年次・半期・四半期ごとにスナップショットを作成

---

### 2-4. シナリオ加重バリュエーション

```
WeightedTargetPrice = Σ [ Scenario_i.probability × Scenario_i.targetPrice ]
```

- 全 `Scenario` の probability 合計 = 1.0 であることをバリデーション（許容誤差は下記「データ整合性バリデーション」参照）
- シナリオ数は柔軟（最低 2 つ）．典型的には Bull / Base / Bear の 3 シナリオを推奨するが，規制変化・破壊的革新など追加シナリオも許容
- 出力は `InvestmentThesis` に紐付く `ValuationOutput` に反映

---

### 2-5. モニタリング指標の更新

`MonitoringRule.triggerCondition` の評価は以下の順序で行う：

1. `FilingPublished` イベント受信 → MetricObservation を再計算
2. 各 MonitoringRule の `triggerCondition`（例：`ROE < 0.08`）を評価
3. 条件成立 → `MonitoringTriggered` イベントを発火

---

## 3. 判断ルール（Decision Rules）

### 3-1. 投資推奨ルール（Recommendation Generation）

| 条件 | 推奨アクション | Conviction |
|---|---|---|
| `WeightedTargetPrice / CurrentPrice ≥ 1.30` AND `QualityScore ≥ 70` AND `RiskScore < 0.4` | `BUY` | `HIGH` |
| `WeightedTargetPrice / CurrentPrice ≥ 1.15` AND `QualityScore ≥ 50` | `BUY` | `MEDIUM` |
| `0.90 ≤ WeightedTargetPrice / CurrentPrice < 1.15` | `HOLD` | `MEDIUM` |
| `WeightedTargetPrice / CurrentPrice < 0.90` AND `RiskScore ≥ 0.6` | `SELL` | `HIGH` |
| `WeightedTargetPrice / CurrentPrice < 0.90` | `SELL` | `MEDIUM` |
| `RiskScore ≥ 0.8` | `SELL` | `HIGH`（リスク優先ルール） |

- 上記ルールは優先順位順（リスク優先ルールが最上位）
- `Recommendation.rationale` に適用されたルール ID と入力値を記録

---

### 3-2. 仮説ステータス更新ルール（Hypothesis State Transition）

```
状態遷移: draft → testing → confirmed / falsified / stale
```

| 遷移 | 条件 |
|---|---|
| `draft → testing` | `testMethod` に対応するデータが取得可能になった |
| `testing → confirmed` | `falsificationCondition` が **成立しない** まま `testMethod` の結果が `expected range` に収まった |
| `testing → falsified` | `falsificationCondition` が成立（例：「3Q 連続で ROE < 8%」等） |
| `testing → stale` | `effectiveTo` を超過，または関連 Filing が 2 期以上未更新 |

---

### 3-3. アラート発火ルール（Alert Rules）

以下の条件を満たした場合，`MonitoringTriggered` イベントを生成し，ユーザーに通知する．

| 分類 | 条件 | 優先度 |
|---|---|---|
| バリュエーション乖離 | `|CurrentPrice - WeightedTargetPrice| / WeightedTargetPrice ≥ 0.20` | HIGH |
| 財務悪化 | `Net Debt / EBITDA ≥ 5.0` OR `インタレスト・カバレッジ < 1.5` | HIGH |
| ガイダンス下方修正 | `GuidanceRevised` イベント + 修正幅 ≥ -10% | MEDIUM |
| 仮説棄却 | `HypothesisFalsified` イベント発火 | HIGH |
| 経営陣交代 | `ManagementChanged`（CEO / CFO / CTO） | MEDIUM |
| 重大リスク出現 | `RiskItem.likelihoodScore ≥ 4 AND impactScore ≥ 4` | HIGH |
| データ品質低下 | `DataQualityIssue` が 3 件以上かつ severity = high | MEDIUM |

---

### 3-4. ポートフォリオ構築ルール（Portfolio Construction Rules）

プロ投資家がポートフォリオを組む際のガードレール．

| ルール | 内容 |
|---|---|
| 集中度制限 | 単一銘柄の `OwnershipHolding.ownershipPct` が NAV の 20% を超えない |
| セクター分散 | 同一 `IndustryTaxonomy.code`（大分類）への配分が NAV の 40% を超えない |
| 国別分散 | 同一 `Organization.countryCode` への配分が NAV の 50% を超えない |
| 流動性チェック | `isListed = false` の企業への合計配分が NAV の 30% を超えない |
| リスク上限 | ポートフォリオ全体の加重平均 `RiskScore ≥ 0.6` の場合，新規 BUY 推奨を停止 |

---

### 3-5. データ整合性バリデーション（Data Integrity Rules）

| チェック項目 | ルール |
|---|---|
| シナリオ確率合計 | `Σ Scenario.probability = 1.0 (± PROBABILITY_TOLERANCE)`．`PROBABILITY_TOLERANCE` はシステム定数（デフォルト 0.001）として設定ファイルで管理 |
| 持分合計 | `Σ OwnershipHolding.ownershipPct ≤ 1.0` （同一 Company の同一 asOfDate） |
| 財務期間整合 | `ReportingPeriod.startDate < ReportingPeriod.endDate` |
| バリュエーション通貨 | `ValuationModel.currency = ValuationOutput.currency` |
| ガイダンス矛盾 | `Guidance.low ≤ Guidance.high` |
| 在任期間 | `BoardSeat.startDate ≤ BoardSeat.endDate` |
