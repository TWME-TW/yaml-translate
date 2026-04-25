"""
YAML 解析與分段模塊
負責解析 YAML 文件並進行智能分段
"""

import hashlib
from typing import Any, Dict, List, Optional, Tuple
import tiktoken
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO


class YAMLSegment:
    """YAML 段落類"""
    
    def __init__(self, path: str, content: Any, parent: Optional[str] = None):
        """
        初始化段落
        
        Args:
            path: YAML 路徑（如 'root.config.database'）
            content: 內容
            parent: 父節點路徑
        """
        self.path = path
        self.content = content
        self.parent = parent
        self.token_count = 0
        self.translated_content = None
    
    def __repr__(self) -> str:
        return f"YAMLSegment(path='{self.path}', tokens={self.token_count})"


class YAMLParser:
    """YAML 解析器"""
    
    def __init__(self, max_tokens_per_segment: int = 4000, model: str = "gpt-4"):
        """
        初始化解析器
        
        Args:
            max_tokens_per_segment: 每段最大 token 數
            model: 模型名稱（用於 token 計算）
        """
        self.max_tokens = max_tokens_per_segment
        
        # 初始化 tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # 如果模型不存在，使用默認編碼
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def parse(self, yaml_file: str, target_keys: Optional[List[str]] = None) -> List[YAMLSegment]:
        """
        解析 YAML 文件並分段
        
        Args:
            yaml_file: YAML 文件路徑
            target_keys: 指定要翻譯的鍵路徑
            
        Returns:
            List[YAMLSegment]: 段落列表
        """
        # 讀取 YAML 文件
        yaml = YAML()
        yaml.preserve_quotes = True
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.load(f)
        
        # 分段
        segments = []
        self._segment_recursive(data, "root", None, segments, target_keys)
        
        return segments
    
    def _clean_path(self, path: str) -> str:
        if path.startswith("root."):
            return path[5:]
        if path.startswith("root["):
            return path[4:]
        if path == "root":
            return ""
        return path
        
    def _force_split(self, path: str, target_keys: Optional[List[str]]) -> bool:
        if not target_keys:
            return False
        clean_path = self._clean_path(path)
        if clean_path == "":
            return True
        for tk in target_keys:
            if tk.startswith(clean_path + ".") or tk.startswith(clean_path + "["):
                return True
        return False

    def _segment_recursive(
        self, 
        data: Any, 
        path: str, 
        parent: Optional[str],
        segments: List[YAMLSegment],
        target_keys: Optional[List[str]] = None
    ):
        """
        遞迴分段
        
        Args:
            data: 數據
            path: 當前路徑
            parent: 父節點路徑
            segments: 段落列表
            target_keys: 指定要翻譯的鍵路徑
        """
        force_split = self._force_split(path, target_keys)
        
        if isinstance(data, dict):
            # 嘗試將整個字典作為一個段落
            segment = YAMLSegment(path, data, parent)
            segment.token_count = self._estimate_tokens(data)
            
            if not force_split and segment.token_count <= self.max_tokens:
                # 如果 token 數在限制內且不強制分割，添加這個段落
                segments.append(segment)
            else:
                # 遞迴處理每個子項
                for key, value in data.items():
                    child_path = f"{path}.{key}"
                    self._segment_recursive(value, child_path, path, segments, target_keys)
        
        elif isinstance(data, list):
            # 嘗試將整個列表作為一個段落
            segment = YAMLSegment(path, data, parent)
            segment.token_count = self._estimate_tokens(data)
            
            if not force_split and segment.token_count <= self.max_tokens:
                segments.append(segment)
            else:
                # 處理每個列表項
                for i, item in enumerate(data):
                    child_path = f"{path}[{i}]"
                    self._segment_recursive(item, child_path, path, segments, target_keys)
        
        else:
            # 基本類型（字符串、數字等）
            segment = YAMLSegment(path, data, parent)
            segment.token_count = self._estimate_tokens(data)
            segments.append(segment)
    
    def _estimate_tokens(self, data: Any) -> int:
        """
        估算數據的 token 數
        
        Args:
            data: 數據
            
        Returns:
            int: token 數
        """
        # 將數據轉換為字符串
        if isinstance(data, (dict, list)):
            yaml = YAML()
            stream = StringIO()
            yaml.dump(data, stream)
            text = stream.getvalue()
        else:
            text = str(data)
        
        # 計算 token 數
        tokens = self.encoding.encode(text)
        return len(tokens)
    
    def reconstruct_yaml(self, segments: List[YAMLSegment], fallback_to_original: bool = False) -> Dict[str, Any]:
        """
        從翻譯後的段落重建 YAML 結構
        
        Args:
            segments: 段落列表（包含翻譯後的內容）
            fallback_to_original: 若段落未翻譯，是否回退使用原文
            
        Returns:
            Dict[str, Any]: 重建的 YAML 數據
        """
        result = {}
        
        for segment in segments:
            # 決定要使用的內容
            content_to_use = segment.translated_content
            if content_to_use is None and fallback_to_original:
                content_to_use = segment.content
                
            if content_to_use is None:
                continue
            
            # 解析路徑
            path_parts = segment.path.split('.')
            if path_parts[0] == 'root':
                path_parts = path_parts[1:]
            
            # 設置值
            self._set_nested_value(result, path_parts, content_to_use)
        
        return result
    
    def _set_nested_value(self, data: Dict, path_parts: List[str], value: Any):
        """
        設置嵌套值
        
        Args:
            data: 數據字典
            path_parts: 路徑部分列表
            value: 值
        """
        if len(path_parts) == 0:
            return
        
        if len(path_parts) == 1:
            key = path_parts[0]
            # 處理列表索引
            if '[' in key and ']' in key:
                base_key = key[:key.index('[')]
                index = int(key[key.index('[')+1:key.index(']')])
                if base_key not in data:
                    data[base_key] = []
                while len(data[base_key]) <= index:
                    data[base_key].append(None)
                data[base_key][index] = value
            else:
                data[key] = value
        else:
            key = path_parts[0]
            if key not in data:
                data[key] = {}
            self._set_nested_value(data[key], path_parts[1:], value)
    
    def save_yaml(self, data: Dict[str, Any], output_file: str):
        """
        保存 YAML 文件
        
        Args:
            data: YAML 數據
            output_file: 輸出文件路徑
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.indent(mapping=2, sequence=4, offset=2)
            yaml.dump(data, f)
