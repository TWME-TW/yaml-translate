"""
Tests for TranslationMemory module
"""

import os
import pytest
import tempfile
from yaml_translator.memory import TranslationMemory


@pytest.fixture
def temp_db():
    """創建臨時資料庫"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


def test_memory_initialization(temp_db):
    """測試記憶庫初始化"""
    memory = TranslationMemory(temp_db)
    stats = memory.get_stats()
    
    assert stats['total_translations'] == 0
    assert stats['language_pairs'] == 0
    
    memory.close()


def test_add_and_find_translation(temp_db):
    """測試添加和查找翻譯"""
    memory = TranslationMemory(temp_db)
    
    # 添加翻譯
    memory.add_translation(
        source_text="Hello",
        target_text="你好",
        target_lang="zh-TW"
    )
    
    # 查找翻譯
    result = memory.find_exact_match("Hello", "zh-TW")
    
    assert result == "你好"
    
    memory.close()


def test_find_similar_translations(temp_db):
    """測試查找相似翻譯"""
    memory = TranslationMemory(temp_db)
    
    # 添加多個翻譯
    memory.add_translation("Hello world", "你好世界", "zh-TW")
    memory.add_translation("Hello there", "你好啊", "zh-TW")
    memory.add_translation("Hi world", "嗨世界", "zh-TW")
    
    # 查找相似翻譯
    similar = memory.find_similar_translations("Hello", "zh-TW", threshold=0.5)
    
    assert len(similar) > 0
    # 應該找到包含 "Hello" 的翻譯
    assert any("Hello" in s[0] for s in similar)
    
    memory.close()


def test_get_context_translations(temp_db):
    """測試獲取上下文翻譯"""
    memory = TranslationMemory(temp_db)
    
    # 添加帶上下文的翻譯
    memory.add_translation(
        source_text="Settings",
        target_text="設定",
        target_lang="zh-TW",
        context_path="root.app.settings"
    )
    
    memory.add_translation(
        source_text="Theme",
        target_text="主題",
        target_lang="zh-TW",
        context_path="root.app.settings.theme"
    )
    
    # 獲取上下文翻譯
    context = memory.get_context_translations("root.app.settings", "zh-TW")
    
    assert len(context) >= 1
    
    memory.close()


def test_memory_stats(temp_db):
    """測試統計資訊"""
    memory = TranslationMemory(temp_db)
    
    # 添加不同語言對的翻譯
    memory.add_translation("Hello", "你好", "zh-TW")
    memory.add_translation("Hello", "こんにちは", "ja")
    
    stats = memory.get_stats()
    
    assert stats['total_translations'] == 2
    assert stats['language_pairs'] == 2
    
    memory.close()
