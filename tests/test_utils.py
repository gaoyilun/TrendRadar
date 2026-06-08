# coding=utf-8
"""Tests for utility functions in main.py."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from main import (
    clean_title,
    ensure_directory_exists,
    html_escape,
    format_time_display,
    format_rank_display,
    get_beijing_time,
    format_date_folder,
    format_time_filename,
    is_first_crawl_today,
)


class TestCleanTitle:
    """Tests for clean_title function."""

    def test_basic_string(self):
        assert clean_title("Hello World") == "Hello World"

    def test_newlines_replaced(self):
        assert clean_title("Hello\nWorld") == "Hello World"

    def test_carriage_return_replaced(self):
        assert clean_title("Hello\rWorld") == "Hello World"

    def test_mixed_whitespace_collapsed(self):
        assert clean_title("Hello   \n  \r  World") == "Hello World"

    def test_leading_trailing_stripped(self):
        assert clean_title("  Hello World  ") == "Hello World"

    def test_non_string_input(self):
        assert clean_title(12345) == "12345"

    def test_none_input(self):
        assert clean_title(None) == "None"

    def test_empty_string(self):
        assert clean_title("") == ""

    def test_tabs_collapsed(self):
        assert clean_title("Hello\t\tWorld") == "Hello World"


class TestHtmlEscape:
    """Tests for html_escape function."""

    def test_ampersand(self):
        assert html_escape("a & b") == "a &amp; b"

    def test_less_than(self):
        assert html_escape("a < b") == "a &lt; b"

    def test_greater_than(self):
        assert html_escape("a > b") == "a &gt; b"

    def test_double_quote(self):
        assert html_escape('a "b" c') == "a &quot;b&quot; c"

    def test_single_quote(self):
        assert html_escape("a 'b' c") == "a &#x27;b&#x27; c"

    def test_combined_special_chars(self):
        result = html_escape('<script>alert("xss")</script>')
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result

    def test_non_string_input(self):
        assert html_escape(123) == "123"

    def test_empty_string(self):
        assert html_escape("") == ""

    def test_no_special_chars(self):
        assert html_escape("Hello World") == "Hello World"


class TestFormatTimeDisplay:
    """Tests for format_time_display function."""

    def test_same_first_and_last_time(self):
        assert format_time_display("10时30分", "10时30分") == "10时30分"

    def test_different_times(self):
        assert format_time_display("10时30分", "14时00分") == "[10时30分 ~ 14时00分]"

    def test_empty_first_time(self):
        assert format_time_display("", "14时00分") == ""

    def test_empty_last_time(self):
        assert format_time_display("10时30分", "") == "10时30分"

    def test_both_empty(self):
        assert format_time_display("", "") == ""


class TestFormatRankDisplay:
    """Tests for format_rank_display function."""

    def test_empty_ranks(self):
        assert format_rank_display([], 5, "feishu") == ""

    def test_single_high_rank_feishu(self):
        result = format_rank_display([3], 5, "feishu")
        assert "**" in result
        assert "[3]" in result

    def test_single_low_rank_feishu(self):
        result = format_rank_display([7], 5, "feishu")
        assert "**" not in result
        assert "[7]" in result

    def test_range_high_rank_feishu(self):
        result = format_rank_display([2, 5, 8], 5, "feishu")
        assert "[2 - 8]" in result
        assert "**" in result

    def test_range_low_rank_feishu(self):
        result = format_rank_display([6, 8, 10], 5, "feishu")
        assert "[6 - 10]" in result
        assert "**" not in result

    def test_html_format_high_rank(self):
        result = format_rank_display([1], 5, "html")
        assert "<strong>" in result
        assert "[1]" in result

    def test_dingtalk_format(self):
        result = format_rank_display([3], 5, "dingtalk")
        assert "**[3]**" in result

    def test_wework_format(self):
        result = format_rank_display([3], 5, "wework")
        assert "**[3]**" in result

    def test_telegram_format_high_rank(self):
        result = format_rank_display([2], 5, "telegram")
        assert "<b>[2]</b>" in result

    def test_duplicate_ranks_deduplicated(self):
        result = format_rank_display([3, 3, 3], 5, "feishu")
        assert "[3]" in result
        # Should not show range since all same
        assert "~" not in result


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists function."""

    def test_creates_directory(self, tmp_path):
        new_dir = str(tmp_path / "new" / "nested" / "dir")
        ensure_directory_exists(new_dir)
        assert Path(new_dir).exists()

    def test_existing_directory_no_error(self, tmp_path):
        ensure_directory_exists(str(tmp_path))
        assert tmp_path.exists()


class TestGetBeijingTime:
    """Tests for get_beijing_time function."""

    def test_returns_datetime(self):
        result = get_beijing_time()
        assert result.tzinfo is not None
        assert "Asia/Shanghai" in str(result.tzinfo)


class TestFormatDateFolder:
    """Tests for format_date_folder function."""

    @patch("main.get_beijing_time")
    def test_format(self, mock_time):
        from datetime import datetime
        import pytz

        mock_time.return_value = datetime(
            2025, 8, 15, 10, 30, 0, tzinfo=pytz.timezone("Asia/Shanghai")
        )
        result = format_date_folder()
        assert result == "2025年08月15日"


class TestFormatTimeFilename:
    """Tests for format_time_filename function."""

    @patch("main.get_beijing_time")
    def test_format(self, mock_time):
        from datetime import datetime
        import pytz

        mock_time.return_value = datetime(
            2025, 8, 15, 10, 30, 0, tzinfo=pytz.timezone("Asia/Shanghai")
        )
        result = format_time_filename()
        assert result == "10时30分"


class TestIsFirstCrawlToday:
    """Tests for is_first_crawl_today function."""

    @patch("main.format_date_folder")
    def test_no_directory_returns_true(self, mock_folder, tmp_path):
        mock_folder.return_value = "2025年08月15日"
        with patch("main.Path") as mock_path_cls:
            mock_txt_dir = tmp_path / "output" / "2025年08月15日" / "txt"
            # Don't create the dir so it doesn't exist
            mock_path_cls.return_value.__truediv__ = lambda *a: mock_txt_dir
            # Use actual function with non-existent path
            result = is_first_crawl_today()
            assert result is True
