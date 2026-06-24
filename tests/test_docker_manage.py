# coding=utf-8
"""Tests for docker/manage.py functions."""

import sys
from pathlib import Path

import pytest

# Add docker directory to path for importing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docker"))
from manage import parse_cron_schedule


class TestParseCronSchedule:
    """Tests for parse_cron_schedule function."""

    def test_empty_expression(self):
        assert parse_cron_schedule("") == "未设置"

    def test_not_set(self):
        assert parse_cron_schedule("未设置") == "未设置"

    def test_none_input(self):
        assert parse_cron_schedule(None) == "未设置"

    def test_every_30_minutes(self):
        result = parse_cron_schedule("*/30 * * * *")
        assert "30" in result
        assert "分钟" in result

    def test_daily_at_9(self):
        result = parse_cron_schedule("0 9 * * *")
        assert "9" in result
        assert "00" in result
        assert "每天" in result

    def test_weekly_schedule(self):
        result = parse_cron_schedule("0 9 * * 1")
        assert "周一" in result

    def test_invalid_format_too_few_parts(self):
        result = parse_cron_schedule("*/30 *")
        assert "原始表达式" in result

    def test_every_5_minutes(self):
        result = parse_cron_schedule("*/5 * * * *")
        assert "5" in result
        assert "分钟" in result

    def test_specific_time_daily(self):
        result = parse_cron_schedule("30 14 * * *")
        assert "14" in result
        assert "30" in result
        assert "每天" in result

    def test_complex_expression(self):
        result = parse_cron_schedule("0 9 1 * *")
        # Complex - should contain some info
        assert "执行" in result or "表达式" in result

    def test_every_hour(self):
        result = parse_cron_schedule("0 */2 * * *")
        # Every 2 hours at minute 0
        assert "执行" in result or "表达式" in result
