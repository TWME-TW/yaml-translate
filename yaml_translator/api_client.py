"""
OpenAI API 客戶端模塊
負責與 OpenAI 格式的 API 進行通訊
"""

import requests
import json
from typing import Optional, Dict, Any
import time


class OpenAIClient:
    """OpenAI API 客戶端"""
    
    def __init__(self, api_url: str, api_key: str, model: str, 
                 custom_prompt: str = "", prompt_template_file: str = "",
                 prompt_rules: list = None):
        """
        初始化客戶端
        
        Args:
            api_url: API 端點 URL
            api_key: API 金鑰
            model: 模型名稱
            custom_prompt: 自定義 prompt 模板
            prompt_template_file: prompt 模板文件路徑
            prompt_rules: 自定義翻譯規則列表
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.custom_prompt = custom_prompt
        self.prompt_template_file = prompt_template_file
        self.prompt_rules = prompt_rules or []
        
        # 確保 URL 格式正確
        if not self.api_url.endswith('/chat/completions'):
            if self.api_url.endswith('/v1'):
                self.api_url += '/chat/completions'
            else:
                self.api_url += '/v1/chat/completions'
        
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        from .config import Config
        cfg = Config()
        self.max_retries = cfg.max_retries
        self.retry_delay = 2  # 秒
    
    def translate(
        self, 
        text: str, 
        target_lang: str,
        memory_context: Optional[str] = None,
        temperature: float = 0.3,
        previous_error: Optional[str] = None
    ) -> str:
        """
        翻譯文本
        
        Args:
            text: 待翻譯文本
            target_lang: 目標語言
            memory_context: 翻譯記憶上下文
            temperature: 溫度參數（0-1，越低越確定）
            previous_error: 先前解析錯誤時的錯誤訊息，用於讓 LLM 修正
            
        Returns:
            str: 翻譯結果
        """
        prompt = self._build_prompt(text, target_lang, memory_context, previous_error)
        
        for attempt in range(self.max_retries):
            try:
                response = self._call_api(prompt, temperature)
                return response
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️  API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    print(f"   Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed to translate after {self.max_retries} attempts: {e}")
    
    def _build_prompt(
        self, 
        text: str, 
        target_lang: str, 
        memory_context: Optional[str],
        previous_error: Optional[str] = None
    ) -> str:
        """
        構建翻譯提示詞
        
        Args:
            text: 待翻譯文本
            target_lang: 目標語言
            memory_context: 記憶上下文
            previous_error: 上次的錯誤訊息（如果有）
            
        Returns:
            str: 提示詞
        """
        # 最終返回前，如果有錯誤訊息，附加在 Prompt 後面
        error_suffix = ""
        if previous_error:
            error_suffix = f"\n\nERROR TO FIX:\nYou previously provided an invalid YAML output that caused the following parse error. Please make sure to provide valid YAML format that strictly follows the structure of the original YAML.\nError message: {previous_error}\n"

        # 如果有自定義 prompt 模板文件，優先使用
        if self.prompt_template_file:
            try:
                with open(self.prompt_template_file, 'r', encoding='utf-8') as f:
                    template = f.read()
                    # 替換變數
                    prompt = template.replace('{target_lang}', target_lang)
                    prompt = prompt.replace('{text}', text)
                    if memory_context:
                        prompt = prompt.replace('{memory_context}', memory_context)
                    else:
                        # 移除記憶上下文相關部分
                        prompt = prompt.replace('{memory_context}', '')
                    return prompt + error_suffix
            except Exception as e:
                print(f"⚠️  Failed to load prompt template file: {e}")
                print("   Using default prompt...")
        
        # 如果有完整自定義 prompt，使用它
        if self.custom_prompt:
            prompt = self.custom_prompt.replace('{target_lang}', target_lang)
            prompt = prompt.replace('{text}', text)
            if memory_context:
                prompt += f"\n\nTRANSLATION MEMORY:\n{memory_context}"
            return prompt + error_suffix
        
        # 默認 prompt（可被 prompt_rules 自定義）
        default_rules = [
            "1. ONLY translate the textual values and any # comments to the target language.",
            "2. DO NOT translate the YAML keys (the keys before the colon).",
            "3. If a value is a date, number, or boolean, preserve it exactly as is.",
            "4. You MUST preserve all structural formatting, spaces, empty lines, and indents exactly as in the original.",
            "5. Provide ONLY the valid translated YAML text without any markdown code wrappers (like ```yaml). No explanations.",
        ]
        
        # 如果有自定義規則，使用自定義規則
        rules = self.prompt_rules if self.prompt_rules else default_rules
        
        prompt_parts = [
            f"You are an expert YAML translator. Your goal is to translate all values and comments in the provided YAML text to {target_lang}.",
            "",
            "IMPORTANT RULES:",
        ]
        prompt_parts.extend(rules)
        
        if memory_context:
            prompt_parts.extend([
                "",
                "TRANSLATION MEMORY (for consistency):",
                memory_context,
                "",
                "Please maintain consistency with the above translations."
            ])
        
        prompt_parts.extend([
            "",
            "TEXT TO TRANSLATE:",
            text
        ])
        
        return '\n'.join(prompt_parts) + error_suffix
    
    def _call_api(self, prompt: str, temperature: float = 0.3) -> str:
        """
        呼叫 API
        
        Args:
            prompt: 提示詞
            temperature: 溫度參數
            
        Returns:
            str: API 回應的翻譯結果
        """
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': temperature
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # 提取回應內容
            if 'choices' in result and len(result['choices']) > 0:
                translated = result['choices'][0]['message']['content'].strip()
                return translated
            else:
                raise Exception(f"Unexpected API response format: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 數（簡單估算）
        
        Args:
            text: 文本
            
        Returns:
            int: 估算的 token 數
        """
        # 簡單估算：英文約 4 個字符一個 token，中文約 1.5 個字符一個 token
        # 這裡使用平均值
        return len(text) // 3
    
    def test_connection(self) -> bool:
        """
        測試 API 連接
        
        Returns:
            bool: 連接是否成功
        """
        try:
            # 發送一個簡單的測試請求
            test_text = "Hello"
            result = self.translate(test_text, "zh-TW")
            return bool(result)
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"OpenAIClient(url='{self.api_url}', model='{self.model}')"
