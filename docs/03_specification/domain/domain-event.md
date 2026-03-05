# ドメインイベント仕様

各ドメインが「何をきっかけに，どう振る舞うか」を定義する．
イベントは **発生 → 状態変化 → 副作用** の連鎖として表現し，RAG エンジン・分析ロジック・通知システムが
これを購読（Subscribe）することで，プラットフォーム全体の一貫性を保つ．

### イベント処理の保証事項

| 項目 | 方針 |
|---|---|
| **順序保証** | 同一エンティティ（同一 Company ID 等）に対するイベントは発生順に処理する（per-entity 順序保証）．異なるエンティティ間は並列処理可 |
| **べき等性** | 同一イベント ID の重複受信は無視する（exactly-once セマンティクス） |
| **結果整合性** | 副作用（下流エンティティの更新）は最終的整合性（Eventual Consistency）で処理する．同時更新が競合した場合は楽観的ロック（バージョン番号）で解決 |
| **失敗時の挙動** | 処理失敗イベントはデッドレターキューに格納し，`DataQualityIssue` を生成して人手レビューを促す |

---

## 1. Company（企業）

企業はプラットフォームの中心エンティティであり，最も多くのイベントを発生させる．

| イベント名 | トリガー条件 | 主な状態変化 | 副作用（下流） |
|---|---|---|---|
| `CompanyRegistered` | 新規企業が登録された | `status = active` | Investor / Market へ通知 |
| `CompanyListed` | 株式市場への上場が確定 | `isListed = true`，Listing 作成 | SecurityCreated イベント発火 |
| `CompanyDelisted` | 上場廃止（倒産・非公開化等） | `isListed = false`，Listing.status = delisted | OwnershipHolding の評価停止 |
| `CompanyMerged` | M&A クロージング | 存続会社に BusinessSegment / LegalEntity が統合 | CapTableSnapshot 更新，OwnershipHolding 再計算 |
| `CompanySpunOff` | 事業分離完了 | 新 Company エンティティ作成，BusinessSegment 移管 | 新 CapTableSnapshot 生成 |
| `CompanyDissolved` | 法人格消滅 | `status = dissolved`，dissolvedDate 設定 | 全 OwnershipHolding を終了状態に |
| `ManagementChanged` | CEO/CFO 等の交代発令 | OfficerRole の endDate 設定，新 OfficerRole 作成 | GovernanceEvent 生成，Hypothesis 再評価トリガー |
| `SegmentRestructured` | 事業セグメントの統廃合 | BusinessSegment の effectiveTo 更新 / 新規作成 | MetricObservation の集計基準変更通知 |
| `FacilityOpened` / `FacilityClosed` | 新工場・拠点の開設 / 閉鎖 | Facility.status 更新 | ValueChainRelation 再評価 |

---

## 2. Investor（投資家）

投資家は企業に資本を配分し，ポートフォリオを管理する主体である．

| イベント名 | トリガー条件 | 主な状態変化 | 副作用（下流） |
|---|---|---|---|
| `InvestmentMade` | 出資・株式取得が完了 | OwnershipHolding 作成，InvestmentTransaction 記録 | CapTableSnapshot 更新，FundingRound 更新 |
| `PositionIncreased` | 持分比率が増加 | OwnershipHolding.ownershipPct 更新 | MonitoringRule の閾値チェック |
| `PositionDecreased` | 持分比率が減少 | OwnershipHolding.ownershipPct 更新 | MonitoringRule の閾値チェック |
| `FullExitMade` | 持分をゼロまで売却 | OwnershipHolding.effectiveTo 設定 | Recommendation ステータス更新 |
| `FundingRoundClosed` | ラウンドのクロージング | FundingRound.status = closed | Company の postMoneyValuation 確定 |
| `ValuationMarkUpdated` | ポートフォリオ評価額の更新 | ValuationOutput 更新 | Scenario の probability 再評価トリガー |

---

## 3. Market（市場）

市場は複数企業・製品が競合する空間であり，外部環境の変化を捉える．

| イベント名 | トリガー条件 | 主な状態変化 | 副作用（下流） |
|---|---|---|---|
| `MarketShareShifted` | シェアの変動が観測された | MarketShareObservation 追加 | CompetitorRelation の rationale 更新トリガー |
| `PricingChanged` | 製品・サービスの価格変動 | PricingObservation 追加 | MetricObservation（粗利率等）の再計算トリガー |
| `MarketEntryDetected` | 新規プレイヤーの参入 | CompetitorRelation 新規作成 | RiskItem（競争リスク）の更新 |
| `MarketExitDetected` | 競合の撤退 | CompetitorRelation の effectiveTo 更新 | MarketShareObservation の再集計 |
| `RegulatoryChangeAnnounced` | 規制当局による規則変更 | RegulatoryEvent 作成 | RiskItem 更新，Hypothesis の falsification チェック |

