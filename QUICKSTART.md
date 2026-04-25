# 快速開始指南

本指南將幫助你在 5 分鐘內開始使用 YAML Translator。

## 步驟 1：安裝依賴

```bash
# 創建虛擬環境（推薦）
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 安裝專案（開發模式）
pip install -e .
```

## 步驟 2：配置 API

創建 `.env` 文件（或複製 `.env.example`）：

```bash
# Windows:
copy .env.example .env
# Linux/Mac:
cp .env.example .env
```

編輯 `.env` 文件，填入你的 API 資訊：

```env
API_URL=https://api.openai.com/v1
API_KEY=your-api-key-here
MODEL=gpt-4
TARGET_LANGUAGE=zh-TW
```

### 支援的 API 提供商

本工具支援所有兼容 OpenAI 格式的 API：

- **OpenAI**：`https://api.openai.com/v1`
- **Azure OpenAI**：`https://your-resource.openai.azure.com/`
- **其他兼容 API**：只要支援 `/chat/completions` 端點即可

## 步驟 3：測試連接

```bash
yaml-translate examples/simple.yaml --test-connection
```

如果看到 "✅ API connection successful!"，表示配置正確。

## 步驟 4：第一次翻譯

```bash
# 翻譯範例文件
yaml-translate examples/simple.yaml -o examples/simple_zh.yaml -l zh-TW
```

你應該會看到類似以下的輸出：

```
✅ YAML Translator initialized
   Model: gpt-4
   Target Language: zh-TW
   Rate Limits: 60 RPM, 90000 TPM

📄 Processing: examples/simple.yaml
🎯 Target language: zh-TW

🔍 Parsing and segmenting YAML...
   Created 5 segment(s)
   Total tokens: 250

🌍 Translating 5 segment(s)...
Translating: 100%|████████████████| 5/5 [00:10<00:00, 2.00s/segment]

🔨 Reconstructing YAML structure...
💾 Saving to: examples/simple_zh.yaml

✅ Translation completed!
```

## 步驟 5：檢查結果

打開生成的文件 `examples/simple_zh.yaml`，你應該會看到翻譯後的內容。

## 常用命令

### 基本翻譯

```bash
# 最簡單的用法（使用 .env 中的配置）
yaml-translate input.yaml -o output.yaml

# 指定目標語言
yaml-translate input.yaml -o output.yaml -l ja

# 自動生成輸出文件名（input_translated.yaml）
yaml-translate input.yaml -l zh-TW
```

### 精準翻譯與原地替換

```bash
# 只翻譯特定的鍵值段落 (多個請用逗號分隔)
yaml-translate input.yaml -o output.yaml -l zh-TW -k app.name,settings

# 原地覆寫翻譯 (不再產生新檔案，直接修改 input.yaml)
yaml-translate input.yaml -i -l zh-TW

# 原地覆寫且僅翻譯指定段落 (非常適合進行漸進式翻譯)
yaml-translate input.yaml -i -l zh-TW -k messages.error
```

### 使用配置文件

```bash
# 使用 YAML 配置文件
yaml-translate input.yaml --config config.example.yaml
```

### 命令行覆蓋配置

```bash
# 覆蓋特定參數
yaml-translate input.yaml \
  --api-url https://custom.api.com \
  --api-key sk-custom-key \
  --model gpt-3.5-turbo \
  --language zh-CN \
  --rpm-limit 30 \
  --tpm-limit 40000
```

### 翻譯大型文件

```bash
# 對於大型文件，可以調整分段參數
yaml-translate large.yaml \
  --max-tokens 2000 \
  --rpm-limit 20
```

## 進階使用

### 1. 翻譯記憶庫

翻譯記憶會自動維護，存儲在 `translation_memory.db`。如果需要清空：

```bash
# 刪除記憶庫
rm translation_memory.db
```

### 2. 速率限制調整

根據你的 API 方案調整速率限制：

| API 方案 | RPM | TPM |
|---------|-----|-----|
| Free Tier | 3 | 40,000 |
| Pay-as-you-go | 60 | 90,000 |
| Dedicated | 自定義 | 自定義 |

在 `.env` 中設置：

```env
RATE_LIMIT_RPM=60
RATE_LIMIT_TPM=90000
```

### 3. 批次處理

使用腳本批次處理多個文件：

```bash
# Windows (PowerShell)
Get-ChildItem *.yaml | ForEach-Object {
    yaml-translate $_.Name -o "$($_.BaseName)_zh.yaml" -l zh-TW
}

# Linux/Mac (Bash)
for file in *.yaml; do
    yaml-translate "$file" -o "${file%.yaml}_zh.yaml" -l zh-TW
done
```

## 故障排除

### 問題 1：API Key 錯誤

```
❌ Configuration error: API_KEY is required
```

**解決方案**：確保 `.env` 文件存在且包含有效的 API_KEY。

### 問題 2：速率限制

```
⏳ Rate limit reached. Waiting 15.5 seconds...
```

**解決方案**：這是正常行為，程式會自動等待。你可以調低 RPM/TPM 限制。

### 問題 3：連接失敗

```
❌ API connection failed
```

**解決方案**：
1. 檢查網路連接
2. 驗證 API_URL 和 API_KEY 是否正確
3. 確認 API 服務是否可用

### 問題 4：YAML 解析錯誤

```
❌ Error: Failed to parse YAML file
```

**解決方案**：
1. 驗證 YAML 文件格式是否正確
2. 使用在線 YAML 驗證器檢查語法
3. 確保文件編碼為 UTF-8

## 運行測試

```bash
# 運行所有測試
pytest

# 運行特定測試
pytest tests/test_config.py

# 顯示覆蓋率
pytest --cov=yaml_translator
```

## 下一步

- 閱讀 [README.md](README.md) 了解更多功能
- 查看 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) 了解技術細節
- 嘗試翻譯你自己的 YAML 文件！

## 需要幫助？

如果遇到問題：

1. 檢查 `.env` 配置
2. 運行 `yaml-translate --help` 查看所有選項
3. 使用 `--test-connection` 測試 API 連接
4. 查看錯誤訊息並參考本指南的故障排除部分
