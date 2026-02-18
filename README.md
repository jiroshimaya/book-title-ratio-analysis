# 書籍タイトル割合分析

国立国会図書館サーチAPIを使用して、「〜が〜割」形式のタイトルを持つ書籍を収集・分析するプロジェクトです。

## 📖 概要

このプロジェクトは、書籍タイトルに含まれる「aはbがc割」や「bがc割」といったパターンを分析し、どのような表現が多く使われているかを可視化します。

## 🚀 使い方

### 1. データ収集と分析

```bash
uv run main.py
```

**機能:**
- 国立国会図書館サーチAPIから「〜が〜割」形式のタイトルを持つ書籍を検索
- タイトルから「a」「b」「c（割の数値）」を抽出
- aごとのランキングを作成し、bの内訳も集計

**出力ファイル:**
- `local/titles_extracted.csv` - 抽出したタイトルと解析結果
- `local/a_ranking.csv` - aごとのランキング（CSV形式）
- `local/a_ranking.json` - aごとのランキングとbの内訳（JSON形式）

**オプション:**
- `--test` - テストモード（最小サンプルで実行）
- `--debug` - デバッグモード（XMLレスポンスを保存）
- `--force` - 強制再取得（既存のCSVを無視して再度APIから取得）

**注意:** 既に `local/titles_extracted.csv` が存在する場合、そのデータを使用します。再取得する場合は `--force` オプションを指定してください。

### 2. 円グラフの作成

```bash
uv run create_pie_charts.py
```

**機能:**
- `local/a_ranking.json` から各aごとにbの構成比を示す円グラフを作成

**出力:**
- `local/charts/000_[a名]_pie_chart.png` - aごとの円グラフ（c_sum順）

### 3. ヒストグラムの作成

```bash
uv run create_histogram.py
```

**機能:**
- `local/titles_extracted.csv` からc（割の数値）の分布を示すヒストグラムを作成
- 統計情報（平均値、中央値、分布）を表示

**出力:**
- `local/c_value_histogram.png` - cの値のヒストグラム

## 📊 実行例

```bash
# 1. データ収集（初回のみ、または更新時に --force 付きで実行）
uv run main.py

# 2. 可視化
uv run create_pie_charts.py
uv run create_histogram.py
```

## 📄 ライセンス

このプロジェクトはMITライセンスの下でリリースされています。詳細は[LICENSE](LICENSE)をご覧ください。
