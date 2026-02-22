"""
b_rawごとのランキング作成スクリプト
local/titles_extracted.csvからb_rawに対してc_valueの合計を集計し、
b_ranking.csvとb_ranking.jsonを生成します。
"""

import json
from datetime import datetime

import pandas as pd
from sudachipy import tokenizer, dictionary


# Sudachi Tokenizerの初期化（短単位用）
_TOKENIZER_OBJ = dictionary.Dictionary().create()


def extract_last_simple_noun(text: str) -> str:
    """短単位の形態素解析で末尾の単純名詞を抽出する

    Args:
        text: 処理するテキスト

    Returns:
        末尾の単純名詞、または見つからない場合は元のテキスト

    Examples:
        >>> extract_last_simple_noun("高校サッカー")
        "サッカー"
        >>> extract_last_simple_noun("高校野球")
        "野球"
    """
    if not text:
        return text

    # Aモード（短単位）で形態素解析
    morphemes = _TOKENIZER_OBJ.tokenize(text, tokenizer.Tokenizer.SplitMode.A)
    morpheme_list = list(morphemes)

    if not morpheme_list:
        return text

    # 末尾から遡って最初に見つかった名詞を返す
    for morpheme in reversed(morpheme_list):
        if morpheme.part_of_speech()[0] == "名詞":
            return morpheme.surface()

    # 名詞が見つからない場合は元のテキストを返す
    return text


def build_b_ranking_csv(extracted: pd.DataFrame) -> pd.DataFrame:
    """b_rawごとにc_valueの合計とカウントを集計（CSV用）"""
    if len(extracted) == 0:
        return pd.DataFrame(columns=["b_raw", "c_sum", "n", "examples"])

    # b_rawがあるものだけを使用
    df = extracted.dropna(subset=["b_raw", "c_value"]).copy()

    if len(df) == 0:
        return pd.DataFrame(columns=["b_raw", "c_sum", "n", "examples"])

    # b_rawごとに集計
    agg = (
        df.groupby("b_raw")
        .agg(c_sum=("c_value", "sum"), n=("c_value", "count"))
        .sort_values(["c_sum", "n"], ascending=[False, False])
        .reset_index()
    )

    # 代表タイトル（上位3件）
    examples = (
        df.groupby("b_raw")["title_raw"]
        .apply(lambda s: " / ".join(list(s.head(3))))
        .reset_index()
        .rename(columns={"title_raw": "examples"})
    )

    agg = agg.merge(examples, on="b_raw", how="left")
    return agg


def build_b_ranking_json(extracted: pd.DataFrame) -> dict:
    """b_rawごとにa_rawの内訳も含めたランキングJSON（詳細版）"""
    if len(extracted) == 0:
        return {
            "rankings": [],
            "metadata": {
                "total_titles": 0,
                "total_b_categories": 0,
                "generated_at": datetime.now().isoformat(),
            },
        }

    # b_rawとa_rawがあるものだけを使用
    df = extracted.dropna(subset=["b_raw", "a_raw", "c_value"]).copy()

    if len(df) == 0:
        return {
            "rankings": [],
            "metadata": {
                "total_titles": len(extracted),
                "total_b_categories": 0,
                "generated_at": datetime.now().isoformat(),
            },
        }

    # a_rawを正規化（末尾の単純名詞のみを抽出）
    df["a_normalized"] = df["a_raw"].apply(extract_last_simple_noun)

    # bごとに集計
    rankings = []
    for b_val in (
        df.groupby("b_raw")["c_value"].sum().sort_values(ascending=False).index
    ):
        b_df = df[df["b_raw"] == b_val]
        b_c_sum = float(b_df["c_value"].sum())
        b_count = len(b_df)

        # aごとに集計（正規化されたa_normalizedを使用）
        a_breakdown = []
        for a_val in (
            b_df.groupby("a_normalized")["c_value"]
            .sum()
            .sort_values(ascending=False)
            .index
        ):
            a_df = b_df[b_df["a_normalized"] == a_val]
            a_c_sum = float(a_df["c_value"].sum())
            a_count = len(a_df)
            titles = a_df["title_raw"].tolist()

            a_breakdown.append(
                {"a": a_val, "c_sum": a_c_sum, "count": a_count, "titles": titles}
            )

        rankings.append(
            {"b": b_val, "c_sum": b_c_sum, "count": b_count, "a_breakdown": a_breakdown}
        )

    return {
        "rankings": rankings,
        "metadata": {
            "total_titles": len(extracted),
            "total_b_categories": len(rankings),
            "generated_at": datetime.now().isoformat(),
        },
    }


def main():
    """メイン処理"""
    print("📊 b_ranking作成スクリプト")
    print("=" * 60)

    # titles_extracted.csvを読み込み
    csv_path = "local/titles_extracted.csv"
    try:
        extracted = pd.read_csv(csv_path, encoding="utf-8-sig")
        print(f"✓ {len(extracted)}件のタイトルを読み込みました")
    except FileNotFoundError:
        print(f"❌ {csv_path} が見つかりません")
        return

    # CSV形式のランキングを作成
    b_ranking_csv = build_b_ranking_csv(extracted)
    csv_output = "local/b_ranking.csv"
    b_ranking_csv.to_csv(csv_output, index=False, encoding="utf-8-sig")
    print(f"✓ {csv_output} を保存しました")

    # JSON形式のランキングを作成
    b_ranking_json = build_b_ranking_json(extracted)
    json_output = "local/b_ranking.json"
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(b_ranking_json, f, ensure_ascii=False, indent=2)
    print(f"✓ {json_output} を保存しました")

    # プレビュー表示
    if len(b_ranking_csv) > 0:
        print(f"\n📈 Top 20 (全{len(b_ranking_csv)}件):")
        print(b_ranking_csv.head(20).to_string(index=False))
    else:
        print("\n⚠️  ランキングデータなし")

    print("\n✨ 完了!")


if __name__ == "__main__":
    main()
