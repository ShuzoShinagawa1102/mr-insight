# Javaプラクティス（概念モデリングの最小サンプル）

このフォルダは `概要説明.md` の内容（抽象化 / 一般化 / 構造化 / Java実装）を、**コンソール出力だけ**で確認できる最小のJavaサンプルです。

## 実行

前提: `javac` と `java` が使えること（JDK 17想定）

推奨（実行ポリシーの影響を受けにくい）:

```bat
.\run.cmd
```

PowerShell実行ポリシーが許可されている場合:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

## 何を見ればよいか

- 抽象化 / 一般化: `Mammal` と `Human/Dog/Cat`
- 構造化: `Company-Employee`（関連）、`Car-Tire`（コンポジション）、`Carpenter->Saw`（依存）
- 実現: `Vehicle` と `CarVehicle/Train`
- 同一性 / 等価性: `Customer`（同一性=ID）、`Money`（等価性=値）
