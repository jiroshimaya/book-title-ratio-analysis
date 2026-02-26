"""Google Books APIクライアント

Google Books APIを使って書籍情報を検索・取得する。
APIキーは環境変数 GOOGLE_API_KEY から読み込むか、引数で渡す。
"""

import os
from dataclasses import dataclass, field
from typing import Optional

import requests

_GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


@dataclass
class BookInfo:
    """Google Books APIから取得した書籍情報"""

    title: str
    authors: list[str] = field(default_factory=list)
    published_date: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None


def search_books(
    query: str,
    api_key: Optional[str] = None,
    max_results: int = 10,
) -> list[BookInfo]:
    """Google Books APIで書籍を検索する

    Args:
        query: 検索クエリ（書籍タイトル, 著者名など）
        api_key: Google API キー。Noneの場合は環境変数 GOOGLE_API_KEY を使用
        max_results: 取得する最大件数（1〜40）

    Returns:
        BookInfoのリスト。見つからない場合は空リスト

    Raises:
        requests.HTTPError: APIがエラーレスポンスを返した場合
    """
    key = api_key if api_key is not None else os.environ.get("GOOGLE_API_KEY")

    params: dict[str, str | int] = {
        "q": query,
        "maxResults": max_results,
    }
    if key:
        params["key"] = key

    response = requests.get(_GOOGLE_BOOKS_API_URL, params=params)
    response.raise_for_status()

    data = response.json()
    items = data.get("items", [])
    return _parse_items(items)


_RATIO_QUERY = 'intitle:"が9割"'
_PAGE_SIZE = 40
_MAX_RESULTS = 300  # Google Books APIの内部上限は1000だが、実際の一クエリ最多取得件数は200程度なので300をデフォルトとする


def fetch_all_books(
    query: str,
    api_key: Optional[str] = None,
    max_results: int = _MAX_RESULTS,
) -> list[BookInfo]:
    """任意のクエリで書籍を全件取得する

    ページネーションを使って全件を収集する。
    Google Books API は startIndex + maxResults が 1000 を超えるとエラーになるため、
    max_results の上限は 1000 まで。

    Args:
        query: 検索クエリ（intitle: 演算子なども使用可）
        api_key: Google API キー。Noneの場合は環境変数 GOOGLE_API_KEY を使用
        max_results: 取得する最大件数（1　1000）。デフォルトは {_MAX_RESULTS}

    Returns:
        BookInfoのリスト（最大 max_results 件）

    Raises:
        requests.HTTPError: APIがエラーレスポンスを返した場合
    """
    key = api_key if api_key is not None else os.environ.get("GOOGLE_API_KEY")
    all_results: list[BookInfo] = []
    start_index = 0

    while True:
        remaining = max_results - start_index
        page_size = min(_PAGE_SIZE, remaining)

        params: dict[str, str | int] = {
            "q": query,
            "maxResults": page_size,
            "startIndex": start_index,
        }
        if key:
            params["key"] = key

        response = requests.get(_GOOGLE_BOOKS_API_URL, params=params)
        response.raise_for_status()

        data = response.json()
        total_items = data.get("totalItems", 0)
        items = data.get("items", [])

        if not items:
            break

        all_results.extend(_parse_items(items))
        start_index += len(items)

        if start_index >= min(total_items, max_results):
            break

    return all_results[:max_results]


def search_ratio_books(
    api_key: Optional[str] = None,
) -> list[BookInfo]:
    """「が9割」タイトルの書籍を全件取得する（最大1000件）

    `intitle:"が9割"` クエリを使い、ページネーションで全件を収集する。

    Args:
        api_key: Google API キー。Noneの場合は環境変数 GOOGLE_API_KEY を使用

    Returns:
        BookInfoのリスト（最大1000件）

    Raises:
        requests.HTTPError: APIがエラーレスポンスを返した場合
    """
    return fetch_all_books(_RATIO_QUERY, api_key=api_key)


def _parse_items(items: list[dict]) -> list[BookInfo]:
    """APIレスポンスのitemsリストをBookInfoリストに変換する"""
    results: list[BookInfo] = []
    for item in items:
        volume_info = item.get("volumeInfo", {})

        isbn = None
        for identifier in volume_info.get("industryIdentifiers", []):
            if identifier.get("type") == "ISBN_13":
                isbn = identifier.get("identifier")
                break
        if isbn is None:
            for identifier in volume_info.get("industryIdentifiers", []):
                if identifier.get("type") == "ISBN_10":
                    isbn = identifier.get("identifier")
                    break

        results.append(
            BookInfo(
                title=volume_info.get("title", ""),
                authors=volume_info.get("authors", []),
                published_date=volume_info.get("publishedDate"),
                description=volume_info.get("description"),
                isbn=isbn,
            )
        )
    return results
