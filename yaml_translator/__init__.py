"""
YAML Translator
一個智能的 YAML 翻譯器，支援大型文件的分段翻譯
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .translator import YAMLTranslator
from .config import Config

__all__ = ["YAMLTranslator", "Config"]
