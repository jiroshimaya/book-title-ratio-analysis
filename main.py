import re
import sys
import time
import math
import html
import os
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from urllib.parse import quote
from python_template_for_ai_assistant.title_parser import parse_ratio_title

# -----------------------------
# 1) 検索語（助詞必須 + 図書のみでノイズ削減）
# -----------------------------
# dpid=iss-ndl-opac で国会図書館蔵書（主に図書）に限定
# 助詞（の/が/は）を必須にしてパターンマッチ精度UP
# NDLサーチは全角・半角数字を正規化するが、漢数字は別扱い
QUERIES = [    
    # 「が」パターン（「aはbがc」形式）- 半角数字
    'title="が1割" AND dpid=iss-ndl-opac',
    'title="が2割" AND dpid=iss-ndl-opac',
    'title="が3割" AND dpid=iss-ndl-opac',
    'title="が4割" AND dpid=iss-ndl-opac',
    'title="が5割" AND dpid=iss-ndl-opac',
    'title="が6割" AND dpid=iss-ndl-opac',
    'title="が7割" AND dpid=iss-ndl-opac',
    'title="が8割" AND dpid=iss-ndl-opac',
    'title="が9割" AND dpid=iss-ndl-opac',
    # 漢数字
    'title="が一割" AND dpid=iss-ndl-opac',
    'title="が二割" AND dpid=iss-ndl-opac',
    'title="が三割" AND dpid=iss-ndl-opac',
    'title="が四割" AND dpid=iss-ndl-opac',
    'title="が五割" AND dpid=iss-ndl-opac',
    'title="が六割" AND dpid=iss-ndl-opac',
    'title="が七割" AND dpid=iss-ndl-opac',
    'title="が八割" AND dpid=iss-ndl-opac',
    'title="が九割" AND dpid=iss-ndl-opac',
]

SRU_ENDPOINT = "https://ndlsearch.ndl.go.jp/api/sru"  # 公式例でもこのエンドポイントが提示されています  [oai_citation:2‡国立国会図書館サーチ（NDLサーチ）](https://ndlsearch.ndl.go.jp/help/api/specifications)

# 控えめに（大量アクセスは注意喚起あり） [oai_citation:3‡国立国会図書館サーチ（NDLサーチ）](https://iss.ndl.go.jp/information/api/)
SLEEP_SEC = 0.25

