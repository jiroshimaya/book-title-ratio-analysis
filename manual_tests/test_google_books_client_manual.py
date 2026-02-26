"""Google Books APIの手動テスト

実際にAPIを叩いて動作確認するスクリプト。
事前に環境変数 GOOGLE_API_KEY を設定してください。

実行方法:
    uv run pytest manual_tests/test_google_books_client_manual.py -v -s
"""

import pytest

from book_title_ratio_analysis.google_books_client import search_books, search_ratio_books


class TestSearchBooksManual:
    def test_正常系_実際のAPIで書籍を検索できる(self):
        results = search_books("人は見た目が9割")

        assert len(results) > 0
        print(f"\n検索結果件数: {len(results)}")
        for book in results[:3]:
            print(f"  タイトル: {book.title}")
            print(f"  著者: {book.authors}")
            print(f"  出版日: {book.published_date}")
            print(f"  ISBN: {book.isbn}")

    def test_正常系_max_resultsで件数を制限できる(self):
        results = search_books("Python", max_results=3)

        assert len(results) <= 3
        print(f"\n検索結果件数: {len(results)}")
        for book in results:
            print(f"  タイトル: {book.title}")


class TestSearchRatioBooksManual:
    def test_正常系_が9割タイトルの書籍を全件取得できる(self):
        results = search_ratio_books()

        assert len(results) > 0
        print(f"\n取得件数: {len(results)}")
        for book in results:
            print(f"  {book.title} / {book.authors} / {book.published_date} / ISBN:{book.isbn}")
