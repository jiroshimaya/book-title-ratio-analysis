"""ネットワークグラフ作成機能のテスト"""

import pytest
from book_title_ratio_analysis.network_graph import (
    extract_last_noun,
    aggregate_normalized_data,
)


class TestExtractLastNoun:
    """末尾の名詞抽出関数のテスト"""

    def test_正常系_末尾が名詞の場合(self):
        """末尾が名詞の場合、その名詞のみを返す"""
        assert extract_last_noun("住宅営業") == "営業"
        assert extract_last_noun("初回面談") == "面談"
        assert extract_last_noun("Web選考") == "選考"

    def test_正常系_複数名詞がある場合(self):
        """複数の名詞がある場合、最後の名詞のみを返す"""
        assert extract_last_noun("男性の気持ち") == "気持ち"
        assert extract_last_noun("会社の人") == "人"

    def test_正常系_末尾が名詞でない場合(self):
        """末尾が名詞でない場合、元の文字列をそのまま返す"""
        # 動詞のみ
        assert extract_last_noun("走る") == "走る"
        # 形容詞のみ
        assert extract_last_noun("美しい") == "美しい"

    def test_正常系_単一の名詞(self):
        """単一の名詞の場合、その名詞を返す"""
        assert extract_last_noun("営業") == "営業"
        assert extract_last_noun("会社") == "会社"

    def test_正常系_空文字列(self):
        """空文字列の場合、空文字列を返す"""
        assert extract_last_noun("") == ""

    def test_正常系_記号を含む場合(self):
        """記号を含む場合、適切に処理する"""
        assert extract_last_noun("テキトー") == "テキトー"
        # 「ドM」の場合、末尾の名詞は「M」
        assert extract_last_noun("ドM") == "M"


class TestAggregateNormalizedData:
    """データ正規化・集計関数のテスト"""

    def test_正常系_基本的な集計(self):
        """基本的なデータ集計が正しく行われる"""
        data = [
            {"a_raw": "営業", "b_raw": "準備", "c_value": 9.0},
            {"a_raw": "会社", "b_raw": "人", "c_value": 1.0},
        ]
        result = aggregate_normalized_data(data)
        assert result == {
            ("営業", "準備"): 9.0,
            ("会社", "人"): 1.0,
        }

    def test_正常系_複合語の正規化と集計(self):
        """複合語を正規化して集計する"""
        data = [
            {"a_raw": "住宅営業", "b_raw": "初回面談", "c_value": 9.0},
            {"a_raw": "営業", "b_raw": "面談", "c_value": 5.0},
        ]
        result = aggregate_normalized_data(data)
        # 「住宅営業」→「営業」、「初回面談」→「面談」に正規化されるため、合計される
        assert result == {("営業", "面談"): 14.0}

    def test_正常系_同じaとbは除外(self):
        """正規化後にaとbが同じ場合は除外される"""
        data = [
            {"a_raw": "営業", "b_raw": "営業", "c_value": 9.0},
            {"a_raw": "会社", "b_raw": "人", "c_value": 1.0},
        ]
        result = aggregate_normalized_data(data)
        assert result == {("会社", "人"): 1.0}

    def test_正常系_複数のエッジの合計(self):
        """同じエッジが複数回出現する場合、c_valueが合計される"""
        data = [
            {"a_raw": "営業", "b_raw": "準備", "c_value": 9.0},
            {"a_raw": "営業", "b_raw": "準備", "c_value": 5.0},
            {"a_raw": "会社", "b_raw": "人", "c_value": 1.0},
        ]
        result = aggregate_normalized_data(data)
        assert result == {
            ("営業", "準備"): 14.0,
            ("会社", "人"): 1.0,
        }

    def test_正常系_空のデータ(self):
        """空のデータの場合、空の辞書を返す"""
        data = []
        result = aggregate_normalized_data(data)
        assert result == {}

