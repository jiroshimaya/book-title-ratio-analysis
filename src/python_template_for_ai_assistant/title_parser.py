"""「aはbがc割」形式のタイトルパーサー

書籍タイトルから「aはbがc割」の形式でa、b、cを抽出する。
cは割の桁数（1-10）として返される（例: 9割 -> 9、10割 -> 10）
"""

import re
from typing import Optional


# 漢数字の変換マップ（一桁のみ、10は漢数字として扱わない）
_KANJI_NUM = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9
}

# 「aはbがc割」パターン
# c割の部分は半角数字1-10または漢数字一-九を許可
# 後ろに余分な文字列が続くことを許容する
_PATTERN = re.compile(
    r'(?P<a>.+?)は(?P<b>.+?)が(?P<c>(?:10|[1-9])\s*割|[一二三四五六七八九]割)',
    re.MULTILINE
)


def parse_ratio_title(title: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """「aはbがc割」形式のタイトルからa、b、cを抽出する
    
    Args:
        title: パースするタイトル文字列
        
    Returns:
        (a, b, c)のタプル。aはタイトルの主語、bは述語、cは割の桁数（1-10）
        パースできない場合は(None, None, None)を返す
        
    Examples:
        >>> parse_ratio_title("人は見た目が9割")
        ('人', '見た目', 9)
        
        >>> parse_ratio_title("人は見た目が九割")
        ('人', '見た目', 9)
        
        >>> parse_ratio_title("人の見た目は9割")  # パターンにマッチしない
        (None, None, None)
    """
    if not title:
        return None, None, None
    
    # コロン（全角・半角）で分割
    segments = re.split(r'[：:]', title)
    
    # 後ろのセグメントから優先的に検査
    for segment in reversed(segments):
        # 前後の空白を除去
        segment = segment.strip()
        
        # パターンにマッチするか試す（複数マッチする場合は最後のマッチを使う）
        matches = list(_PATTERN.finditer(segment))
        if not matches:
            continue
        
        # 最後のマッチを使用
        match = matches[-1]
            
        a = match.group("a").strip()
        b = match.group("b").strip()
        c_raw = match.group("c")
        
        # aから括弧類を削除
        a = _remove_brackets(a)
        
        # aから連体修飾句を除去（漫画で〜る、まんがで〜る など）
        a = _remove_modifier_phrases(a)
        
        # bから括弧類を削除
        b = _remove_brackets(b)
        
        # bの先頭から句読点を除去
        b = b.lstrip('、。，．,.')
        
        # c_rawから数値を抽出
        c_value = _extract_c_value(c_raw)
        if c_value is None:
            continue
        
        return a, b, c_value
    
    return None, None, None


def _remove_modifier_phrases(text: str) -> str:
    """テキストから連体修飾句を除去する
    
    「漫画で分かる」「まんがでわかる」のような、後ろの文全体を修飾する句を除去する。
    「日本も世界も」のような並列句も除去する。
    
    Args:
        text: 処理するテキスト
        
    Returns:
        連体修飾句を削除したテキスト
    """
    # 「漫画で〜る」「まんがで〜る」のようなパターンを除去
    text = re.sub(r'^(漫画|まんが)で.+?る', '', text)
    
    # 「〜も〜も」のような並列句を除去（複数の「も」がある場合）
    # 例: 「日本も世界もマスコミ」→「マスコミ」
    text = re.sub(r'^.+?も.+?も', '', text)
    
    return text.strip()


def _remove_brackets(text: str) -> str:
    """テキストから括弧類を削除する
    
    Args:
        text: 処理するテキスト
        
    Returns:
        括弧を削除したテキスト
    """
    # 「」『』【】()（）などを削除
    text = re.sub(r'[「」『』【】()（）\[\]]', '', text)
    # ダブルクォート・シングルクォートを削除
    text = re.sub(r'["\']', '', text)
    return text


def _extract_c_value(c_raw: str) -> Optional[int]:
    """「9割」や「九割」、「10割」から割の桁数を抽出する
    
    Args:
        c_raw: 「9割」や「九割」、「10割」などの文字列（空白を含む可能性あり）
        
    Returns:
        割の桁数（1-10）。抽出できない場合はNone
    """
    # 半角数字パターン（10および1-9）
    m = re.search(r'(10|[1-9])\s*割', c_raw)
    if m:
        return int(m.group(1))
    
    # 漢数字パターン（一-九のみ）
    m = re.search(r'([一二三四五六七八九])割', c_raw)
    if m:
        return _KANJI_NUM[m.group(1)]
    
    return None
