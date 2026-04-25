# YAML 翻譯器開發計劃

## 專案概述

開發一個智能 YAML 翻譯器，支援大型 YAML 文件的分段翻譯，並具備翻譯記憶功能以保持一致性。

## 核心需求

1. **API 配置**：支援 OpenAI 格式的 API（URL、Key、模型選擇）
2. **語言指定**：可指定目標翻譯語言
3. **智能分段**：根據 YAML 節點結構自動分段，避免 context 過大
4. **翻譯記憶**：維護翻譯一致性的記憶庫
5. **速率限制**：防止 API 速率限制問題

## 技術架構

### 目錄結構
```
yaml-translate/
├── yaml_translator/
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── yaml_parser.py         # YAML 解析與分段
│   ├── translator.py          # 翻譯核心邏輯
│   ├── memory.py              # 翻譯記憶庫
│   ├── api_client.py          # OpenAI API 客戶端
│   └── rate_limiter.py        # 速率限制器
├── tests/
│   ├── test_yaml_parser.py
│   ├── test_translator.py
│   └── test_memory.py
├── examples/
│   ├── sample.yaml
│   └── config.example.yaml
├── requirements.txt
├── setup.py
├── README.md
└── .env.example
```

## 模塊設計

### 1. 配置管理 (config.py)
**功能**：
- 讀取環境變數或配置文件
- 管理 API URL、Key、模型名稱
- 設定目標語言、速率限制等參數

**配置項**：
```python
- API_URL: OpenAI API 端點
- API_KEY: API 金鑰
- MODEL: 模型名稱（如 gpt-4, gpt-3.5-turbo）
- TARGET_LANGUAGE: 目標語言
- MAX_TOKENS_PER_REQUEST: 每次請求的最大 token 數
- RATE_LIMIT_RPM: 每分鐘請求次數限制
- RATE_LIMIT_TPM: 每分鐘 token 數限制
- MEMORY_DB_PATH: 翻譯記憶庫存儲路徑
```

### 2. YAML 解析與分段 (yaml_parser.py)
**功能**：
- 解析 YAML 文件結構
- 按節點（key-value pairs）分段
- 計算每段的字數/token 數
- 遞迴細分過大的段落

**核心算法**：
```python
1. 解析 YAML 為樹狀結構
2. 遍歷第一層節點作為初始段落
3. 估算每段 token 數：
   - 如果 < MAX_TOKENS_PER_REQUEST，作為一個翻譯單元
   - 如果 >= MAX_TOKENS_PER_REQUEST：
     - 檢查是否可細分（有子節點）
     - 遞迴分割子節點
     - 如果無法細分（純文本），按字數分割
4. 保留 YAML 路徑資訊（如 root.section.subsection）
```

**段落結構**：
```python
{
    "path": "root.config.database",  # YAML 路徑
    "content": {...},                 # 原始內容
    "token_count": 150,               # 估算 token 數
    "parent": "root.config"           # 父節點路徑
}
```

### 3. 翻譯記憶庫 (memory.py)
**功能**：
- 儲存歷史翻譯對照
- 查詢相似翻譯
- 提供一致性建議

**實現方式**：
- 使用 SQLite 作為本地資料庫
- 儲存：原文、譯文、語言對、時間戳
- 支援模糊匹配和精確匹配
- 為 AI 提供翻譯上下文

**數據結構**：
```sql
CREATE TABLE translations (
    id INTEGER PRIMARY KEY,
    source_text TEXT NOT NULL,
    target_text TEXT NOT NULL,
    source_lang TEXT DEFAULT 'en',
    target_lang TEXT NOT NULL,
    context_path TEXT,  -- YAML 路徑
    created_at TIMESTAMP,
    INDEX(source_text, target_lang)
);
```

**查詢策略**：
1. 精確匹配：完全相同的原文
2. 相似匹配：使用相似度算法（如 difflib）
3. 上下文匹配：相同 YAML 路徑下的翻譯

### 4. OpenAI API 客戶端 (api_client.py)
**功能**：
- 封裝 OpenAI API 呼叫
- 支援自定義 API URL
- 處理錯誤和重試
- 計算 token 使用量

**核心方法**：
```python
class OpenAIClient:
    def __init__(self, api_url, api_key, model):
        ...
    
    def translate(self, text, target_lang, memory_context=None):
        """
        翻譯文本
        參數：
            text: 待翻譯文本
            target_lang: 目標語言
            memory_context: 來自記憶庫的上下文
        """
        prompt = self._build_prompt(text, target_lang, memory_context)
        return self._call_api(prompt)
    
    def _build_prompt(self, text, target_lang, memory_context):
        """構建包含記憶上下文的提示詞"""
        ...
```

### 5. 速率限制器 (rate_limiter.py)
**功能**：
- 追蹤 API 請求頻率
- 追蹤 token 使用量
- 自動延遲以符合限制

**實現方式**：
- 使用滑動窗口算法
- 記錄每分鐘的請求數和 token 數
- 在超過限制前自動等待

