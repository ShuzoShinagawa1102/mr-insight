# mr-insight（みえるマン）

EDINET APIを使って、東証上場企業の有価証券報告書（有報）を検索してダウンロードするReactアプリです。

## セットアップ

```bash
cd mr-insight
npm install
```

## 会社辞書（東証上場）

JPXが公開している上場会社一覧（Excel）から辞書JSONを生成します。

```bash
npm run gen:companies
```

生成先: `src/data/tse_companies.json`

## 起動

```bash
npm run dev
```

## ロゴ

左上のロゴはホームボタンです。`mr-insight/public/logo.png` を表示します（未配置時は簡易SVGを表示）。

## 使い方

- EDINET APIキー（サブスクリプションキー）を `.env.local` に設定
- 会社を検索して、右側のダウンロードボタンを押す
- 年度別のステータス（有報があるか）を表示し、ダウンロード（高速）

## 高速化（company×年度→docID インデックス）

EDINETは「日付ごとの提出書類一覧」APIのため、都度探索すると時間がかかります。事前に `docID` の対応表を生成してアプリに同梱すると、年度ステータス表示とダウンロード開始がほぼ即時になります。

```bash
npm run gen:yuhou-index -- --year 2024
```

生成先: `src/data/yuhou_index_2024.json`（年ごとに作成）

複数年度まとめて生成（例）:

```bash
# 2020〜2025 をまとめて生成（既にあるファイルはスキップ）
npm run gen:yuhou-index -- --years 2020-2025

# カンマ区切りの指定もOK
npm run gen:yuhou-index -- --years 2023,2024,2025

# 月日の窓を指定（各年に適用）
npm run gen:yuhou-index -- --years 2015-2025 --fromMD 06-01 --toMD 07-31

# 既存を上書きしたい場合
npm run gen:yuhou-index -- --years 2024-2025 --force
```

## 技術

- React + Vite + TypeScript
- Material UI（DataGrid）
- EDINET API v2（開発時はViteのプロキシ `/edinet` 経由）

## 注意

- EDINET APIは「日付ごとの提出書類一覧」ベースのため、年全体など長い期間での検索は時間がかかります。
- 本番（静的ホスティング）ではCORS/プロキシの用意が必要になる場合があります。
