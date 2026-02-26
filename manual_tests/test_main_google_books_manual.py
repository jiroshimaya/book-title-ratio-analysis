"""main_google_books.py の手動テスト（サブプロセス実行）

実際にAPIを叩いて end-to-end で動作確認するスクリプト。
事前に環境変数 GOOGLE_API_KEY を設定してください。

実行方法:
    uv run pytest manual_tests/test_main_google_books_manual.py -v -s
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


class TestMainGoogleBooksScript:
    def test_正常系_testモードで正常終了しCSVとJSONが生成される(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(ROOT / "main_google_books.py"), "--test", "--force"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        print("\n--- stdout ---")
        print(result.stdout)
        if result.stderr:
            print("--- stderr ---")
            print(result.stderr)

        assert result.returncode == 0, f"終了コードが0でない: {result.stderr}"
        assert (ROOT / "local" / "titles_extracted_google.csv").exists()
        assert (ROOT / "local" / "a_ranking_google.csv").exists()
        assert (ROOT / "local" / "a_ranking_google.json").exists()

    def test_正常系_生成されたJSONの構造が正しい(self):
        json_path = ROOT / "local" / "a_ranking_google.json"

        # 先にスクリプトを実行してJSONを生成
        subprocess.run(
            [sys.executable, str(ROOT / "main_google_books.py"), "--test", "--force"],
            cwd=ROOT,
            capture_output=True,
        )

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "rankings" in data
        assert "metadata" in data
        assert "total_titles" in data["metadata"]
        assert "generated_at" in data["metadata"]
        print(f"\ntotal_titles: {data['metadata']['total_titles']}")
        print(f"total_a_categories: {data['metadata']['total_a_categories']}")
        if data["rankings"]:
            print(f"Top a: {data['rankings'][0]['a']} (c_sum={data['rankings'][0]['c_sum']})")
