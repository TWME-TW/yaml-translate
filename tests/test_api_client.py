"""
Tests for APIClient module
"""

import pytest
from unittest.mock import patch, Mock
import requests
from yaml_translator.api_client import OpenAIClient


@pytest.fixture
def mock_client():
    return OpenAIClient("https://api.test.com", "test-key", "gpt-4")


def test_client_initialization(mock_client):
    """測試客戶端初始化"""
    assert mock_client.api_url == "https://api.test.com/v1/chat/completions"
    assert mock_client.api_key == "test-key"
    assert mock_client.model == "gpt-4"


@patch('requests.post')
def test_translate_success(mock_post, mock_client):
    """測試翻譯成功"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "你好"
                }
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    result = mock_client.translate("Hello", "zh-TW")
    assert result == "你好"


@patch('requests.post')
def test_translate_retry(mock_post, mock_client):
    """測試翻譯重試機制"""
    # 前兩次失敗，第三次成功
    mock_success = Mock()
    mock_success.json.return_value = {"choices": [{"message": {"content": "成功"}}]}
    
    mock_post.side_effect = [
        requests.exceptions.RequestException("Timeout"),
        requests.exceptions.RequestException("Connection error"),
        mock_success
    ]
    
    mock_client.retry_delay = 0  # 加速測試
    result = mock_client.translate("Hello", "zh-TW")
    assert result == "成功"
    assert mock_post.call_count == 3
