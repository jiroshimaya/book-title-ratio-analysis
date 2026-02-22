"""ネットワークグラフ作成機能"""

from collections import defaultdict

from sudachipy import dictionary, tokenizer


# Sudachi辞書とトークナイザーの初期化
_tokenizer_obj = None


def _get_tokenizer() -> tokenizer.Tokenizer:
    """トークナイザーのシングルトンインスタンスを取得"""
    global _tokenizer_obj
    if _tokenizer_obj is None:
        _tokenizer_obj = dictionary.Dictionary().create()
    return _tokenizer_obj


def extract_last_noun(text: str) -> str:
    """
    文字列から末尾の名詞を抽出する
    
    Args:
        text: 抽出対象の文字列
    
    Returns:
        末尾の名詞、または名詞がない場合は元の文字列
    """
    if not text:
        return text
    
    tok = _get_tokenizer()
    tokens = tok.tokenize(text, tokenizer.Tokenizer.SplitMode.C)
    
    # トークンをリストに変換してから後ろから名詞を探す
    token_list = list(tokens)
    for token in reversed(token_list):
        pos = token.part_of_speech()[0]
        if pos == "名詞":
            return token.surface()
    
    # 名詞が見つからない場合は元の文字列を返す
    return text


def aggregate_normalized_data(data: list[dict]) -> dict[tuple[str, str], float]:
    """
    データを正規化して集計する
    
    Args:
        data: a_raw, b_raw, c_valueを含む辞書のリスト
    
    Returns:
        (正規化されたa, 正規化されたb) -> c_valueの合計 の辞書
        ただし、正規化後にaとbが同じ場合は除外される
    """
    aggregated = defaultdict(float)
    
    for row in data:
        a_normalized = extract_last_noun(row["a_raw"])
        b_normalized = extract_last_noun(row["b_raw"])
        
        # 正規化後にaとbが同じ場合は除外
        if a_normalized == b_normalized:
            continue
        
        aggregated[(a_normalized, b_normalized)] += row["c_value"]
    
    return dict(aggregated)

