"""
Tests for RateLimiter module
"""

import time
import pytest
from yaml_translator.rate_limiter import RateLimiter


def test_rate_limiter_initialization():
    """測試速率限制器初始化"""
    limiter = RateLimiter(rpm_limit=60, tpm_limit=90000)
    
    assert limiter.rpm_limit == 60
    assert limiter.tpm_limit == 90000


def test_rate_limiter_record():
    """測試記錄請求"""
    limiter = RateLimiter(rpm_limit=60, tpm_limit=90000)
    
    limiter.record_request(100)
    limiter.record_request(200)
    
    stats = limiter.get_stats()
    assert stats['requests_in_window'] == 2
    assert stats['tokens_in_window'] == 300


def test_rate_limiter_cleanup():
    """測試清理舊記錄"""
    limiter = RateLimiter(rpm_limit=60, tpm_limit=90000)
    
    # 記錄一個請求
    limiter.record_request(100)
    
    # 等待一小段時間
    time.sleep(0.1)
    
    stats = limiter.get_stats()
    assert stats['requests_in_window'] == 1


def test_rate_limiter_stats():
    """測試統計資訊"""
    limiter = RateLimiter(rpm_limit=10, tpm_limit=1000)
    
    for i in range(5):
        limiter.record_request(100)
    
    stats = limiter.get_stats()
    assert stats['requests_in_window'] == 5
    assert stats['tokens_in_window'] == 500
    assert stats['rpm_limit'] == 10
    assert stats['tpm_limit'] == 1000
