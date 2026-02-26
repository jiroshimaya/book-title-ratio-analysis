"""Google Books APIクライアントのテスト"""

from unittest.mock import MagicMock, call, patch

import pytest

from book_title_ratio_analysis.google_books_client import search_books, search_ratio_books, fetch_all_books, BookInfo


class TestSearchBooks:
    def test_正常系_クエリに一致する書籍リストを返す(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "totalItems": 1,
            "items": [
                {
                    "volumeInfo": {
                        "title": "人は見た目が9割",
                        "authors": ["竹内一郎"],
                        "publishedDate": "2005-09",
                        "description": "非言語コミュニケーションの重要性を解説する本",
                        "industryIdentifiers": [
                            {"type": "ISBN_13", "identifier": "9784106100697"}
                        ],
                    }
                }
            ],
        }

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            results = search_books("人は見た目が9割", api_key="test_key")

        assert len(results) == 1
        assert results[0].title == "人は見た目が9割"
        assert results[0].authors == ["竹内一郎"]
        assert results[0].published_date == "2005-09"
        assert results[0].isbn == "9784106100697"
        assert results[0].description == "非言語コミュニケーションの重要性を解説する本"

    def test_正常系_書籍が見つからない場合は空リストを返す(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"totalItems": 0}

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            results = search_books("存在しない書籍タイトルXYZ", api_key="test_key")

        assert results == []

    def test_正常系_著者なしの書籍を扱える(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "totalItems": 1,
            "items": [
                {
                    "volumeInfo": {
                        "title": "著者不明の本",
                    }
                }
            ],
        }

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            results = search_books("著者不明の本", api_key="test_key")

        assert len(results) == 1
        assert results[0].title == "著者不明の本"
        assert results[0].authors == []
        assert results[0].isbn is None
        assert results[0].description is None
        assert results[0].published_date is None

    def test_正常系_api_keyがNoneかつ環境変数未設定ならkeyなしでリクエストできる(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"totalItems": 0}

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get, \
             patch.dict("os.environ", {}, clear=True):
            mock_get.return_value = mock_response
            results = search_books("テスト", api_key=None)

        assert results == []
        call_kwargs = mock_get.call_args
        assert "key" not in call_kwargs.kwargs.get("params", {})

    def test_異常系_HTTPエラー時にraise_for_statusが例外を伝播する(self):
        import requests as req

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.HTTPError("404 Not Found")

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            with pytest.raises(req.HTTPError):
                search_books("テスト", api_key="test_key")

    def test_正常系_max_resultsパラメータがリクエストに含まれる(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"totalItems": 0}

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            search_books("テスト", api_key="test_key", max_results=5)

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["maxResults"] == 5


class TestSearchRatioBooks:
    def test_正常系_intitleが9割クエリで書籍を取得できる(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "totalItems": 2,
            "items": [
                {"volumeInfo": {"title": "人は見た目が9割"}},
                {"volumeInfo": {"title": "話し方が9割"}},
            ],
        }

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            results = search_ratio_books(api_key="test_key")

        assert len(results) == 2
        params = mock_get.call_args.kwargs["params"]
        assert params["q"] == 'intitle:"が9割"'

    def test_正常系_ページネーションで全件取得できる(self):
        def side_effect(url, **kwargs):
            start = kwargs["params"].get("startIndex", 0)
            mock = MagicMock()
            mock.raise_for_status.return_value = None
            if start == 0:
                mock.json.return_value = {
                    "totalItems": 45,
                    "items": [{"volumeInfo": {"title": f"本{i}"}} for i in range(40)],
                }
            else:
                mock.json.return_value = {
                    "totalItems": 45,
                    "items": [{"volumeInfo": {"title": f"本{i}"}} for i in range(40, 45)],
                }
            return mock

        with patch("book_title_ratio_analysis.google_books_client.requests.get", side_effect=side_effect) as mock_get:
            results = search_ratio_books(api_key="test_key")

        assert len(results) == 45
        assert mock_get.call_count == 2
        # 2回目のリクエストにstartIndexが含まれる
        second_call_params = mock_get.call_args_list[1].kwargs["params"]
        assert second_call_params["startIndex"] == 40

    def test_正常系_書籍が見つからない場合は空リストを返す(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"totalItems": 0}

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            results = search_ratio_books(api_key="test_key")

        assert results == []
        assert mock_get.call_count == 1

    def test_異常系_HTTPエラー時にraise_for_statusが例外を伝播する(self):
        import requests as req

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.HTTPError("403 Forbidden")

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            with pytest.raises(req.HTTPError):
                search_ratio_books(api_key="test_key")

    def test_正常系_totalItemsがMAX_RESULTS超でもMAX_RESULTSで打ち切る(self):
        def side_effect(url, **kwargs):
            start = kwargs["params"]["startIndex"]
            mock = MagicMock()
            mock.raise_for_status.return_value = None
            mock.json.return_value = {
                "totalItems": 2000,
                "items": [{"volumeInfo": {"title": f"本{start + i}"}} for i in range(40)],
            }
            return mock

        with patch("book_title_ratio_analysis.google_books_client.requests.get", side_effect=side_effect):
            results = search_ratio_books(api_key="test_key")

        from book_title_ratio_analysis.google_books_client import _MAX_RESULTS
        assert len(results) == _MAX_RESULTS


