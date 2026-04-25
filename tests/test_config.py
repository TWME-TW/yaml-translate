"""
Tests for Config module
"""

import os
import pytest
from yaml_translator.config import Config


def test_config_from_env(monkeypatch):
    """測試從環境變數載入配置"""
    monkeypatch.setenv("API_URL", "https://test.api.com")
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("MODEL", "gpt-4")
    monkeypatch.setenv("TARGET_LANGUAGE", "ja")
    
    config = Config()
    
    assert config.api_url == "https://test.api.com"
    assert config.api_key == "test-key"
    assert config.model == "gpt-4"
    assert config.target_language == "ja"


def test_config_validation():
    """測試配置驗證"""
    config = Config()
    config.api_key = "test-key"
    config.api_url = "https://api.test.com"
    config.model = "gpt-4"
    config.target_language = "zh-TW"
    
    assert config.validate() is True


def test_config_validation_missing_key():
    """測試缺少 API Key 的驗證"""
    config = Config()
    config.api_key = ""
    
    with pytest.raises(ValueError, match="API_KEY is required"):
        config.validate()


def test_config_to_dict():
    """測試配置轉換為字典"""
    config = Config()
    config.api_key = "secret-key"
    
    config_dict = config.to_dict()
    
    # API Key 應該被隱藏
    assert config_dict['api_key'] == '***'
    assert 'api_url' in config_dict
    assert 'model' in config_dict
