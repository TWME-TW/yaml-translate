# YAML Translator

一個智能的 YAML 翻譯器，支援大型文件的分段翻譯，並具備翻譯記憶功能。

## 特色功能

- 🔄 **智能分段**：自動根據 YAML 結構分段，避免 context 過大
- 🎯 **精準翻譯**：支援指定特定 YAML 鍵值或段落進行局部翻譯
- 💾 **原地替換**：支援直接覆寫原檔案 (`-i`)，方便漸進式翻譯工作流
- 🧠 **翻譯記憶**：維護翻譯一致性的記憶庫
- ⚡ **速率控制**：內建速率限制器，防止 API 限制問題
- 🎯 **靈活配置**：支援 OpenAI 格式的 API（自定義 URL、Key、模型）
- 📊 **進度追蹤**：即時顯示翻譯進度
- 🌍 **多語言支援**：可指定任意目標語言
- ✨ **自定義 Prompt**：完全控制翻譯提示詞，支援模板文件和規則列表

## 安裝

```bash
# 克隆專案
git clone <repository-url>
cd yaml-translate

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 開發安裝
pip install -e .
```

## 快速開始

### 1. 配置 API

創建 `.env` 文件：

```env
API_URL=https://api.openai.com/v1
API_KEY=your-api-key-here
MODEL=gpt-4
TARGET_LANGUAGE=zh-TW
RATE_LIMIT_RPM=60
RATE_LIMIT_TPM=90000
```

### 2. 基本使用

```bash
# 簡單翻譯
yaml-translate input.yaml -o output.yaml

# 指定語言
yaml-translate input.yaml -o output.yaml -l zh-TW

# 翻譯特定段落 (可多個目標鍵，逗號分隔)
yaml-translate input.yaml -o output.yaml -l zh-TW -k app.name,settings.theme

# 原地替換 (直接修改並覆寫原檔案)
yaml-translate input.yaml -i -l zh-TW

# 原地替換且只翻譯指定段落
yaml-translate input.yaml -i -l zh-TW -k settings

# 使用配置文件
yaml-translate input.yaml --config config.yaml
```

### 3. 自定義翻譯 Prompt（可選）✨

**方法 A：在 config.yaml 中自定義規則**

```yaml
prompt:
  rules:
    - "1. 只返回翻譯文本，不添加解釋"
    - "2. 保持 YAML 格式不變"
    - "3. 技術術語保持英文"
    - "4. 使用台灣繁體中文"
```

**方法 B：使用外部模板文件**

```yaml
prompt:
  template_file: "./prompts/my_template.txt"
```

**方法 C：完整自定義 prompt**

```yaml
prompt:
  custom_prompt: "你是專業翻譯。翻譯成 {target_lang}: {text}"
```

詳細說明請查看 [Prompt 自定義指南](PROMPT_GUIDE.md)。

### 4. 完整參數

```bash
yaml-translate input.yaml \
  -i \
  -k app.name,settings \
  --output output.yaml \
  --language zh-TW \
  --api-url https://api.openai.com/v1 \
  --api-key sk-xxx \
  --model gpt-4 \
  --rpm-limit 60 \
  --tpm-limit 90000 \
  --max-tokens 4000
```

## 工作原理

1. **解析**：讀取並解析 YAML 文件結構
2. **分段**：根據節點和 token 數智能分段
3. **記憶查詢**：從翻譯記憶庫查找相似翻譯
4. **翻譯**：使用 AI 進行翻譯，維持一致性
5. **速率控制**：自動控制請求速率
6. **合併**：重建 YAML 結構並輸出

## 專案結構

```
yaml-translate/
├── yaml_translator/       # 核心模塊
│   ├── config.py         # 配置管理
│   ├── yaml_parser.py    # YAML 解析與分段
│   ├── translator.py     # 翻譯核心
│   ├── memory.py         # 翻譯記憶庫
│   ├── api_client.py     # API 客戶端
│   └── rate_limiter.py   # 速率限制器
├── prompts/              # Prompt 模板
│   ├── default_template.txt    # 默認英文模板
│   └── chinese_template.txt    # 中文模板
├── tests/                # 測試
└── examples/             # 範例文件
```

## 📚 文檔

- **[QUICKSTART.md](QUICKSTART.md)** - 快速開始指南（5 分鐘上手）
- **[PROMPT_GUIDE.md](PROMPT_GUIDE.md)** - Prompt 自定義完整指南 ✨
- **[DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)** - 技術架構和開發計劃
- **[TODO.md](TODO.md)** - 開發任務清單

## 開發

```bash
# 運行測試
pytest

# 代碼格式化
black yaml_translator/

# 代碼檢查
flake8 yaml_translator/
```

## 詳細文檔

- **[開發計劃](DEVELOPMENT_PLAN.md)** - 了解技術架構和實現細節
- **[Prompt 指南](PROMPT_GUIDE.md)** - 學習如何自定義翻譯 prompt ✨
- **[快速開始](QUICKSTART.md)** - 5 分鐘快速上手教程

## 授權

MIT License
