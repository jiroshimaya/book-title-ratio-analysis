"""Google Books APIを使って書籍情報を収集・集計するスクリプト

main.py（NDLサーチ版）のGoogle Books API版。
「が〇割」パターンの書籍タイトルを収集し、a/b/cを抽出してランキングを出力する。

Usage:
    uv run main_google_books.py          # 全クエリで実行
    uv run main_google_books.py --force  # 既存CSVを無視して再取得
    uv run main_google_books.py --test   # 最小サンプルで動作確認
"""

import json
import os
import sys
import time
from datetime import datetime

import pandas as pd

from book_title_ratio_analysis.google_books_client import BookInfo, fetch_all_books
from book_title_ratio_analysis.title_parser import parse_ratio_title

# -----------------------------
# 1) クエリ一覧（intitleフレーズ検索）
# -----------------------------
QUERIES = [
    # 半角数字
    'intitle:"が1割"',
    'intitle:"が2割"',
    'intitle:"が3割"',
    'intitle:"が4割"',
    'intitle:"が5割"',
    'intitle:"が6割"',
    'intitle:"が7割"',
    'intitle:"が8割"',
    'intitle:"が9割"',
    # 漢数字
    'intitle:"が一割"',
    'intitle:"が二割"',
    'intitle:"が三割"',
    'intitle:"が四割"',
    'intitle:"が五割"',
    'intitle:"が六割"',
    'intitle:"が七割"',
    'intitle:"が八割"',
    'intitle:"が九割"',
]

SLEEP_SEC = 0.5
OUTPUT_CSV = "local/titles_extracted_google.csv"
OUTPUT_RANKING_CSV = "local/a_ranking_google.csv"
OUTPUT_RANKING_JSON = "local/a_ranking_google.json"


# -----------------------------
# 2) Google Books APIで書籍を収集
# -----------------------------
def harvest_google_books(
    queries: list[str],
    sleep_sec: float = SLEEP_SEC,
) -> pd.DataFrame:
    """各クエリからBookInfoを収集してDataFrameを返す"""
    all_rows: list[dict] = []

    for i, query in enumerate(queries, 1):
        print(f"  [{i}/{len(queries)}] {query}", end=" ", flush=True)
        books = fetch_all_books(query)
        rows = [
            {
                "source": "google_books",
                "title_raw": book.title,
                "authors": ", ".join(book.authors),
                "published_date": book.published_date,
                "isbn": book.isbn,
            }
            for book in books
        ]
        all_rows.extend(rows)
        print(f"→ {len(rows)}件")
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    df = pd.DataFrame(all_rows) if all_rows else pd.DataFrame(
        columns=["source", "title_raw", "authors", "published_date", "isbn"]
    )
    print(f"  生データ: {len(df)}件")
    return df


# -----------------------------
# 3) タイトルから a/b/c を抽出
# -----------------------------
def build_rank(df: pd.DataFrame):
    if len(df) == 0:
        empty_extracted = pd.DataFrame(
            columns=["source", "title_raw", "c_value", "c_type", "a_raw", "b_raw"]
        )
        empty_ranking = pd.DataFrame(columns=["a_raw", "c_sum", "n", "examples"])
        return empty_extracted, empty_ranking

    out = df.copy()

    # 重複除去
    original_count = len(out)
    out = out.drop_duplicates(subset=["title_raw"]).reset_index(drop=True)
    if len(out) < original_count:
        print(f"  重複除去: {original_count}件 → {len(out)}件")

    result = out["title_raw"].map(parse_ratio_title)
    out["a_raw"] = result.map(lambda x: x[0])
    out["b_raw"] = result.map(lambda x: x[1])
    out["c_value"] = result.map(lambda x: x[2])
    out["c_type"] = out["c_value"].map(lambda x: "wari" if x is not None else None)

    matched_count = out["c_value"].notna().sum()
    print(f"  パターンマッチ: {matched_count}件 / {len(out)}件")
    out = out[out["c_value"].notna()].reset_index(drop=True)

    out_ab = out.dropna(subset=["a_raw"]).copy()
    if len(out_ab) == 0:
        return out, pd.DataFrame(columns=["a_raw", "c_sum", "n", "examples"])

    agg = (
        out_ab.groupby("a_raw")
        .agg(c_sum=("c_value", "sum"), n=("c_value", "count"))
        .sort_values(["c_sum", "n"], ascending=[False, False])
        .reset_index()
    )
    examples = (
        out_ab.groupby("a_raw")["title_raw"]
        .apply(lambda s: " / ".join(list(s.head(3))))
        .reset_index()
        .rename(columns={"title_raw": "examples"})
    )
    agg = agg.merge(examples, on="a_raw", how="left")
    return out, agg


