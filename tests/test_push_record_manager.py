# coding=utf-8
"""Tests for PushRecordManager class in main.py."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytz
import pytest

from main import PushRecordManager, CONFIG


class TestPushRecordManager:
    """Tests for PushRecordManager class."""

    @patch("main.get_beijing_time")
    def test_get_today_record_file(self, mock_time, tmp_path):
        mock_time.return_value = datetime(
            2025, 8, 15, 10, 30, 0, tzinfo=pytz.timezone("Asia/Shanghai")
        )
        with patch.object(PushRecordManager, "__init__", lambda self: None):
            mgr = PushRecordManager()
            mgr.record_dir = tmp_path / ".push_records"
            mgr.record_dir.mkdir(parents=True)

            record_file = mgr.get_today_record_file()
            assert record_file.name == "push_record_20250815.json"

    @patch("main.get_beijing_time")
    def test_has_pushed_today_false(self, mock_time, tmp_path):
        mock_time.return_value = datetime(
            2025, 8, 15, 10, 30, 0, tzinfo=pytz.timezone("Asia/Shanghai")
        )
        with patch.object(PushRecordManager, "__init__", lambda self: None):
            mgr = PushRecordManager()
            mgr.record_dir = tmp_path / ".push_records"
            mgr.record_dir.mkdir(parents=True)

            assert mgr.has_pushed_today() is False

    @patch("main.get_beijing_time")
    def test_has_pushed_today_true(self, mock_time, tmp_path):
        mock_time.return_value = datetime(
            2025, 8, 15, 10, 30, 0, tzinfo=pytz.timezone("Asia/Shanghai")
        )
        with patch.object(PushRecordManager, "__init__", lambda self: None):
            mgr = PushRecordManager()
            mgr.record_dir = tmp_path / ".push_records"
            mgr.record_dir.mkdir(parents=True)

            # Create a push record
            record_file = mgr.record_dir / "push_record_20250815.json"
            record_file.write_text(
                json.dumps({"pushed": True}), encoding="utf-8"
            )

            assert mgr.has_pushed_today() is True

    @patch("main.get_beijing_time")
    def test_record_push(self, mock_time, tmp_path):
        mock_time.return_value = datetime(
            2025, 8, 15, 14, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai")
        )
        with patch.object(PushRecordManager, "__init__", lambda self: None):
            mgr = PushRecordManager()
            mgr.record_dir = tmp_path / ".push_records"
            mgr.record_dir.mkdir(parents=True)

            mgr.record_push("当日汇总")

            record_file = mgr.record_dir / "push_record_20250815.json"
            assert record_file.exists()

            data = json.loads(record_file.read_text(encoding="utf-8"))
            assert data["pushed"] is True
            assert data["report_type"] == "当日汇总"
            assert "push_time" in data

    def test_is_in_time_range_within(self):
        with patch.object(PushRecordManager, "__init__", lambda self: None):
            mgr = PushRecordManager()

            with patch("main.get_beijing_time") as mock_time:
                mock_time.return_value = datetime(
                    2025, 8, 15, 10, 30, 0, tzinfo=pytz.timezone("Asia/Shanghai")
                )
                assert mgr.is_in_time_range("09:00", "18:00") is True

    def test_is_in_time_range_outside(self):
        with patch.object(PushRecordManager, "__init__", lambda self: None):
            mgr = PushRecordManager()

            with patch("main.get_beijing_time") as mock_time:
                mock_time.return_value = datetime(
                    2025, 8, 15, 7, 30, 0, tzinfo=pytz.timezone("Asia/Shanghai")
                )
                assert mgr.is_in_time_range("09:00", "18:00") is False

    def test_is_in_time_range_at_boundary(self):
        with patch.object(PushRecordManager, "__init__", lambda self: None):
            mgr = PushRecordManager()

            with patch("main.get_beijing_time") as mock_time:
                mock_time.return_value = datetime(
                    2025, 8, 15, 9, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai")
                )
                assert mgr.is_in_time_range("09:00", "18:00") is True

    @patch("main.get_beijing_time")
    @patch("main.CONFIG", {**CONFIG, "SILENT_PUSH": {**CONFIG["SILENT_PUSH"], "RECORD_RETENTION_DAYS": 1}})
    def test_cleanup_old_records(self, mock_time, tmp_path):
        mock_time.return_value = datetime(
            2025, 8, 15, 10, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai")
        )
        with patch.object(PushRecordManager, "__init__", lambda self: None):
            mgr = PushRecordManager()
            mgr.record_dir = tmp_path / ".push_records"
            mgr.record_dir.mkdir(parents=True)

            # Create an old record (more than 1 day old)
            old_record = mgr.record_dir / "push_record_20250810.json"
            old_record.write_text(json.dumps({"pushed": True}), encoding="utf-8")

            # Create a recent record
            recent_record = mgr.record_dir / "push_record_20250815.json"
            recent_record.write_text(json.dumps({"pushed": True}), encoding="utf-8")

            mgr.cleanup_old_records()

            assert not old_record.exists()
            assert recent_record.exists()
