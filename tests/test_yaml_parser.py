"""
Tests for YAMLParser module
"""

import os
import pytest
from yaml_translator.yaml_parser import YAMLParser, YAMLSegment


def test_yaml_segment_initialization():
    """測試段落初始化"""
    segment = YAMLSegment("root.key", "value", "root")
    assert segment.path == "root.key"
    assert segment.content == "value"
    assert segment.parent == "root"
    assert segment.token_count == 0


def test_parser_initialization():
    """測試解析器初始化"""
    parser = YAMLParser(max_tokens_per_segment=100)
    assert parser.max_tokens == 100


def test_estimate_tokens():
    """測試 token 估算"""
    parser = YAMLParser()
    tokens = parser._estimate_tokens("Hello world")
    assert tokens > 0
    
    dict_tokens = parser._estimate_tokens({"key": "value"})
    assert dict_tokens > 0


def test_reconstruct_yaml():
    """測試 YAML 重建"""
    parser = YAMLParser()
    
    seg1 = YAMLSegment("root.app.name", "Old App")
    seg1.translated_content = "New App"
    
    seg2 = YAMLSegment("root.app.version", "1.0")
    seg2.translated_content = "1.0"
    
    # 測試列表重建
    seg3 = YAMLSegment("root.features[0]", "auth")
    seg3.translated_content = "驗證"
    
    segments = [seg1, seg2, seg3]
    result = parser.reconstruct_yaml(segments)
    
    assert result["app"]["name"] == "New App"
    assert result["app"]["version"] == "1.0"
    assert result["features"][0] == "驗證"