**核心邏輯**：
```python
class RateLimiter:
    def __init__(self, rpm_limit, tpm_limit):
        self.rpm_limit = rpm_limit  # requests per minute
        self.tpm_limit = tpm_limit  # tokens per minute
        self.request_times = []
        self.token_counts = []
    
    def wait_if_needed(self, estimated_tokens):
        """如需要則等待以符合速率限制"""
        ...
    
    def record_request(self, tokens_used):
        """記錄請求"""
        ...
```

### 6. 翻譯核心邏輯 (translator.py)
**功能**：
- 協調所有模塊
- 執行翻譯流程
- 合併翻譯結果
- 保持 YAML 結構

**翻譯流程**：
```python
1. 讀取並解析 YAML 文件
2. 分段處理：
   a. 使用 yaml_parser 分段
   b. 對每個段落：
      - 從 memory 查詢相關翻譯
      - 使用 rate_limiter 控制速率
      - 呼叫 api_client 進行翻譯
      - 將結果存入 memory
      - 記錄進度
3. 合併所有翻譯結果
4. 重建 YAML 結構
5. 輸出翻譯後的 YAML 文件
```

**進度追蹤**：
- 顯示當前處理的段落
- 顯示完成百分比
- 估算剩餘時間

### 7. CLI 介面
**功能**：
- 命令行參數解析
- 互動式配置
- 進度顯示

**使用範例**：
```bash
# 基本用法
yaml-translate input.yaml -o output.yaml -l zh-TW

# 完整參數
yaml-translate input.yaml \
  --output output.yaml \
  --language zh-TW \
  --api-url https://api.openai.com/v1 \
  --api-key sk-xxx \
  --model gpt-4 \
  --rpm-limit 60 \
  --tpm-limit 90000

# 使用配置文件
yaml-translate input.yaml --config config.yaml
```

## 實現步驟

### 階段 1：基礎架構（第 1-2 天）
1. 創建專案結構
2. 設置虛擬環境和依賴
3. 實現配置管理模塊
4. 創建基本的測試框架

### 階段 2：YAML 處理（第 3-4 天）
1. 實現 YAML 解析器
2. 實現分段算法
3. 實現 token 計數（使用 tiktoken）
4. 測試各種 YAML 結構

### 階段 3：翻譯記憶庫（第 5 天）
1. 設計資料庫 schema
2. 實現 CRUD 操作
3. 實現相似度匹配算法
4. 測試記憶功能

### 階段 4：API 整合（第 6-7 天）
1. 實現 OpenAI API 客戶端
2. 實現速率限制器
3. 設計翻譯提示詞模板
4. 測試 API 呼叫和錯誤處理

### 階段 5：核心翻譯邏輯（第 8-9 天）
1. 實現主翻譯流程
2. 整合所有模塊
3. 實現結果合併和 YAML 重建
4. 端到端測試

### 階段 6：CLI 和優化（第 10 天）
1. 實現命令行介面
2. 添加進度顯示
3. 性能優化
4. 撰寫文檔

### 階段 7：測試和發布（第 11-12 天）
1. 完整測試
2. 編寫 README 和使用說明
3. 準備範例文件
4. 打包發布

## 技術選型

### 核心依賴
- **PyYAML**：YAML 解析和生成
- **tiktoken**：OpenAI token 計數
- **requests**：HTTP 請求
- **click**：CLI 框架
- **python-dotenv**：環境變數管理
- **tqdm**：進度條顯示

### 開發依賴
- **pytest**：測試框架
- **black**：代碼格式化
- **flake8**：代碼檢查
- **mypy**：類型檢查

## 進階功能（可選）

1. **批次處理**：同時處理多個 YAML 文件
2. **增量翻譯**：只翻譯修改過的部分
3. **翻譯品質檢查**：驗證翻譯結果的完整性
4. **多語言支援**：同時輸出多種語言
5. **Web UI**：提供圖形化介面
6. **翻譯術語表**：自定義特定術語的翻譯
7. **備份和回滾**：保留翻譯歷史版本

## 注意事項

1. **Token 估算**：使用 tiktoken 準確計算，為 prompt 預留空間
2. **YAML 特殊字符**：正確處理引號、換行、縮排
3. **錯誤處理**：網路錯誤、API 錯誤的優雅處理和重試
4. **資料安全**：API Key 不應硬編碼，使用環境變數
5. **編碼問題**：統一使用 UTF-8
6. **記憶庫大小**：定期清理舊記錄，避免資料庫過大
7. **並發控制**：避免同時修改記憶庫造成衝突

## 測試策略

1. **單元測試**：每個模塊獨立測試
2. **整合測試**：模塊間協作測試
3. **端到端測試**：完整翻譯流程測試
4. **邊界測試**：
   - 空 YAML
   - 超大 YAML
   - 深層嵌套結構
   - 特殊字符
5. **速率限制測試**：驗證速率限制器正確運作

## 估算時間

- **開發時間**：10-12 天（全職）
- **測試時間**：2-3 天
- **文檔時間**：1-2 天
- **總計**：約 2-3 週

## 成功標準

1. 能正確翻譯各種結構的 YAML 文件
2. 翻譯保持一致性（相同原文得到相同譯文）
3. 不觸發 API 速率限制
4. 處理大型文件不會超出 context 限制
5. CLI 介面友好，易於使用
6. 代碼結構清晰，易於維護和擴展
