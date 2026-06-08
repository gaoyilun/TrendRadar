# coding=utf-8
"""Tests for notification functions in main.py."""

import json
from unittest.mock import patch, MagicMock

import pytest

from main import (
    send_to_feishu,
    send_to_dingtalk,
    send_to_wework,
    send_to_telegram,
    send_to_webhooks,
    CONFIG,
)


def _make_report_data(**overrides):
    """Helper to create report_data dict."""
    data = {
        "stats": [
            {
                "word": "苹果",
                "count": 2,
                "percentage": 50,
                "titles": [
                    {
                        "title": "苹果发布新品",
                        "source_name": "今日头条",
                        "time_display": "10时30分",
                        "count": 1,
                        "ranks": [1],
                        "rank_threshold": 5,
                        "url": "https://example.com",
                        "mobile_url": "",
                        "is_new": False,
                    }
                ],
            }
        ],
        "new_titles": [],
        "failed_ids": [],
        "total_new_count": 0,
    }
    data.update(overrides)
    return data


class TestSendToFeishu:
    """Tests for send_to_feishu function."""

    @patch("main.requests.post")
    def test_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        result = send_to_feishu(
            "https://feishu.webhook.url", report_data, "当日汇总"
        )

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["headers"]["Content-Type"] == "application/json"

    @patch("main.requests.post")
    def test_failure_status_code(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        result = send_to_feishu(
            "https://feishu.webhook.url", report_data, "当日汇总"
        )

        assert result is False

    @patch("main.requests.post")
    def test_exception_handled(self, mock_post):
        mock_post.side_effect = Exception("Connection error")

        report_data = _make_report_data()
        result = send_to_feishu(
            "https://feishu.webhook.url", report_data, "当日汇总"
        )

        assert result is False

    @patch("main.requests.post")
    def test_with_proxy(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        send_to_feishu(
            "https://feishu.webhook.url",
            report_data,
            "当日汇总",
            proxy_url="http://proxy:8080",
        )

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["proxies"] == {
            "http": "http://proxy:8080",
            "https": "http://proxy:8080",
        }

    @patch("main.requests.post")
    def test_with_update_info(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        update_info = {"current_version": "2.0.0", "remote_version": "2.1.0"}
        send_to_feishu(
            "https://feishu.webhook.url",
            report_data,
            "当日汇总",
            update_info=update_info,
        )

        # Should succeed without error
        assert mock_post.called


class TestSendToDingtalk:
    """Tests for send_to_dingtalk function."""

    @patch("main.requests.post")
    def test_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        result = send_to_dingtalk(
            "https://dingtalk.webhook.url", report_data, "当日汇总"
        )

        assert result is True

    @patch("main.requests.post")
    def test_failure_errcode(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 1, "errmsg": "invalid token"}
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        result = send_to_dingtalk(
            "https://dingtalk.webhook.url", report_data, "当日汇总"
        )

        assert result is False

    @patch("main.requests.post")
    def test_exception_handled(self, mock_post):
        mock_post.side_effect = Exception("Timeout")

        report_data = _make_report_data()
        result = send_to_dingtalk(
            "https://dingtalk.webhook.url", report_data, "当日汇总"
        )

        assert result is False


class TestSendToWework:
    """Tests for send_to_wework function."""

    @patch("main.requests.post")
    def test_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        result = send_to_wework(
            "https://wework.webhook.url", report_data, "当日汇总"
        )

        assert result is True

    @patch("main.requests.post")
    def test_exception_handled(self, mock_post):
        mock_post.side_effect = Exception("Network error")

        report_data = _make_report_data()
        result = send_to_wework(
            "https://wework.webhook.url", report_data, "当日汇总"
        )

        assert result is False


class TestSendToTelegram:
    """Tests for send_to_telegram function."""

    @patch("main.requests.post")
    def test_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        result = send_to_telegram(
            "bot_token_123", "chat_id_456", report_data, "当日汇总"
        )

        assert result is True

    @patch("main.requests.post")
    def test_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        report_data = _make_report_data()
        result = send_to_telegram(
            "bad_token", "chat_id", report_data, "当日汇总"
        )

        assert result is False

    @patch("main.requests.post")
    def test_exception_handled(self, mock_post):
        mock_post.side_effect = Exception("Telegram unreachable")

        report_data = _make_report_data()
        result = send_to_telegram(
            "token", "chat_id", report_data, "当日汇总"
        )

        assert result is False


class TestSendToWebhooks:
    """Tests for send_to_webhooks function."""

    @patch("main.send_to_feishu")
    @patch("main.send_to_dingtalk")
    @patch("main.send_to_wework")
    @patch("main.send_to_telegram")
    @patch("main.CONFIG", {
        **CONFIG,
        "FEISHU_WEBHOOK_URL": "https://feishu.url",
        "DINGTALK_WEBHOOK_URL": "",
        "WEWORK_WEBHOOK_URL": "",
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_CHAT_ID": "",
        "SILENT_PUSH": {**CONFIG["SILENT_PUSH"], "ENABLED": False},
        "SHOW_VERSION_UPDATE": False,
    })
    def test_sends_only_to_configured_webhooks(
        self, mock_telegram, mock_wework, mock_dingtalk, mock_feishu
    ):
        mock_feishu.return_value = True
        stats = [{"word": "test", "count": 1, "titles": []}]
        results = send_to_webhooks(stats)

        mock_feishu.assert_called_once()
        mock_dingtalk.assert_not_called()
        mock_wework.assert_not_called()
        mock_telegram.assert_not_called()
        assert results["feishu"] is True

    @patch("main.send_to_feishu")
    @patch("main.CONFIG", {
        **CONFIG,
        "FEISHU_WEBHOOK_URL": "",
        "DINGTALK_WEBHOOK_URL": "",
        "WEWORK_WEBHOOK_URL": "",
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_CHAT_ID": "",
        "SILENT_PUSH": {**CONFIG["SILENT_PUSH"], "ENABLED": False},
        "SHOW_VERSION_UPDATE": False,
    })
    def test_no_webhooks_configured(self, mock_feishu):
        stats = []
        results = send_to_webhooks(stats)

        assert results == {}
        mock_feishu.assert_not_called()

    @patch("main.PushRecordManager")
    @patch("main.send_to_feishu")
    @patch("main.CONFIG", {
        **CONFIG,
        "FEISHU_WEBHOOK_URL": "https://feishu.url",
        "DINGTALK_WEBHOOK_URL": "",
        "WEWORK_WEBHOOK_URL": "",
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_CHAT_ID": "",
        "SILENT_PUSH": {
            "ENABLED": True,
            "TIME_RANGE": {"START": "09:00", "END": "18:00"},
            "ONCE_PER_DAY": True,
            "RECORD_RETENTION_DAYS": 7,
        },
        "SHOW_VERSION_UPDATE": False,
    })
    def test_silent_push_outside_time_range(self, mock_feishu, mock_push_mgr):
        mock_instance = MagicMock()
        mock_instance.is_in_time_range.return_value = False
        mock_push_mgr.return_value = mock_instance

        stats = [{"word": "test", "count": 1, "titles": []}]
        results = send_to_webhooks(stats)

        assert results == {}
        mock_feishu.assert_not_called()

    @patch("main.PushRecordManager")
    @patch("main.send_to_feishu")
    @patch("main.CONFIG", {
        **CONFIG,
        "FEISHU_WEBHOOK_URL": "https://feishu.url",
        "DINGTALK_WEBHOOK_URL": "",
        "WEWORK_WEBHOOK_URL": "",
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_CHAT_ID": "",
        "SILENT_PUSH": {
            "ENABLED": True,
            "TIME_RANGE": {"START": "09:00", "END": "18:00"},
            "ONCE_PER_DAY": True,
            "RECORD_RETENTION_DAYS": 7,
        },
        "SHOW_VERSION_UPDATE": False,
    })
    def test_silent_push_already_pushed_today(self, mock_feishu, mock_push_mgr):
        mock_instance = MagicMock()
        mock_instance.is_in_time_range.return_value = True
        mock_instance.has_pushed_today.return_value = True
        mock_push_mgr.return_value = mock_instance

        stats = [{"word": "test", "count": 1, "titles": []}]
        results = send_to_webhooks(stats)

        assert results == {}
        mock_feishu.assert_not_called()