class TestFetchAllBooks:
    def test_正常系_任意のクエリで書籍を取得できる(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "totalItems": 1,
            "items": [{"volumeInfo": {"title": "人は見た目が9割"}}],
        }

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            results = fetch_all_books('intitle:"が9割"', api_key="test_key")

        assert len(results) == 1
        params = mock_get.call_args.kwargs["params"]
        assert params["q"] == 'intitle:"が9割"'

    def test_正常系_ページネーションで全件取得できる(self):
        def side_effect(url, **kwargs):
            start = kwargs["params"]["startIndex"]
            mock = MagicMock()
            mock.raise_for_status.return_value = None
            if start == 0:
                mock.json.return_value = {
                    "totalItems": 55,
                    "items": [{"volumeInfo": {"title": f"本{i}"}} for i in range(40)],
                }
            else:
                mock.json.return_value = {
                    "totalItems": 55,
                    "items": [{"volumeInfo": {"title": f"本{i}"}} for i in range(40, 55)],
                }
            return mock

        with patch("book_title_ratio_analysis.google_books_client.requests.get", side_effect=side_effect) as mock_get:
            results = fetch_all_books('intitle:"が8割"', api_key="test_key")

        assert len(results) == 55
        assert mock_get.call_count == 2

    def test_正常系_デフォルトのmax_resultsで上限が適用される(self):
        call_count = 0

        def side_effect(url, **kwargs):
            nonlocal call_count
            start = kwargs["params"]["startIndex"]
            mock = MagicMock()
            mock.raise_for_status.return_value = None
            mock.json.return_value = {
                "totalItems": 9999,
                "items": [{"volumeInfo": {"title": f"本{start + i}"}} for i in range(40)],
            }
            call_count += 1
            return mock

        with patch("book_title_ratio_analysis.google_books_client.requests.get", side_effect=side_effect):
            results = fetch_all_books('intitle:"が9割"', api_key="test_key")

        from book_title_ratio_analysis.google_books_client import _MAX_RESULTS
        assert len(results) == _MAX_RESULTS

    def test_正常系_max_resultsパラメータで上限を指定できる(self):
        def side_effect(url, **kwargs):
            start = kwargs["params"]["startIndex"]
            mock = MagicMock()
            mock.raise_for_status.return_value = None
            mock.json.return_value = {
                "totalItems": 9999,
                "items": [{"volumeInfo": {"title": f"本{start + i}"}} for i in range(40)],
            }
            return mock

        with patch("book_title_ratio_analysis.google_books_client.requests.get", side_effect=side_effect):
            results = fetch_all_books('intitle:"が9割"', api_key="test_key", max_results=80)

        assert len(results) == 80

    def test_正常系_書籍が見つからない場合は空リストを返す(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"totalItems": 0}

        with patch("book_title_ratio_analysis.google_books_client.requests.get") as mock_get:
            mock_get.return_value = mock_response
            results = fetch_all_books('intitle:"が1割"', api_key="test_key")

        assert results == []
