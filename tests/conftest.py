# coding=utf-8
"""Shared fixtures for TrendRadar tests."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the project root is on sys.path so we can import main
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set CONFIG_PATH to the real config before importing main
os.environ.setdefault("CONFIG_PATH", str(PROJECT_ROOT / "config" / "config.yaml"))


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Provide a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_frequency_words_file(tmp_path):
    """Create a sample frequency_words.txt for testing."""
    content = """苹果
iPhone
iOS

华为
鸿蒙
+Mate

!广告
!推广
"""
    freq_file = tmp_path / "frequency_words.txt"
    freq_file.write_text(content, encoding="utf-8")
    return str(freq_file)


@pytest.fixture
def sample_titles_file(tmp_path):
    """Create a sample titles txt file for testing."""
    content = """toutiao | 今日头条
1. 苹果发布新iPhone [URL:https://example.com/1] [MOBILE:https://m.example.com/1]
2. 华为鸿蒙系统更新 [URL:https://example.com/2]
3. AI技术新突破 [URL:https://example.com/3]

baidu | 百度热搜
1. 苹果iPhone降价 [URL:https://example.com/4]
2. 小米SU7交付 [URL:https://example.com/5]
"""
    titles_file = tmp_path / "10时30分.txt"
    titles_file.write_text(content, encoding="utf-8")
    return titles_file
