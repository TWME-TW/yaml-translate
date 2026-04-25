"""
配置管理模塊
負責讀取和管理配置參數
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
from dotenv import load_dotenv


class Config:
    """配置管理類"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路徑（YAML 格式）
        """
        # 載入環境變數
        load_dotenv()
        
        # 默認配置
        self.api_url = os.getenv("API_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("API_KEY", "")
        self.model = os.getenv("MODEL", "gpt-4")
        self.target_language = os.getenv("TARGET_LANGUAGE", "zh-TW")
        self.max_tokens_per_request = int(os.getenv("MAX_TOKENS_PER_REQUEST", "4000"))
        self.rate_limit_rpm = int(os.getenv("RATE_LIMIT_RPM", "60"))
        self.rate_limit_tpm = int(os.getenv("RATE_LIMIT_TPM", "90000"))
        self.memory_db_path = os.getenv("MEMORY_DB_PATH", "./translation_memory.db")
        
        # Prompt 設定
        self.custom_prompt = os.getenv("CUSTOM_PROMPT", "")
        self.prompt_template_file = os.getenv("PROMPT_TEMPLATE_FILE", "")
        self.prompt_rules = []
        
        # 如果未提供配置路徑，自動檢查當前目錄是否有 config.yaml
        if not config_file and os.path.exists("config.yaml"):
            config_file = "config.yaml"
            
        # 如果提供了配置文件（或自動找到），則覆蓋默認配置
        if config_file:
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """
        從 YAML 配置文件載入配置
        
        Args:
            config_file: 配置文件路徑
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # API 配置
            if 'api' in config_data:
                api_config = config_data['api']
                self.api_url = api_config.get('url', self.api_url)
                self.api_key = api_config.get('key', self.api_key)
                self.model = api_config.get('model', self.model)
            
            # 翻譯設定
            if 'translation' in config_data:
                trans_config = config_data['translation']
                self.target_language = trans_config.get('target_language', self.target_language)
                self.max_tokens_per_request = trans_config.get('max_tokens_per_request', self.max_tokens_per_request)
            
            # 速率限制
            if 'rate_limit' in config_data:
                rate_config = config_data['rate_limit']
                self.rate_limit_rpm = rate_config.get('requests_per_minute', self.rate_limit_rpm)
                self.rate_limit_tpm = rate_config.get('tokens_per_minute', self.rate_limit_tpm)
            
            # 記憶庫設定
            if 'memory' in config_data:
                memory_config = config_data['memory']
                self.memory_db_path = memory_config.get('db_path', self.memory_db_path)
            
            # Prompt 設定
            if 'prompt' in config_data:
                prompt_config = config_data['prompt']
                self.custom_prompt = prompt_config.get('custom_prompt', self.custom_prompt)
                self.prompt_template_file = prompt_config.get('template_file', self.prompt_template_file)
                self.prompt_rules = prompt_config.get('rules', self.prompt_rules)
                
        except Exception as e:
            raise ValueError(f"Failed to load config file: {e}")
    
    def validate(self) -> bool:
        """
        驗證配置是否完整
        
        Returns:
            bool: 配置是否有效
        """
        if not self.api_key:
            raise ValueError("API_KEY is required")
        
        if not self.api_url:
            raise ValueError("API_URL is required")
        
        if not self.model:
            raise ValueError("MODEL is required")
        
        if not self.target_language:
            raise ValueError("TARGET_LANGUAGE is required")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        將配置轉換為字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'api_url': self.api_url,
            'api_key': '***' if self.api_key else '',  # 隱藏 API Key
            'model': self.model,
            'target_language': self.target_language,
            'max_tokens_per_request': self.max_tokens_per_request,
            'rate_limit_rpm': self.rate_limit_rpm,
            'rate_limit_tpm': self.rate_limit_tpm,
            'memory_db_path': self.memory_db_path,
            'custom_prompt': bool(self.custom_prompt),
            'prompt_template_file': self.prompt_template_file,
        }
    
    def __repr__(self) -> str:
        return f"Config({self.to_dict()})"
