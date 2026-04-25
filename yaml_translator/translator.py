"""
主翻譯器模塊
協調所有組件完成翻譯任務
"""

from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import re
from typing import Optional
from pathlib import Path
from tqdm import tqdm

from .config import Config
from .yaml_parser import YAMLParser, YAMLSegment
from .api_client import OpenAIClient
from .memory import TranslationMemory
from .rate_limiter import RateLimiter


class YAMLTranslator:
    """YAML 翻譯器"""
    
    def __init__(self, config: Config):
        """
        初始化翻譯器
        
        Args:
            config: 配置對象
        """
        self.config = config
        
        # 驗證配置
        config.validate()
        
        # 初始化組件
        self.parser = YAMLParser(
            max_tokens_per_segment=config.max_tokens_per_request,
            model=config.model
        )
        
        self.api_client = OpenAIClient(
            api_url=config.api_url,
            api_key=config.api_key,
            model=config.model,
            custom_prompt=config.custom_prompt,
            prompt_template_file=config.prompt_template_file,
            prompt_rules=config.prompt_rules
        )
        
        self.memory = TranslationMemory(db_path=config.memory_db_path)
        
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit_rpm,
            tokens_per_minute=config.rate_limit_tpm
        )
        
        print("✅ YAML Translator initialized")
        print(f"   Model: {config.model}")
        print(f"   Target Language: {config.target_language}")
        print(f"   Rate Limits: {config.rate_limit_rpm} RPM, {config.rate_limit_tpm} TPM")
    
    def translate_file(
        self, 
        input_file: str, 
        output_file: str,
        target_language: Optional[str] = None
    ):
        """
        翻譯 YAML 文件
        
        Args:
            input_file: 輸入文件路徑
            output_file: 輸出文件路徑
            target_language: 目標語言（可選，覆蓋配置）
        """
        target_lang = target_language or self.config.target_language
        
        print(f"\n📄 Processing: {input_file}")
        print(f"🎯 Target language: {target_lang}")
        
        # 1. 解析並分段
        print("\n🔍 Parsing and segmenting YAML...")
        segments = self.parser.parse(input_file)
        print(f"   Created {len(segments)} segment(s)")
        
        # 顯示分段統計
        total_tokens = sum(s.token_count for s in segments)
        print(f"   Total tokens: {total_tokens}")
        print(f"   Average tokens per segment: {total_tokens // len(segments) if segments else 0}")
        
        # 2. 翻譯每個段落
        print(f"\n🌍 Translating {len(segments)} segment(s)...")
        print(f"   (Intermediate result will be auto-saved to {output_file} periodically)")
        
        for i, segment in enumerate(tqdm(segments, desc="Translating", unit="segment")):
            self._translate_segment(segment, target_lang)
            
            # 每 5 個 segment 或是處理完所有段落時，即時寫入檔案（提供預覽）
            # 因為部分還沒翻譯到的內容會顯示為原文
            if (i + 1) % 5 == 0 or (i + 1) == len(segments):
                try:
                    temp_result = self.parser.reconstruct_yaml(segments, fallback_to_original=True)
                    self.parser.save_yaml(temp_result, output_file)
                except Exception as e:
                    # 如果預覽寫入失敗，不中斷翻譯進程
                    pass
        
        # 3. 重建最終 YAML 結構（確保完全正確生成且沒有 fallback）
        print("\n🔨 Finalizing YAML structure...")
        result = self.parser.reconstruct_yaml(segments, fallback_to_original=True)
        
        # 4. 保存最終結果
        print(f"💾 Saving final file to: {output_file}")
        self.parser.save_yaml(result, output_file)
        
        print("\n✅ Translation completed!")
        self._print_summary(segments)
    
    def _translate_segment(self, segment: YAMLSegment, target_lang: str):
        """
        翻譯單個段落
        
        Args:
            segment: YAML 段落
            target_lang: 目標語言
        """
        yaml_parser = YAML()
        
        # 將內容轉換為文本
        if isinstance(segment.content, (dict, list)):
            stream = StringIO()
            yaml_parser.dump(segment.content, stream)
            text = stream.getvalue()
        else:
            text = str(segment.content)
        
        # 檢查是否有精確匹配的翻譯
        cached = self.memory.find_exact_match(text, target_lang)
        if cached:
            # 使用緩存的翻譯
            if isinstance(segment.content, (dict, list)):
                try:
                    segment.translated_content = yaml_parser.load(cached)
                except Exception:
                    segment.translated_content = cached
            else:
                segment.translated_content = cached
            return
        
        # 獲取記憶上下文
        memory_context = self.memory.get_memory_context(
            text, 
            target_lang, 
            segment.path
        )
        
        # 等待速率限制
        self.rate_limiter.wait_if_needed(segment.token_count)
        
        max_retries = 2
        last_error_msg = None
        
        for attempt in range(max_retries + 1):
            try:
                # 呼叫 API 翻譯
                translated_text = self.api_client.translate(
                    text, 
                    target_lang, 
                    memory_context,
                    previous_error=last_error_msg
                )
                
                # 記錄請求
                self.rate_limiter.record_request(segment.token_count)
                
                # 解析翻譯結果
                if isinstance(segment.content, (dict, list)):
                    # 移除可能由 LLM 產生的 Markdown Code Block 標籤 (例如 ```yaml)
                    cleaned_text = translated_text.strip()
                    
                    # 尋找是否包含 Markdown Code Block
                    match = re.search(r'```(?:yaml|yml)?\s*(.*?)\s*```', cleaned_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        cleaned_text = match.group(1).strip()
                    else:
                        # 處理只有開頭的 ```yaml 等
                        cleaned_text = re.sub(r'^```[a-zA-Z]*\s*', '', cleaned_text)
                        # 處理只有結尾的 ```
                        cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
                    
                    # 避免內容只有空白或失敗導致 load 回傳 None
                    try:
                        loaded = yaml_parser.load(cleaned_text)
                    except Exception as parse_error:
                        print(f"DEBUG: Parse error -> {parse_error}")
                        raise parse_error
                    
                    if loaded is None:
                        loaded = segment.content
                    segment.translated_content = loaded
                else:
                    segment.translated_content = translated_text
                
                # 存入記憶庫
                self.memory.add_translation(
                    source_text=text,
                    target_text=translated_text,
                    target_lang=target_lang,
                    context_path=segment.path
                )
                
                # 成功則跳出迴圈
                break
                
            except Exception as e:
                import traceback
                print(f"DEBUG EXCEPTION TYPE: {type(e)}")
                last_error_msg = str(e)
                import time
                if attempt < max_retries:
                    print(f"\n⚠️ Error translating segment {segment.path}: {e}. Retrying ({attempt+1}/{max_retries})...")
                    time.sleep(2) # 等待 2 秒後重試
                else:
                    print(f"\n❌ Failed to translate segment {segment.path} after {max_retries + 1} attempts: {e}")
                    # 使用原文作為備用
                    segment.translated_content = segment.content
    
    def _print_summary(self, segments):
        """
        打印翻譯摘要
        
        Args:
            segments: 段落列表
        """
        print("\n" + "="*50)
        print("TRANSLATION SUMMARY")
        print("="*50)
        
        total_segments = len(segments)
        total_tokens = sum(s.token_count for s in segments)
        
        print(f"Total segments: {total_segments}")
        print(f"Total tokens: {total_tokens}")
        
        # 速率限制統計
        rate_stats = self.rate_limiter.get_stats()
        print(f"\nRate Limiter Stats:")
        print(f"  Requests: {rate_stats['requests_in_window']}/{rate_stats['rpm_limit']}")
        print(f"  Tokens: {rate_stats['tokens_in_window']}/{rate_stats['tpm_limit']}")
        
        # 記憶庫統計
        memory_stats = self.memory.get_stats()
        print(f"\nTranslation Memory Stats:")
        print(f"  Total translations: {memory_stats['total_translations']}")
        print(f"  Language pairs: {memory_stats['language_pairs']}")
        
        print("="*50)
    
    def test_connection(self) -> bool:
        """
        測試 API 連接
        
        Returns:
            bool: 連接是否成功
        """
        print("🔌 Testing API connection...")
        return self.api_client.test_connection()
    
    def close(self):
        """關閉翻譯器，釋放資源"""
        self.memory.close()
        print("👋 Translator closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