---

## 4. Financials / Filing（財務・開示）

定期的な財務報告と修正申告がシステムに与えるイベント．

| イベント名 | トリガー条件 | 主な状態変化 | 副作用（下流） |
|---|---|---|---|
| `FilingPublished` | 有価証券報告書・決算短信が公開 | Filing 作成，FinancialStatement / StatementLineItem / ReportedValue 生成 | MetricObservation の再計算トリガー，NormalizedValue 生成 |
| `EarningsSurprise` | 実績が市場コンセンサスを大幅に上回る / 下回る | MetricObservation に valueType = surprise として記録 | Hypothesis のステータス更新，NewsItem 生成 |
| `RestatementIssued` | 過去期財務数値の訂正 | Restatement 作成，対象 ReportedValue に restatement フラグ | DataQualityIssue 生成，NormalizedValue 再計算 |
| `GuidanceIssued` | 会社側の業績予想（ガイダンス）発表 | Guidance 作成 | Scenario の probability 再評価，Hypothesis チェック |
| `GuidanceRevised` | ガイダンスの上方 / 下方修正 | 既存 Guidance を更新，旧値を VersionedRecord に保存 | MonitoringRule の再評価 |
| `AuditOpinionIssued` | 監査意見の確定 | AuditOpinion 作成 | 限定意見・不適正意見の場合 RiskItem 生成 |

---

## 5. Risk / ESG（リスク・ESG）

企業のリスクプロファイルと ESG 評価が変化するイベント．

| イベント名 | トリガー条件 | 主な状態変化 | 副作用（下流） |
|---|---|---|---|
| `RiskIdentified` | 新たなリスクが認識された | RiskItem 作成（status = open） | MonitoringRule の生成トリガー |
| `RiskEscalated` | likelihoodScore または impactScore が閾値を超過 | RiskItem 更新 | Recommendation の action 再評価 |
| `RiskMitigated` | 対策完了によりリスクが低下 | RiskItem.status = mitigated | RiskExposure の再計算 |
| `LitigationFiled` | 訴訟・行政手続きの開始 | LitigationCase 作成 | RiskItem 生成，ESGMetric 更新 |
| `ESGRatingChanged` | ESG 格付けの変更 | ESGMetric 更新 | Investor の投資方針チェック（strategy に ESG 制約がある場合） |

---

## 6. Research / Thesis / Decision（調査・仮説・意思決定）

投資家の意思決定プロセスにおけるイベント．

| イベント名 | トリガー条件 | 主な状態変化 | 副作用（下流） |
|---|---|---|---|
| `ThesisCreated` | 投資仮説の新規作成 | InvestmentThesis 作成（status = draft） | Hypothesis 分解，Scenario 初期化 |
| `HypothesisConfirmed` | 仮説の検証条件が満たされた | Hypothesis.status = confirmed | Thesis の stance 強化，Recommendation 更新 |
| `HypothesisFalsified` | 仮説の棄却条件が成立 | Hypothesis.status = falsified | Thesis の stance 弱化，MonitoringRule 更新 |
| `ScenarioProbabilityUpdated` | シナリオ確率の更新 | Scenario.probability 更新，Assumption 更新 | ValuationModel 再計算トリガー |
| `ValuationCompleted` | バリュエーションモデルの計算完了 | ValuationOutput 作成 | Recommendation 生成トリガー |
| `RecommendationIssued` | 投資推奨の確定 | Recommendation 作成 | MonitoringRule の起動 |
| `MonitoringTriggered` | トリガー条件を満たすイベントが発生 | MonitoringRule.status = triggered | Recommendation の再検討通知 |

---

## 7. Evidence / Provenance（エビデンス・出典）

RAG（Retrieval-Augmented Generation）パイプラインにおけるイベント．

| イベント名 | トリガー条件 | 主な状態変化 | 副作用（下流） |
|---|---|---|---|
| `DocumentIngested` | 新しいソースドキュメントが取り込まれた | SourceDocument 作成，DocumentChunk 分割 | ExtractionRun のキュー投入 |
| `ClaimsExtracted` | LLM による情報抽出完了 | ExtractedClaim 生成，EvidenceLink 作成 | 対応 Fact / Event / Risk へのリンク付け |
| `DataQualityIssueFound` | クレームの矛盾・低信頼度を検出 | DataQualityIssue 作成 | 人手レビューキューへの投入 |
| `EvidenceLinked` | クレームと既存エンティティの紐付け完了 | EvidenceLink 確定 | MetricObservation / RiskItem の confidence 更新 |
| `SourceObsoleted` | ソースドキュメントが失効（訂正・削除等） | SourceDocument.status = obsolete | 関連 EvidenceLink の信頼度引き下げ |
