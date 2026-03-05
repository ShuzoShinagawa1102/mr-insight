# ドメインモデル

## レビュー所見と改善方針

旧モデルは約45クラスを単一の図に詰め込んでいたため，「プロ投資家が稼げる判断をするための構造」が見えにくかった．
以下の観点で整理・削減した（約30クラスに集約）：

| 削減・統合の内容 | 理由 |
|---|---|
| `LegalEntity` を `組織` に吸収 | 法人登記情報は `組織` の属性で十分 |
| `CapTableSnapshot` / `Covenant` を削除 | 持分スナップショットは `持分保有` の基準日で代替；コベナンツは `負債証書` の属性へ |
| `Board` / `Committee` / `CompensationPlan` / `RelatedPartyRelationship` を削除 | ガバナンスは「誰が席に就いているか」だけに絞る |
| `RevenueModel` / `CustomerSegment` / `Channel` / `Facility` / `Supplier` / `ValueChainRelation` を削除 | 事業構造の詳細は運用フェーズで拡張；コアドメインに不要 |
| `MarketShareObservation` / `PricingObservation` を `指標` に統合 | 観測値の種別は `指標名` 属性で区別できる |
| `ReportingPeriod` を `開示書類` の属性へ | 一対一の期間情報はクラス分離不要 |
| `StatementLineItem` / `ReportedValue` / `NormalizedValue` を `財務数値` に統合 | 勘定科目・報告値・正規化値は単一レコードで管理 |
| `MetricDefinition` / `MetricObservation` / `Benchmark` / `BenchmarkValue` を `指標` に統合 | 定義と観測を分ける必要はドメイン層では不要 |
| `Restatement` / `AuditOpinion` / `Transcript` / `NewsItem` を削除 | 開示コンテキストは `コーポレートイベント` と `原典文書` で代替 |
| `ResearchProject` を削除，`投資仮説` に統合 | 調査案件は仮説の集合体であり，独立エンティティ不要 |
| `ValuationModel` / `ValuationOutput` / `Assumption` を `バリュエーション` / `シナリオ` に統合 | 手法・出力・前提を一つのバリュエーションレコードで表現 |
| `RiskExposure` / `RegulatoryEvent` / `LitigationCase` を削除 | リスクの定量値・規制・訴訟は `リスク` 属性と `コーポレートイベント` で代替 |
| `ExtractionRun` / `DataQualityIssue` / `AsOfSnapshot` / `VersionedRecord` を削除 | インフラ・横断関心事はドメインモデルから除外し，実装設計で対応 |

---

## 概念モデル（改訂版）

