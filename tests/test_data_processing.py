# coding=utf-8
"""Tests for data processing functions in main.py."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from main import (
    load_frequency_words,
    parse_file_titles,
    matches_word_groups,
    calculate_news_weight,
    process_source_data,
    detect_latest_new_titles,
    save_titles_to_file,
    CONFIG,
)


class TestLoadFrequencyWords:
    """Tests for load_frequency_words function."""

    def test_basic_loading(self, sample_frequency_words_file):
        groups, filter_words = load_frequency_words(sample_frequency_words_file)
        assert len(groups) > 0
        assert isinstance(filter_words, list)

    def test_filter_words_extracted(self, sample_frequency_words_file):
        groups, filter_words = load_frequency_words(sample_frequency_words_file)
        assert "广告" in filter_words
        assert "推广" in filter_words

    def test_required_words_extracted(self, sample_frequency_words_file):
        groups, filter_words = load_frequency_words(sample_frequency_words_file)
        # The group with "+Mate" should have "Mate" as required word
        has_required = any(
            "Mate" in group["required"] for group in groups
        )
        assert has_required

    def test_normal_words_extracted(self, sample_frequency_words_file):
        groups, filter_words = load_frequency_words(sample_frequency_words_file)
        # First group should have normal words like 苹果, iPhone, iOS
        first_group = groups[0]
        assert "苹果" in first_group["normal"]
        assert "iPhone" in first_group["normal"]

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_frequency_words("/nonexistent/path.txt")

    def test_group_key_generated(self, sample_frequency_words_file):
        groups, _ = load_frequency_words(sample_frequency_words_file)
        for group in groups:
            assert "group_key" in group
            assert len(group["group_key"]) > 0

    def test_empty_file(self, tmp_path):
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")
        groups, filter_words = load_frequency_words(str(empty_file))
        assert groups == []
        assert filter_words == []


class TestMatchesWordGroups:
    """Tests for matches_word_groups function."""

    def test_no_word_groups_matches_all(self):
        assert matches_word_groups("any title", [], []) is True

    def test_normal_word_match(self):
        word_groups = [{"required": [], "normal": ["苹果", "iPhone"], "group_key": "苹果"}]
        assert matches_word_groups("苹果发布新品", word_groups, []) is True

    def test_normal_word_no_match(self):
        word_groups = [{"required": [], "normal": ["苹果", "iPhone"], "group_key": "苹果"}]
        assert matches_word_groups("华为发布新品", word_groups, []) is False

    def test_required_word_all_present(self):
        word_groups = [
            {"required": ["AI", "芯片"], "normal": [], "group_key": "AI 芯片"}
        ]
        assert matches_word_groups("AI芯片技术突破", word_groups, []) is True

    def test_required_word_partial_match(self):
        word_groups = [
            {"required": ["AI", "芯片"], "normal": [], "group_key": "AI 芯片"}
        ]
        assert matches_word_groups("AI技术突破", word_groups, []) is False

    def test_filter_word_blocks(self):
        word_groups = [{"required": [], "normal": ["苹果"], "group_key": "苹果"}]
        filter_words = ["广告"]
        assert matches_word_groups("苹果广告投放", word_groups, filter_words) is False

    def test_filter_word_case_insensitive(self):
        word_groups = [{"required": [], "normal": ["AI"], "group_key": "AI"}]
        filter_words = ["spam"]
        assert matches_word_groups("AI SPAM detection", word_groups, filter_words) is False

    def test_case_insensitive_matching(self):
        word_groups = [{"required": [], "normal": ["iPhone"], "group_key": "iPhone"}]
        assert matches_word_groups("新款iphone发布", word_groups, []) is True

    def test_multiple_groups_any_match(self):
        word_groups = [
            {"required": [], "normal": ["苹果"], "group_key": "苹果"},
            {"required": [], "normal": ["华为"], "group_key": "华为"},
        ]
        assert matches_word_groups("华为鸿蒙更新", word_groups, []) is True

    def test_required_and_normal_combined(self):
        word_groups = [
            {"required": ["Mate"], "normal": ["华为", "鸿蒙"], "group_key": "华为"}
        ]
        # Has required word "Mate" but needs normal word too
        assert matches_word_groups("华为Mate60发布", word_groups, []) is True

    def test_required_without_normal(self):
        word_groups = [
            {"required": ["Mate"], "normal": ["华为", "鸿蒙"], "group_key": "华为"}
        ]
        # Has required but no normal word
        assert matches_word_groups("Mate桌垫推荐", word_groups, []) is False


class TestCalculateNewsWeight:
    """Tests for calculate_news_weight function."""

    def test_empty_ranks(self):
        title_data = {"ranks": [], "count": 0}
        assert calculate_news_weight(title_data) == 0.0

    def test_high_rank_high_weight(self):
        title_data = {"ranks": [1], "count": 1}
        weight = calculate_news_weight(title_data)
        assert weight > 0

    def test_low_rank_lower_weight(self):
        high_rank_data = {"ranks": [1], "count": 1}
        low_rank_data = {"ranks": [10], "count": 1}
        assert calculate_news_weight(high_rank_data) > calculate_news_weight(
            low_rank_data
        )

    def test_more_appearances_higher_weight(self):
        single = {"ranks": [3], "count": 1}
        multiple = {"ranks": [3, 3, 3], "count": 3}
        assert calculate_news_weight(multiple) > calculate_news_weight(single)

    def test_rank_capped_at_10(self):
        data_11 = {"ranks": [11], "count": 1}
        data_20 = {"ranks": [20], "count": 1}
        # Both should have same rank weight since capped at 10
        assert calculate_news_weight(data_11) == calculate_news_weight(data_20)

    def test_weight_is_float(self):
        title_data = {"ranks": [1, 2, 3], "count": 3}
        assert isinstance(calculate_news_weight(title_data), float)


class TestParseFileTitles:
    """Tests for parse_file_titles function."""

    def test_basic_parsing(self, sample_titles_file):
        titles_by_id, id_to_name = parse_file_titles(sample_titles_file)
        assert "toutiao" in titles_by_id
        assert "baidu" in titles_by_id
        assert id_to_name["toutiao"] == "今日头条"
        assert id_to_name["baidu"] == "百度热搜"

    def test_title_extraction(self, sample_titles_file):
        titles_by_id, _ = parse_file_titles(sample_titles_file)
        toutiao_titles = titles_by_id["toutiao"]
        assert "苹果发布新iPhone" in toutiao_titles
        assert "华为鸿蒙系统更新" in toutiao_titles

    def test_rank_extraction(self, sample_titles_file):
        titles_by_id, _ = parse_file_titles(sample_titles_file)
        toutiao_titles = titles_by_id["toutiao"]
        assert toutiao_titles["苹果发布新iPhone"]["ranks"] == [1]
        assert toutiao_titles["华为鸿蒙系统更新"]["ranks"] == [2]

    def test_url_extraction(self, sample_titles_file):
        titles_by_id, _ = parse_file_titles(sample_titles_file)
        toutiao_titles = titles_by_id["toutiao"]
        assert toutiao_titles["苹果发布新iPhone"]["url"] == "https://example.com/1"
        assert (
            toutiao_titles["苹果发布新iPhone"]["mobileUrl"]
            == "https://m.example.com/1"
        )

    def test_id_without_name(self, tmp_path):
        content = """toutiao
