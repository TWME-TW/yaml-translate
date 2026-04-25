"""
速率限制器模塊
防止超過 API 速率限制
"""

import time
import threading
from typing import List, Tuple
from collections import deque


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, requests_per_minute: int = 60, tokens_per_minute: int = 90000):
        """
        初始化速率限制器
        
        Args:
            requests_per_minute: 每分鐘最大請求數
            tokens_per_minute: 每分鐘最大 token 數
        """
        self.rpm_limit = requests_per_minute
        self.tpm_limit = tokens_per_minute
        
        self.lock = threading.Lock()
        
        # 使用 deque 記錄請求時間和 token 數
        self.request_times: deque = deque()
        self.token_records: deque = deque()  # (timestamp, tokens)
    
    def wait_if_needed(self, estimated_tokens: int = 0):
        """
        如果需要則等待以符合速率限制
        
        Args:
            estimated_tokens: 預估的 token 數
        """
        while True:
            with self.lock:
                current_time = time.time()
                
                # 清理 60 秒前的記錄
                self._clean_old_records(current_time)
                
                wait_time = 0
                # 檢查請求數限制
                if len(self.request_times) >= self.rpm_limit:
                    oldest_time = self.request_times[0]
                    wait_time = max(wait_time, 60 - (current_time - oldest_time))
                
                # 檢查 token 數限制
                current_tokens = sum(tokens for _, tokens in self.token_records)
                if current_tokens + estimated_tokens > self.tpm_limit:
                    if self.token_records:
                        oldest_time = self.token_records[0][0]
                        wait_time = max(wait_time, 60 - (current_time - oldest_time))
                
                if wait_time > 0:
                    pass # We will sleep outside the lock
                else:
                    return # Safe to proceed
            
            if wait_time > 0:
                print(f"⏳ Rate limit approaching. Thread waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
    
    def record_request(self, tokens_used: int):
        """
        記錄一次請求
        
        Args:
            tokens_used: 使用的 token 數
        """
        with self.lock:
            current_time = time.time()
            self.request_times.append(current_time)
            self.token_records.append((current_time, tokens_used))
    
    def _clean_old_records(self, current_time: float):
        """
        清理 60 秒前的記錄
        
        Args:
            current_time: 當前時間戳
        """
        cutoff_time = current_time - 60
        
        # 清理請求時間記錄
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()
        
        # 清理 token 記錄
        while self.token_records and self.token_records[0][0] < cutoff_time:
            self.token_records.popleft()
    
    def get_stats(self) -> dict:
        """
        獲取當前統計資訊
        
        Returns:
            dict: 統計資訊
        """
        current_time = time.time()
        self._clean_old_records(current_time)
        
        current_tokens = sum(tokens for _, tokens in self.token_records)
        
        return {
            'requests_in_window': len(self.request_times),
            'rpm_limit': self.rpm_limit,
            'tokens_in_window': current_tokens,
            'tpm_limit': self.tpm_limit,
        }
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return (f"RateLimiter(RPM: {stats['requests_in_window']}/{stats['rpm_limit']}, "
                f"TPM: {stats['tokens_in_window']}/{stats['tpm_limit']})")