# -----------------------------
# 2) SRUでタイトルを集める
# -----------------------------
def sru_search(query: str, start_record: int = 1, maximum_records: int = 50) -> str:
    """
    SRU searchRetrieve.
    例では operation=searchRetrieve&maximumRecords=10&query=title="桜" AND from="2018" といった形。 [oai_citation:4‡国立国会図書館サーチ（NDLサーチ）](https://ndlsearch.ndl.go.jp/help/api/specifications)
    """
    params = {
        "operation": "searchRetrieve",
        "query": query,
        "startRecord": start_record,
        "maximumRecords": maximum_records,
    }
    r = requests.get(SRU_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    return r.text

def parse_sru(xml_text: str):
    """
    SRU XMLからタイトル等を抜く（DC-NDLベース）。 [oai_citation:5‡国立国会図書館サーチ（NDLサーチ）](https://ndlsearch.ndl.go.jp/help/api/specifications)
    フィールドはDPにより揺れるので、まずは title と identifier/link だけを堅牢に拾う。
    """
    root = ET.fromstring(xml_text)

    # 名前空間（SRU/DCなど）
    ns = {
        "srw": "http://www.loc.gov/zing/srw/",
    }

    # total件数
    n = root.findtext(".//srw:numberOfRecords", default="0", namespaces=ns)
    total = int(n) if n.isdigit() else 0

    rows = []
    for rec in root.findall(".//srw:record", ns):
        # recordDataの中身を取得（エスケープされたXMLが入っている）
        record_data = rec.findtext(".//srw:recordData", default="", namespaces=ns)
        
        if not record_data:
            continue
            
        # HTMLエスケープを解除
        unescaped = html.unescape(record_data)
        
        # 正規表現でタイトルとidentifierを抽出（名前空間を考慮）
        title_match = re.search(r'<dc:title>(.+?)</dc:title>', unescaped)
        title = title_match.group(1) if title_match else None
        
        # identifierも同様に抽出
        id_match = re.search(r'<dc:identifier>(.+?)</dc:identifier>', unescaped)
        identifier = id_match.group(1) if id_match else None

        if title:  # タイトルがある場合のみ追加
            # &amp; などのエンティティも解除
            title = html.unescape(title)
            rows.append({
                "source": "ndl_sru",
                "title_raw": title,
                "id_or_url": identifier,
            })
    return total, rows

def harvest_ndl(queries, per_page=50, max_pages=20, debug=False):
    all_rows = []
    for i, q in enumerate(queries, 1):
        print(f"  [{i}/{len(queries)}] {q[:30]}...", end=" ", flush=True)
        # 1ページ目で総件数を知る
        xml1 = sru_search(q, start_record=1, maximum_records=per_page)
        
        if debug and i == 1:
            # 最初のクエリの生XMLをファイルに保存
            with open("debug_response.xml", "w", encoding="utf-8") as f:
                f.write(xml1)
            print(f"\n✓ XMLレスポンスを debug_response.xml に保存")
        
        total, rows = parse_sru(xml1)
        
        if debug and i == 1:
            print(f"  パース結果: {len(rows)}件のレコード")
            if len(rows) > 0:
                print(f"  サンプル: {rows[0]}")
        
        all_rows.extend(rows)
        time.sleep(SLEEP_SEC)

        pages = min(max_pages, math.ceil(total / per_page))
        for p in range(2, pages + 1):
            start = (p - 1) * per_page + 1
            xmlp = sru_search(q, start_record=start, maximum_records=per_page)
            _, rows = parse_sru(xmlp)
            all_rows.extend(rows)
            time.sleep(SLEEP_SEC)
        
        print(f"→ {len(rows)}件 (全{total}件中)")

    df = pd.DataFrame(all_rows)
    print(f"  生データ: {len(df)}件")
    
    if len(df) > 0:
        df = df.dropna(subset=["title_raw"])
        print(f"  タイトル有効: {len(df)}件")
        # タイトルで雑に重複除去（後でid等で精緻化してもOK）
        df = df.drop_duplicates(subset=["title_raw"]).reset_index(drop=True)
        print(f"  重複除去後: {len(df)}件")
    
    return df

# -----------------------------
# 3) タイトルから a/b/c を抽出（title_parserを使用）
# -----------------------------

def build_rank(df: pd.DataFrame):
    if len(df) == 0:
        # 空のDataFrameの場合は空の結果を返す
        empty_extracted = pd.DataFrame(columns=["source", "title_raw", "id_or_url", "c_value", "c_type", "a_raw", "b_raw"])
        empty_ranking = pd.DataFrame(columns=["a_raw", "c_sum", "n", "examples"])
        return empty_extracted, empty_ranking
    
    out = df.copy()
    
    # parse_ratio_titleでa, b, cを抽出
    result = out["title_raw"].map(parse_ratio_title)
    out["a_raw"] = result.map(lambda x: x[0])
    out["b_raw"] = result.map(lambda x: x[1])
    out["c_value"] = result.map(lambda x: x[2])
    out["c_type"] = out["c_value"].map(lambda x: "wari" if x is not None else None)
    
    # パターンにマッチするもの（cが取れたもの）のみをフィルタリング
    matched_count = out["c_value"].notna().sum()
    print(f"  パターンマッチ: {matched_count}件 / {len(out)}件")
    out = out[out["c_value"].notna()].reset_index(drop=True)

    # ランキング（aが取れないタイトルもあるので、aがあるものを優先）
    out_ab = out.dropna(subset=["a_raw"]).copy()

    if len(out_ab) == 0:
        # a_rawが取れたものがない場合
        empty_ranking = pd.DataFrame(columns=["a_raw", "c_sum", "n", "examples"])
        return out, empty_ranking

    agg = (out_ab.groupby("a_raw")
           .agg(c_sum=("c_value","sum"),
                n=("c_value","count"))
           .sort_values(["c_sum","n"], ascending=[False, False])
           .reset_index())

    # 検算用の代表タイトル（上位3件）
    examples = (out_ab.groupby("a_raw")["title_raw"]
                .apply(lambda s: " / ".join(list(s.head(3))))
                .reset_index()
                .rename(columns={"title_raw":"examples"}))

    agg = agg.merge(examples, on="a_raw", how="left")
    return out, agg

def main():
    # コマンドライン引数でテストモード判定
    test_mode = "--test" in sys.argv
    debug_mode = "--debug" in sys.argv
    force_fetch = "--force" in sys.argv  # 強制再取得フラグ
    
    # titles_extracted.csvが存在する場合はそれを使用
    if os.path.exists("titles_extracted.csv") and not force_fetch:
        print("📄 既存のtitles_extracted.csvを使用します")
        print("   （再取得する場合は --force オプションを指定してください）")
        extracted = pd.read_csv("titles_extracted.csv", encoding="utf-8-sig")
        print(f"✓ {len(extracted)}件のタイトルを読み込みました")
    else:
        if force_fetch:
            print("🔄 --force オプションにより再取得します")
        
        if test_mode:
            print("🧪 テストモード: 最小サンプルで実行")
            queries = QUERIES[:2]  # 最初の2クエリのみ
            per_page = 10
            max_pages = 1
        else:
            print("📚 本番モード: 全クエリで実行")
            queries = QUERIES
            per_page = 50
            max_pages = 20
        
        print(f"クエリ数: {len(queries)}, ページ/クエリ: {max_pages}, 件数/ページ: {per_page}")
        print("取得開始...")
        
        df_titles = harvest_ndl(queries, per_page=per_page, max_pages=max_pages, debug=debug_mode or test_mode)
        print(f"✓ {len(df_titles)}件のタイトルを取得")
        
        extracted, ranking = build_rank(df_titles)
        extracted.to_csv("titles_extracted.csv", index=False, encoding="utf-8-sig")
        print("✓ titles_extracted.csvを保存しました")
    
    # 既存ファイルを読み込んだ場合もランキングを再計算
    if os.path.exists("titles_extracted.csv") and not force_fetch:
        # extractedから直接ランキングを作成するため、元のDataFrameを再構築
        df_for_ranking = extracted[["source", "title_raw", "id_or_url"]].copy() if "source" in extracted.columns else pd.DataFrame({"source": "ndl_sru", "title_raw": extracted["title_raw"], "id_or_url": extracted.get("id_or_url", None)})
        _, ranking = build_rank(df_for_ranking)

    ranking.to_csv("a_ranking.csv", index=False, encoding="utf-8-sig")

    print("\nSaved:")
    print(" - a_ranking.csv")
    
    if len(ranking) > 0:
        print(f"\nTop 20 (全{len(ranking)}件):")
        print(ranking.head(20).to_string(index=False))
    else:
        print("\n⚠️  ランキングデータなし")
    
    if test_mode:
        print("\n💡 本番実行は: python main.py")

if __name__ == "__main__":
    main()