```mermaid
classDiagram
direction LR

%% =========================
%% コア（主体）
%% =========================
class 組織 {
    +UUID id
    +string 正式名称
    +string 国コード
    +string ステータス
    +date 設立日
    +date 解散日
}
class 企業 {
    +string 企業タイプ
    +bool 上場フラグ
    +string 業種コード
}
class 投資家 {
    +string 投資家タイプ
    +string 投資戦略
    +string 所在国
}
class 人物 {
    +UUID id
    +string 氏名
    +string 国籍
    +date 生年月日
}
class 証券 {
    +UUID id
    +string 証券タイプ
    +string ISIN
    +string ティッカー
    +string 通貨
}
class 上場 {
    +UUID id
    +date 上場日
    +date 上場廃止日
    +string 市場区分
    +string ステータス
}
class 取引所 {
    +UUID id
    +string 名称
    +string MICコード
    +string 国コード
}

組織 <|-- 企業
組織 <|-- 投資家
企業 "1" --> "*" 証券 : 発行
証券 "1" --> "*" 上場 : 上場先
上場 "*" --> "1" 取引所 : 市場
人物 "*" --> "*" 組織 : 関与

%% =========================
%% 所有・資本
%% =========================
class 投資取引 {
    +UUID id
    +date 公表日
    +date クロージング日
    +decimal 金額
    +string 通貨
    +decimal 投資前バリュエーション
    +decimal 投資後バリュエーション
    +string 取引タイプ
}
class 資金調達ラウンド {
    +UUID id
    +string ラウンド区分
    +date 実施日
    +decimal 調達額
    +decimal バリュエーション
    +string 通貨
}
class 持分保有 {
    +UUID id
    +decimal 保有株数
    +decimal 持分比率
    +decimal 議決権比率
    +date 基準日
}
class 負債証書 {
    +UUID id
    +string 負債タイプ
    +decimal 元本
    +decimal 金利
    +date 満期日
    +string 通貨
    +string コベナンツ条件
}

投資家 "1" --> "*" 投資取引 : 実行
投資取引 "*" --> "1" 企業 : 対象
投資取引 "*" --> "*" 証券 : 取得または売却
資金調達ラウンド "1" --> "*" 投資取引 : 含む
投資家 "1" --> "*" 持分保有 : 保有
持分保有 "*" --> "1" 企業 : 発行体
企業 "1" --> "*" 負債証書 : 保有

%% =========================
%% ガバナンス
%% =========================
class 取締役会席 {
    +UUID id
    +string 席タイプ
    +date 就任日
    +date 退任日
}
class 役員 {
    +UUID id
    +string 役職名
    +date 就任日
    +date 退任日
}

企業 "1" --> "*" 取締役会席 : 設置
取締役会席 "*" --> "1" 人物 : 着席
企業 "1" --> "*" 役員 : 任命
役員 "*" --> "1" 人物 : 担当

%% =========================
%% 事業構造
%% =========================
class 事業区分 {
    +UUID id
    +string 名称
    +string 区分タイプ
    +date 開始日
    +date 終了日
}
class 製品サービス {
    +UUID id
    +string 名称
    +string カテゴリ
    +string ライフサイクル
}
class 市場 {
    +UUID id
    +string 名称
    +string 定義
    +string 通貨
}
class 業種分類 {
    +UUID id
    +string 分類体系
    +string コード
    +string ラベル
}
class 競合関係 {
    +UUID id
    +string 関係タイプ
    +string 根拠
    +date 有効開始日
    +date 有効終了日
}

企業 "1" --> "*" 事業区分 : 運営
事業区分 "1" --> "*" 製品サービス : 提供
事業区分 "*" --> "*" 市場 : 参入
企業 "*" --> "*" 業種分類 : 分類
企業 "1" --> "*" 競合関係 : 競合エッジ
競合関係 "*" --> "1" 企業 : 相手先

%% =========================
%% 財務・指標
%% =========================
class 開示書類 {
    +UUID id
    +string 書類タイプ
    +date 公表日
    +string 会計基準
    +string 監査人
    +date 期間開始日
    +date 期間終了日
}
class 財務諸表 {
    +UUID id
    +string 諸表タイプ
    +string 連結区分
}
class 財務数値 {
    +UUID id
    +string 勘定科目コード
    +string ラベル
    +decimal 報告値
    +decimal 正規化値
    +string 通貨
    +int スケール
    +date 観測日
}
class 指標 {
    +UUID id
    +string 指標名
    +string 計算式
    +decimal 値
    +string 単位
    +date 観測日
    +string 値タイプ
}
class 業績予想 {
    +UUID id
    +string 指標名
    +decimal 下限
    +decimal 上限
    +string 単位
    +date 発表日
}
class コーポレートイベント {
    +UUID id
    +string イベントタイプ
    +date 公表日
    +date 効力発生日
    +string ステータス
    +string 概要
}

企業 "1" --> "*" 開示書類 : 提出
開示書類 "1" --> "*" 財務諸表 : 含む
財務諸表 "1" --> "*" 財務数値 : 明細
事業区分 "1" --> "*" 財務諸表 : 区分財務
企業 "1" --> "*" 指標 : 観測
事業区分 "1" --> "*" 指標 : 区分指標
市場 "1" --> "*" 指標 : 市場指標
企業 "1" --> "*" 業績予想 : 発表
企業 "1" --> "*" コーポレートイベント : 発生
コーポレートイベント "*" --> "*" 事業区分 : 影響
コーポレートイベント "*" --> "*" 人物 : 影響

%% =========================
%% リスク・ESG
%% =========================
class リスク {
    +UUID id
    +string カテゴリ
    +string タイトル
    +string 説明
    +int 発生可能性
    +int 影響度
    +string ステータス
}
class ESG指標 {
    +UUID id
    +string 指標名
    +decimal 値
    +string 単位
    +date 基準日
    +string フレームワーク
}

企業 "1" --> "*" リスク : 保有
企業 "1" --> "*" ESG指標 : 報告

%% =========================
%% 分析・意思決定
%% =========================
class 投資仮説 {
    +UUID id
    +string スタンス
    +string 仮説文
    +date 作成日
    +date 更新日
    +string ステータス
}
class 仮説 {
    +UUID id
    +string 命題文
    +string 検証方法
    +string 棄却条件
    +string ステータス
}
class シナリオ {
    +UUID id
    +string シナリオ区分
    +decimal 確率
    +decimal 永続成長率
    +decimal WACC
}
class バリュエーション {
    +UUID id
    +string 手法
    +date バリュエーション日
    +decimal 株式価値
    +decimal 事業価値
    +decimal 目標株価
    +string 通貨
}
class 推奨アクション {
    +UUID id
    +string アクション
    +string 確信度
    +date 発行日
    +string 根拠
}
class 監視ルール {
    +UUID id
    +string トリガー条件
    +string 発動時アクション
    +string ステータス
}

投資仮説 "*" --> "1" 企業 : 対象
投資仮説 "1" --> "*" 仮説 : 分解
投資仮説 "1" --> "*" シナリオ : 評価
シナリオ "1" --> "*" バリュエーション : 産出
投資仮説 "1" --> "*" 推奨アクション : 産出
投資仮説 "1" --> "*" 監視ルール : 監視

%% =========================
%% エビデンス（RAG基盤）
%% =========================
class 原典文書 {
    +UUID id
    +string 文書タイプ
    +string タイトル
    +string URI
    +string 発行元
    +date 公表日
    +string 言語
}
class 文書チャンク {
    +UUID id
    +int チャンク番号
    +string コンテンツハッシュ
    +string 埋め込みモデル
}
class 抽出クレーム {
    +UUID id
    +string クレームタイプ
    +string 主語タイプ
    +string 述語
    +string 目的語文字列
    +decimal 信頼度スコア
    +date 抽出日時
}
class エビデンスリンク {
    +UUID id
    +string 対象タイプ
    +UUID 対象ID
    +string 関係ロール
}

原典文書 "1" --> "*" 文書チャンク : 分割
文書チャンク "1" --> "*" 抽出クレーム : 抽出
抽出クレーム "1" --> "*" エビデンスリンク : リンク

エビデンスリンク "*" --> "0..1" 企業 : 参照
エビデンスリンク "*" --> "0..1" コーポレートイベント : 参照
エビデンスリンク "*" --> "0..1" 財務数値 : 参照
エビデンスリンク "*" --> "0..1" 指標 : 参照
エビデンスリンク "*" --> "0..1" リスク : 参照
エビデンスリンク "*" --> "0..1" 投資仮説 : 参照
エビデンスリンク "*" --> "0..1" 仮説 : 参照
```
