# GLOBIS MBA 用語集 抽出ツール v3 (Windows / Python)

目的:
- https://mba.globis.ac.jp/about_mba/glossary/ の「カテゴリーから探す」(9カテゴリ)を対象に
- 全カテゴリ・全ページの「用語名のみ」を取得して `glossary_terms.txt` に 1行1語 で出力します
- カテゴリ横断の重複は 1 回にまとめます

実行手順:
1) `create_venv.bat`
2) `run.bat`

成果物:
- `glossary_terms.txt` : 用語名のみ(1行1語)
- `run.log` : URL / page番号 / 取得件数 / 停止理由 / 失敗理由

ページネーション戦略(止まりにくさ優先):
- page を `なし(=1ページ目) → 1 → 2 → ...` で増やして取得します
- 終了条件:
  - そのページで用語が 0 件になった
  - 前ページと同一内容が返った(無限ループ/末尾付近の崩れ対策)
  - `--max-pages` 到達(暴走防止)

Windows / 企業ネットワークで詰まりやすい点:
- SSL(社内証明書/SSLインスペクション):
  - 推奨: `REQUESTS_CA_BUNDLE` または `SSL_CERT_FILE` を社内CA証明書のパスに設定して実行
  - 最終手段: `run.bat` の python 実行に `--insecure` を追加(検証無効化)
- Proxy:
  - requests は既定で `HTTP_PROXY` / `HTTPS_PROXY` 等を見ます
  - それが原因で失敗する場合は `--no-env-proxy` を使います
- シェル:
  - `run.bat` / `create_venv.bat` は cmd.exe 前提です(Git Bash では文字化け/パス解釈で詰まりやすい)
