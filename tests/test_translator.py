"""
Integration tests for YAMLTranslator
"""

import os
import pytest
import yaml
import tempfile
from unittest.mock import patch, MagicMock

from yaml_translator.config import Config
from yaml_translator.translator import YAMLTranslator


@pytest.fixture
def mock_config():
    config = Config()
    config.api_key = "test-key"
    config.api_url = "https://api.test.com"
    config.model = "test-model"
    config.target_language = "zh-TW"
    config.memory_db_path = ":memory:" # 記憶體資料庫，測試完即刪
    return config


@patch('yaml_translator.api_client.OpenAIClient.translate')
def test_full_translation_flow(mock_translate, mock_config):
    """測試完整翻譯流程"""
    # 模擬 API
    mock_translate.side_effect = lambda text, lang, context=None: "測試譯文"
    
    # 創建臨時檔案
    with tempfile.NamedNamedTemporaryFile(suffix='.yaml', delete=False, mode='w', encoding='utf-8') as f:
        yaml.dump({"app": {"name": "Test App"}}, f)
        input_file = f.name
        
    output_file = input_file.replace('.yaml', '_out.yaml')
    
    try:
        # 開始翻譯
        with YAMLTranslator(mock_config) as translator:
            translator.translate_file(input_file, output_file)
            
        # 驗證結果
        assert os.path.exists(output_file)
        with open(output_file, 'r', encoding='utf-8') as f:
            result = yaml.safe_load(f)
            
        assert result["app"]["name"] == "測試譯文"
        
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)
