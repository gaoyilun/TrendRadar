# coding=utf-8
"""Tests for version checking and configuration loading in main.py."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from main import check_version_update, load_config, CONFIG


class TestCheckVersionUpdate:
    """Tests for check_version_update function."""

    @patch("main.requests.get")
    def test_no_update_needed(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "2.2.0"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        need_update, version = check_version_update(
            "2.2.0", "https://example.com/version"
        )
        assert need_update is False
        assert version is None

    @patch("main.requests.get")
    def test_update_available(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "3.0.0"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        need_update, version = check_version_update(
            "2.2.0", "https://example.com/version"
        )
        assert need_update is True
        assert version == "3.0.0"

    @patch("main.requests.get")
    def test_current_newer_than_remote(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "1.0.0"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        need_update, version = check_version_update(
            "2.2.0", "https://example.com/version"
        )
        assert need_update is False
        assert version is None

    @patch("main.requests.get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        need_update, version = check_version_update(
            "2.2.0", "https://example.com/version"
        )
        assert need_update is False
        assert version is None

    @patch("main.requests.get")
    def test_with_proxy(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "2.2.0"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        check_version_update(
            "2.2.0", "https://example.com/version", "http://proxy:8080"
        )

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["proxies"] == {
            "http": "http://proxy:8080",
            "https": "http://proxy:8080",
        }

    @patch("main.requests.get")
    def test_invalid_version_format(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "invalid"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        need_update, version = check_version_update(
            "2.2.0", "https://example.com/version"
        )
        # Invalid version parses to (0,0,0) which is less than (2,2,0),
        # so no update needed
        assert need_update is False

    @patch("main.requests.get")
    def test_minor_version_update(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "2.3.0"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        need_update, version = check_version_update(
            "2.2.0", "https://example.com/version"
        )
        assert need_update is True
        assert version == "2.3.0"

    @patch("main.requests.get")
    def test_patch_version_update(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "2.2.1"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        need_update, version = check_version_update(
            "2.2.0", "https://example.com/version"
        )
        assert need_update is True
        assert version == "2.2.1"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_loads_existing_config(self):
        # This tests the actual config file loading
        config = load_config()
        assert "PLATFORMS" in config
        assert "REPORT_MODE" in config
        assert "RANK_THRESHOLD" in config
        assert isinstance(config["PLATFORMS"], list)
        assert len(config["PLATFORMS"]) > 0

    def test_config_file_not_found(self):
        with patch.dict(os.environ, {"CONFIG_PATH": "/nonexistent/config.yaml"}):
            with pytest.raises(FileNotFoundError):
                load_config()

    def test_env_var_webhook_priority(self):
        with patch.dict(
            os.environ,
            {"FEISHU_WEBHOOK_URL": "https://env-feishu.url"},
        ):
            config = load_config()
            assert config["FEISHU_WEBHOOK_URL"] == "https://env-feishu.url"

    def test_default_values_present(self):
        config = load_config()
        assert "REQUEST_INTERVAL" in config
        assert "MESSAGE_BATCH_SIZE" in config
        assert "WEIGHT_CONFIG" in config
        assert "RANK_WEIGHT" in config["WEIGHT_CONFIG"]
        assert "FREQUENCY_WEIGHT" in config["WEIGHT_CONFIG"]
        assert "HOTNESS_WEIGHT" in config["WEIGHT_CONFIG"]

    def test_silent_push_config(self):
        config = load_config()
        assert "SILENT_PUSH" in config
        assert "ENABLED" in config["SILENT_PUSH"]
        assert "TIME_RANGE" in config["SILENT_PUSH"]
        assert "START" in config["SILENT_PUSH"]["TIME_RANGE"]
        assert "END" in config["SILENT_PUSH"]["TIME_RANGE"]