def build_ranking_json(extracted: pd.DataFrame) -> dict:
    if len(extracted) == 0:
        return {
            "rankings": [],
            "metadata": {
                "total_titles": 0,
                "total_a_categories": 0,
                "generated_at": datetime.now().isoformat(),
            },
        }

    df = extracted.dropna(subset=["a_raw", "b_raw", "c_value"]).copy()
    if len(df) == 0:
        return {
            "rankings": [],
            "metadata": {
                "total_titles": len(extracted),
                "total_a_categories": 0,
                "generated_at": datetime.now().isoformat(),
            },
        }

    rankings = []
    for a_val in df.groupby("a_raw")["c_value"].sum().sort_values(ascending=False).index:
        a_df = df[df["a_raw"] == a_val]
        b_breakdown = []
        for b_val in a_df.groupby("b_raw")["c_value"].sum().sort_values(ascending=False).index:
            b_df = a_df[a_df["b_raw"] == b_val]
            b_breakdown.append({
                "b": b_val,
                "c_sum": float(b_df["c_value"].sum()),
                "count": len(b_df),
                "titles": b_df["title_raw"].tolist(),
            })
        rankings.append({
            "a": a_val,
            "c_sum": float(a_df["c_value"].sum()),
            "count": len(a_df),
            "b_breakdown": b_breakdown,
        })

    return {
        "rankings": rankings,
        "metadata": {
            "total_titles": len(extracted),
            "total_a_categories": len(rankings),
            "generated_at": datetime.now().isoformat(),
        },
    }


# -----------------------------
# 4) エントリポイント
# -----------------------------
def main():
    test_mode = "--test" in sys.argv
    force_fetch = "--force" in sys.argv

    os.makedirs("local", exist_ok=True)

    if os.path.exists(OUTPUT_CSV) and not force_fetch:
        print(f"📄 既存の {OUTPUT_CSV} を使用します")
        print("   （再取得する場合は --force オプションを指定してください）")
        extracted = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        print(f"✓ {len(extracted)}件のタイトルを読み込みました")
    else:
        if force_fetch:
            print("🔄 --force オプションにより再取得します")

        queries = QUERIES[:2] if test_mode else QUERIES
        if test_mode:
            print("🧪 テストモード: 最初の2クエリのみ実行")
        else:
            print("📚 本番モード: 全クエリで実行")

        print(f"クエリ数: {len(queries)}")
        print("取得開始...")

        df_titles = harvest_google_books(queries)
        print(f"✓ {len(df_titles)}件のタイトルを取得")

        extracted, _ = build_rank(df_titles)
        extracted.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print(f"✓ {OUTPUT_CSV} を保存しました")

    _, ranking = build_rank(
        extracted[["source", "title_raw"]].copy()
        if "source" in extracted.columns
        else pd.DataFrame({"source": "google_books", "title_raw": extracted["title_raw"]})
    )

    ranking.to_csv(OUTPUT_RANKING_CSV, index=False, encoding="utf-8-sig")

    ranking_json = build_ranking_json(extracted)
    with open(OUTPUT_RANKING_JSON, "w", encoding="utf-8") as f:
        json.dump(ranking_json, f, ensure_ascii=False, indent=2)

    print("\nSaved:")
    print(f" - {OUTPUT_CSV}")
    print(f" - {OUTPUT_RANKING_CSV}")
    print(f" - {OUTPUT_RANKING_JSON}")

    if len(ranking) > 0:
        print(f"\nTop 20 (全{len(ranking)}件):")
        print(ranking.head(20).to_string(index=False))
    else:
        print("\n⚠️  ランキングデータなし")

    if test_mode:
        print("\n💡 本番実行は: uv run main_google_books.py")


if __name__ == "__main__":
    main()