1. 测试标题 [URL:https://example.com]
"""
        f = tmp_path / "test.txt"
        f.write_text(content, encoding="utf-8")
        titles_by_id, id_to_name = parse_file_titles(f)
        assert id_to_name["toutiao"] == "toutiao"

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        titles_by_id, id_to_name = parse_file_titles(f)
        assert titles_by_id == {}
        assert id_to_name == {}

    def test_failed_ids_section_skipped(self, tmp_path):
        content = """toutiao | 今日头条
1. 正常标题

==== 以下ID请求失败 ====
baidu
"""
        f = tmp_path / "test.txt"
        f.write_text(content, encoding="utf-8")
        titles_by_id, id_to_name = parse_file_titles(f)
        assert "toutiao" in titles_by_id
        # The failed section should not be parsed as data
        assert "baidu" not in titles_by_id


class TestProcessSourceData:
    """Tests for process_source_data function."""

    def test_new_source_added(self):
        all_results = {}
        title_info = {}
        title_data = {
            "测试标题": {"ranks": [1], "url": "https://example.com", "mobileUrl": ""}
        }
        process_source_data("toutiao", title_data, "10时30分", all_results, title_info)

        assert "toutiao" in all_results
        assert "测试标题" in all_results["toutiao"]
        assert title_info["toutiao"]["测试标题"]["first_time"] == "10时30分"
        assert title_info["toutiao"]["测试标题"]["count"] == 1

    def test_existing_source_merged(self):
        all_results = {
            "toutiao": {
                "测试标题": {"ranks": [1], "url": "https://example.com", "mobileUrl": ""}
            }
        }
        title_info = {
            "toutiao": {
                "测试标题": {
                    "first_time": "10时30分",
                    "last_time": "10时30分",
                    "count": 1,
                    "ranks": [1],
                    "url": "https://example.com",
                    "mobileUrl": "",
                }
            }
        }
        title_data = {
            "测试标题": {"ranks": [2], "url": "", "mobileUrl": ""},
            "新标题": {"ranks": [3], "url": "https://new.com", "mobileUrl": ""},
        }
        process_source_data("toutiao", title_data, "11时00分", all_results, title_info)

        # Existing title should have merged ranks
        assert 2 in all_results["toutiao"]["测试标题"]["ranks"]
        assert title_info["toutiao"]["测试标题"]["count"] == 2
        assert title_info["toutiao"]["测试标题"]["last_time"] == "11时00分"

        # New title should be added
        assert "新标题" in all_results["toutiao"]
        assert title_info["toutiao"]["新标题"]["count"] == 1

    def test_duplicate_ranks_not_duplicated(self):
        all_results = {
            "toutiao": {"测试标题": {"ranks": [1, 2], "url": "", "mobileUrl": ""}}
        }
        title_info = {
            "toutiao": {
                "测试标题": {
                    "first_time": "10时30分",
                    "last_time": "10时30分",
                    "count": 1,
                    "ranks": [1, 2],
                    "url": "",
                    "mobileUrl": "",
                }
            }
        }
        title_data = {"测试标题": {"ranks": [1, 3], "url": "", "mobileUrl": ""}}
        process_source_data("toutiao", title_data, "11时00分", all_results, title_info)

        ranks = all_results["toutiao"]["测试标题"]["ranks"]
        assert ranks.count(1) == 1  # No duplicate
        assert 3 in ranks


class TestSaveTitlesToFile:
    """Tests for save_titles_to_file function."""

    @patch("main.get_output_path")
    def test_basic_save(self, mock_get_path, tmp_path):
        output_file = str(tmp_path / "output.txt")
        mock_get_path.return_value = output_file

        results = {
            "toutiao": {
                "标题1": {"ranks": [1], "url": "https://example.com", "mobileUrl": ""},
                "标题2": {"ranks": [2], "url": "", "mobileUrl": ""},
            }
        }
        id_to_name = {"toutiao": "今日头条"}
        failed_ids = ["baidu"]

        path = save_titles_to_file(results, id_to_name, failed_ids)
        assert path == output_file

        content = Path(output_file).read_text(encoding="utf-8")
        assert "toutiao | 今日头条" in content
        assert "标题1" in content
        assert "[URL:https://example.com]" in content
        assert "==== 以下ID请求失败 ====" in content
        assert "baidu" in content

    @patch("main.get_output_path")
    def test_sorted_by_rank(self, mock_get_path, tmp_path):
        output_file = str(tmp_path / "output.txt")
        mock_get_path.return_value = output_file

        results = {
            "toutiao": {
                "低排名": {"ranks": [5], "url": "", "mobileUrl": ""},
                "高排名": {"ranks": [1], "url": "", "mobileUrl": ""},
            }
        }
        id_to_name = {"toutiao": "toutiao"}
        save_titles_to_file(results, id_to_name, [])

        content = Path(output_file).read_text(encoding="utf-8")
        # Higher rank (lower number) should appear first
        pos_high = content.index("高排名")
        pos_low = content.index("低排名")
        assert pos_high < pos_low
