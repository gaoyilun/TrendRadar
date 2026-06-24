# coding=utf-8
"""Tests for report formatting functions in main.py."""

from unittest.mock import patch

import pytest

from main import (
    format_title_for_platform,
    prepare_report_data,
    CONFIG,
)


class TestFormatTitleForPlatform:
    """Tests for format_title_for_platform function."""

    def _make_title_data(self, **overrides):
        """Helper to create title_data dict."""
        data = {
            "title": "测试标题",
            "source_name": "今日头条",
            "time_display": "10时30分",
            "count": 1,
            "ranks": [3],
            "rank_threshold": 5,
            "url": "https://example.com",
            "mobile_url": "https://m.example.com",
            "is_new": False,
        }
        data.update(overrides)
        return data

    # --- Feishu ---
    def test_feishu_basic(self):
        data = self._make_title_data()
        result = format_title_for_platform("feishu", data)
        assert "[测试标题]" in result
        assert "今日头条" in result
        assert "m.example.com" in result  # prefers mobile url

    def test_feishu_no_url(self):
        data = self._make_title_data(url="", mobile_url="")
        result = format_title_for_platform("feishu", data)
        assert "测试标题" in result
        assert "](http" not in result  # no link

    def test_feishu_new_title(self):
        data = self._make_title_data(is_new=True)
        result = format_title_for_platform("feishu", data)
        assert "🆕" in result

    def test_feishu_high_rank_highlighted(self):
        data = self._make_title_data(ranks=[2])
        result = format_title_for_platform("feishu", data)
        assert "**" in result  # feishu uses ** for bold

    def test_feishu_low_rank_not_highlighted(self):
        data = self._make_title_data(ranks=[8])
        result = format_title_for_platform("feishu", data)
        assert "[8]" in result

    def test_feishu_count_display(self):
        data = self._make_title_data(count=3)
        result = format_title_for_platform("feishu", data)
        assert "(3次)" in result

    def test_feishu_no_source(self):
        data = self._make_title_data()
        result = format_title_for_platform("feishu", data, show_source=False)
        assert "今日头条" not in result

    # --- DingTalk ---
    def test_dingtalk_basic(self):
        data = self._make_title_data()
        result = format_title_for_platform("dingtalk", data)
        assert "[今日头条]" in result
        assert "[测试标题]" in result

    def test_dingtalk_new_title(self):
        data = self._make_title_data(is_new=True)
        result = format_title_for_platform("dingtalk", data)
        assert "🆕" in result

    def test_dingtalk_time_display(self):
        data = self._make_title_data(time_display="10时30分")
        result = format_title_for_platform("dingtalk", data)
        assert "10时30分" in result

    # --- WeWork ---
    def test_wework_basic(self):
        data = self._make_title_data()
        result = format_title_for_platform("wework", data)
        assert "[今日头条]" in result
        assert "[测试标题]" in result

    def test_wework_new_title(self):
        data = self._make_title_data(is_new=True)
        result = format_title_for_platform("wework", data)
        assert "🆕" in result

    # --- Telegram ---
    def test_telegram_basic(self):
        data = self._make_title_data()
        result = format_title_for_platform("telegram", data)
        assert '<a href="https://m.example.com">' in result
        assert "[今日头条]" in result

    def test_telegram_no_url(self):
        data = self._make_title_data(url="", mobile_url="")
        result = format_title_for_platform("telegram", data)
        assert "测试标题" in result
        assert "<a href" not in result

    def test_telegram_html_escape_with_url(self):
        data = self._make_title_data(
            title="<script>alert('xss')</script>",
            url="https://example.com",
            mobile_url="",
        )
        result = format_title_for_platform("telegram", data)
        # When URL is present, title is wrapped in <a> tag and escaped
        assert "&lt;script&gt;" in result

    def test_telegram_high_rank(self):
        data = self._make_title_data(ranks=[1])
        result = format_title_for_platform("telegram", data)
        assert "<b>" in result

    # --- HTML ---
    def test_html_basic(self):
        data = self._make_title_data()
        result = format_title_for_platform("html", data)
        assert 'class="news-link"' in result
        assert "target=\"_blank\"" in result

    def test_html_no_url(self):
        data = self._make_title_data(url="", mobile_url="")
        result = format_title_for_platform("html", data)
        assert 'class="no-link"' in result

    def test_html_escapes_title(self):
        data = self._make_title_data(title="A & B <C>", url="", mobile_url="")
        result = format_title_for_platform("html", data)
        assert "&amp;" in result
        assert "&lt;" in result

    def test_html_new_title_div(self):
        data = self._make_title_data(is_new=True)
        result = format_title_for_platform("html", data)
        assert "class='new-title'" in result
        assert "🆕" in result

    # --- Unknown platform ---
    def test_unknown_platform_returns_cleaned_title(self):
        data = self._make_title_data()
        result = format_title_for_platform("unknown", data)
        assert result == "测试标题"


class TestPrepareReportData:
    """Tests for prepare_report_data function."""

    def test_empty_stats(self):
        result = prepare_report_data([], None, None, None)
        assert result["stats"] == []
        assert result["new_titles"] == []
        assert result["total_new_count"] == 0

    def test_stats_with_zero_count_filtered(self):
        stats = [
            {"word": "苹果", "count": 0, "titles": [], "percentage": 0},
            {
                "word": "华为",
                "count": 2,
                "percentage": 50,
                "titles": [
                    {
                        "title": "华为新品",
                        "source_name": "百度",
                        "time_display": "10时",
                        "count": 1,
                        "ranks": [1],
                        "rank_threshold": 5,
                        "url": "",
                        "mobileUrl": "",
                        "is_new": False,
                    }
                ],
            },
        ]
        result = prepare_report_data(stats)
        assert len(result["stats"]) == 1
        assert result["stats"][0]["word"] == "华为"

    def test_incremental_mode_hides_new_section(self):
        new_titles = {"toutiao": {"新标题": {"ranks": [1], "url": "", "mobileUrl": ""}}}
        id_to_name = {"toutiao": "今日头条"}
        result = prepare_report_data([], None, new_titles, id_to_name, mode="incremental")
        assert result["new_titles"] == []
        assert result["total_new_count"] == 0

    def test_daily_mode_includes_new_titles(self):
        new_titles = {"toutiao": {"新标题": {"ranks": [1], "url": "", "mobileUrl": ""}}}
        id_to_name = {"toutiao": "今日头条"}

        with patch("main.load_frequency_words", return_value=([], [])):
            result = prepare_report_data(
                [], None, new_titles, id_to_name, mode="daily"
            )
        assert result["total_new_count"] == 1
        assert len(result["new_titles"]) == 1
        assert result["new_titles"][0]["source_name"] == "今日头条"

    def test_failed_ids_preserved(self):
        result = prepare_report_data([], ["baidu", "zhihu"], None, None)
        assert result["failed_ids"] == ["baidu", "zhihu"]
