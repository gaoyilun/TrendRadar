# coding=utf-8
"""Tests for DataFetcher class in main.py."""

import json
from unittest.mock import patch, MagicMock

import pytest

from main import DataFetcher


class TestDataFetcher:
    """Tests for DataFetcher class."""

    def test_init_no_proxy(self):
        fetcher = DataFetcher()
        assert fetcher.proxy_url is None

    def test_init_with_proxy(self):
        fetcher = DataFetcher("http://proxy:8080")
        assert fetcher.proxy_url == "http://proxy:8080"

    @patch("main.requests.get")
    def test_fetch_data_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {"status": "success", "items": [{"title": "Test", "url": "http://test.com"}]}
        )
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = DataFetcher()
        result, id_value, alias = fetcher.fetch_data("toutiao")

        assert result is not None
        assert id_value == "toutiao"
        assert alias == "toutiao"

    @patch("main.requests.get")
    def test_fetch_data_with_tuple_id(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"status": "success", "items": []})
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = DataFetcher()
        result, id_value, alias = fetcher.fetch_data(("toutiao", "今日头条"))

        assert id_value == "toutiao"
        assert alias == "今日头条"

    @patch("main.requests.get")
    def test_fetch_data_cache_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"status": "cache", "items": []})
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = DataFetcher()
        result, _, _ = fetcher.fetch_data("toutiao")
        assert result is not None

    @patch("main.requests.get")
    @patch("main.time.sleep")
    def test_fetch_data_retry_on_failure(self, mock_sleep, mock_get):
        mock_get.side_effect = Exception("Connection error")

        fetcher = DataFetcher()
        result, id_value, alias = fetcher.fetch_data(
            "toutiao", max_retries=1, min_retry_wait=0, max_retry_wait=0
        )

        assert result is None
        assert id_value == "toutiao"
        # Should have retried
        assert mock_get.call_count == 2  # initial + 1 retry

    @patch("main.requests.get")
    def test_fetch_data_invalid_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"status": "error", "items": []})
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = DataFetcher()
        result, _, _ = fetcher.fetch_data("toutiao", max_retries=0)
        assert result is None

    @patch("main.requests.get")
    @patch("main.time.sleep")
    def test_crawl_websites_success(self, mock_sleep, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "status": "success",
                "items": [
                    {"title": "新闻标题1", "url": "http://url1.com", "mobileUrl": ""},
                    {"title": "新闻标题2", "url": "http://url2.com", "mobileUrl": ""},
                ],
            }
        )
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = DataFetcher()
        results, id_to_name, failed_ids = fetcher.crawl_websites(
            [("toutiao", "今日头条")], request_interval=0
        )

        assert "toutiao" in results
        assert id_to_name["toutiao"] == "今日头条"
        assert failed_ids == []
        assert "新闻标题1" in results["toutiao"]

    @patch("main.requests.get")
    @patch("main.time.sleep")
    def test_crawl_websites_partial_failure(self, mock_sleep, mock_get):
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.text = json.dumps({"status": "success", "items": []})
        success_response.raise_for_status = MagicMock()

        mock_get.side_effect = [
            success_response,
            Exception("Connection error"),
            Exception("Connection error"),
            Exception("Connection error"),
        ]

        fetcher = DataFetcher()
        results, id_to_name, failed_ids = fetcher.crawl_websites(
            ["toutiao", "baidu"], request_interval=0
        )

        assert "toutiao" in results
        assert "baidu" in failed_ids

    @patch("main.requests.get")
    @patch("main.time.sleep")
    def test_crawl_websites_duplicate_titles_merged(self, mock_sleep, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "status": "success",
                "items": [
                    {"title": "重复标题", "url": "http://url1.com", "mobileUrl": ""},
                    {"title": "重复标题", "url": "http://url2.com", "mobileUrl": ""},
                ],
            }
        )
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = DataFetcher()
        results, _, _ = fetcher.crawl_websites(["toutiao"], request_interval=0)

        # Duplicate titles should be merged with multiple ranks
        assert len(results["toutiao"]["重复标题"]["ranks"]) == 2
        assert results["toutiao"]["重复标题"]["ranks"] == [1, 2]

    @patch("main.requests.get")
    def test_fetch_data_with_proxy(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"status": "success", "items": []})
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetcher = DataFetcher("http://proxy:8080")
        fetcher.fetch_data("toutiao")

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["proxies"] == {
            "http": "http://proxy:8080",
            "https": "http://proxy:8080",
        }
