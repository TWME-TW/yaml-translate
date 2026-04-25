"""
翻譯記憶庫模塊
維護翻譯歷史和一致性
"""

import sqlite3
import threading
from typing import List, Optional, Tuple
from datetime import datetime
import difflib


class TranslationMemory:
    """翻譯記憶庫"""
    
    def __init__(self, db_path: str = "./translation_memory.db"):
        """
        初始化記憶庫
        
        Args:
            db_path: 資料庫文件路徑
        """
        self.db_path = db_path
        self.conn = None
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """初始化資料庫"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # 創建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT NOT NULL,
                target_text TEXT NOT NULL,
                source_lang TEXT DEFAULT 'en',
                target_lang TEXT NOT NULL,
                context_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 創建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source_target 
            ON translations(source_text, target_lang)
        ''')
        
        self.conn.commit()
    
    def add_translation(
        self, 
        source_text: str, 
        target_text: str,
        target_lang: str,
        source_lang: str = 'en',
        context_path: Optional[str] = None
    ):
        """
        添加翻譯記錄
        
        Args:
            source_text: 原文
            target_text: 譯文
            target_lang: 目標語言
            source_lang: 源語言
            context_path: YAML 路徑上下文
        """
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO translations 
                (source_text, target_text, source_lang, target_lang, context_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (source_text, target_text, source_lang, target_lang, context_path))
            
            self.conn.commit()
    
    def find_exact_match(
        self, 
        source_text: str, 
        target_lang: str,
        source_lang: str = 'en'
    ) -> Optional[str]:
        """
        查找精確匹配的翻譯
        
        Args:
            source_text: 原文
            target_lang: 目標語言
            source_lang: 源語言
            
        Returns:
            Optional[str]: 譯文（如果找到）
        """
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT target_text FROM translations
                WHERE source_text = ? AND target_lang = ? AND source_lang = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (source_text, target_lang, source_lang))
            
            result = cursor.fetchone()
        return result[0] if result else None
    
    def find_similar_translations(
        self, 
        source_text: str, 
        target_lang: str,
        source_lang: str = 'en',
        threshold: float = 0.8,
        limit: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        查找相似的翻譯
        
        Args:
            source_text: 原文
            target_lang: 目標語言
            source_lang: 源語言
            threshold: 相似度閾值（0-1）
            limit: 最大返回數量
            
        Returns:
            List[Tuple[str, str, float]]: 
                [(source, target, similarity), ...]
        """
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT DISTINCT source_text, target_text FROM translations
                WHERE target_lang = ? AND source_lang = ?
                ORDER BY created_at DESC
                LIMIT 100
            ''', (target_lang, source_lang))
            
            results = cursor.fetchall()
        
        # 計算相似度
        similar = []
        for source, target in results:
            similarity = difflib.SequenceMatcher(None, source_text, source).ratio()
            if similarity >= threshold:
                similar.append((source, target, similarity))
        
        # 按相似度排序
        similar.sort(key=lambda x: x[2], reverse=True)
        
        return similar[:limit]
    
    def get_context_translations(
        self, 
        context_path: str, 
        target_lang: str,
        limit: int = 10
    ) -> List[Tuple[str, str]]:
        """
        獲取相同上下文的翻譯
        
        Args:
            context_path: YAML 路徑
            target_lang: 目標語言
            limit: 最大返回數量
            
        Returns:
            List[Tuple[str, str]]: [(source, target), ...]
        """
        cursor = self.conn.cursor()
        
        # 查找相同路徑或父路徑的翻譯
        path_pattern = f"{context_path}%"
        cursor.execute('''
            SELECT source_text, target_text FROM translations
            WHERE context_path LIKE ? AND target_lang = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (path_pattern, target_lang, limit))
        
        return cursor.fetchall()
    
    def get_memory_context(
        self,
        source_text: str,
        target_lang: str,
        context_path: Optional[str] = None,
        source_lang: str = 'en'
    ) -> str:
        """
        獲取記憶上下文（用於 AI 提示）
        
        Args:
            source_text: 原文
            target_lang: 目標語言
            context_path: YAML 路徑
            source_lang: 源語言
            
        Returns:
            str: 上下文字符串
        """
        context_parts = []
        
        # 1. 精確匹配
        exact = self.find_exact_match(source_text, target_lang, source_lang)
        if exact:
            context_parts.append(f"Previous exact translation: '{source_text}' -> '{exact}'")
        
        # 2. 相似翻譯
        similar = self.find_similar_translations(source_text, target_lang, source_lang)
        if similar:
            context_parts.append("\nSimilar translations:")
            for src, tgt, sim in similar[:3]:
                context_parts.append(f"- '{src}' -> '{tgt}' (similarity: {sim:.2f})")
        
        # 3. 上下文翻譯
        if context_path:
            ctx_trans = self.get_context_translations(context_path, target_lang)
            if ctx_trans:
                context_parts.append(f"\nTranslations from same context ({context_path}):")
                for src, tgt in ctx_trans[:3]:
                    context_parts.append(f"- '{src}' -> '{tgt}'")
        
        return '\n'.join(context_parts) if context_parts else ""
    
    def clear_memory(self):
        """清空記憶庫"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM translations')
        self.conn.commit()
    
    def get_stats(self) -> dict:
        """
        獲取統計資訊
        
        Returns:
            dict: 統計資訊
        """
        cursor = self.conn.cursor()
        
        # 總記錄數
        cursor.execute('SELECT COUNT(*) FROM translations')
        total = cursor.fetchone()[0]
        
        # 語言對數量
        cursor.execute('SELECT DISTINCT source_lang, target_lang FROM translations')
        lang_pairs = cursor.fetchall()
        
        return {
            'total_translations': total,
            'language_pairs': len(lang_pairs),
            'pairs': lang_pairs
        }
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """析構函數"""
        self.close()
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return f"TranslationMemory(translations={stats['total_translations']}, db='{self.db_path}')"
