# Prompt 自定義指南

本指南說明如何自定義 YAML Translator 的翻譯 prompt。

## 📍 三種自定義方式

### 方式 1：自定義規則列表（最簡單）

在 `config.yaml` 中自定義翻譯規則：

```yaml
prompt:
  rules:
    - "1. 只返回翻譯文本，不添加解釋"
    - "2. 保持 YAML 格式不變"
    - "3. 技術術語保持英文"
    - "4. 使用台灣繁體中文"
    - "5. 語氣要專業正式"
```

或在 `.env` 中（不推薦，格式受限）：

```env
# .env 不支援規則列表，請使用 config.yaml
```

### 方式 2：完整自定義 Prompt

#### 在配置文件中 (config.yaml)

```yaml
prompt:
  custom_prompt: |
    你是專業翻譯。將以下內容翻譯成 {target_lang}。
    
    要求：
    - 保持格式
    - 技術詞彙不翻譯
    - 使用自然的語言
    
    內容：{text}
```

#### 在環境變數中 (.env)

```env
CUSTOM_PROMPT="You are a translator. Translate to {target_lang}: {text}"
```

**可用變數：**
- `{target_lang}` - 目標語言
- `{text}` - 待翻譯文本
- `{memory_context}` - 翻譯記憶（自動添加）

### 方式 3：使用外部模板文件（最靈活）✨

#### 1. 創建 prompt 模板文件

創建 `prompts/my_prompt.txt`：

```
You are a professional translator specializing in {domain}.

Translate the following text to {target_lang}.

CONTEXT:
This is a {file_type} configuration file for a {project_type} project.

RULES:
1. Maintain YAML structure
2. Keep variable names in English
3. Use professional terminology
4. Target audience: developers

{memory_context}

TEXT TO TRANSLATE:
{text}
```

#### 2. 在配置中指定模板文件

**方法 A：使用 config.yaml**

```yaml
prompt:
  template_file: "./prompts/my_prompt.txt"
```

**方法 B：使用 .env**

```env
PROMPT_TEMPLATE_FILE=./prompts/my_prompt.txt
```

**方法 C：命令行參數**

```bash
yaml-translate input.yaml \
  --config config.yaml
```

## 📝 模板變數說明

### 必需變數

- `{target_lang}` - 目標語言（由程式自動填入）
- `{text}` - 待翻譯文本（由程式自動填入）

### 可選變數

- `{memory_context}` - 翻譯記憶上下文（如果有的話自動填入，沒有則為空）

### 自定義變數

你可以在模板中使用任何變數名，但需要確保在使用時能正確替換。

## 🎯 實際範例

### 範例 1：技術文檔翻譯

**config.yaml:**

```yaml
prompt:
  rules:
    - "1. 只返回翻譯後的文本"
    - "2. 保持 YAML 結構完整"
    - "3. 以下術語保持英文：API, Token, Configuration, Database"
    - "4. 變數名稱（如 api_key, database_url）保持不變"
    - "5. 使用台灣繁體中文"
    - "6. 技術名詞首次出現時加註英文，如：應用程式介面 (API)"
```

### 範例 2：用戶界面文本

**prompts/ui_translation.txt:**

```
You are a UX writer specializing in user interface translations.

Translate the following UI text to {target_lang}.

GUIDELINES:
- Keep it concise and user-friendly
- Use action-oriented language
- Match the tone of modern applications
- Consider cultural context
- Maximum 50 characters per string when possible

{memory_context}

UI TEXT:
{text}

Remember: This will be displayed in a user interface.
```

**使用：**

```bash
yaml-translate ui_strings.yaml \
  --config ui_config.yaml
```

### 範例 3：多語言團隊協作

**prompts/team_translation.txt:**

```
You are translating for an international development team.

Target language: {target_lang}

TEAM GLOSSARY:
- "deployment" → 部署 (bù shǔ)
- "container" → 容器 (róng qì)
- "pipeline" → 流水線 (liú shuǐ xiàn)
- "staging" → 預備環境 (yù bèi huán jìng)

CONSISTENCY NOTES:
{memory_context}

TRANSLATION RULES:
1. Follow team glossary strictly
2. Keep code and variable names unchanged
3. Use Simplified Chinese (簡體中文)
4. Add English terms in parentheses for ambiguous words

CONTENT:
{text}
```

## 🔧 進階技巧

### 1. 條件性規則

在模板中使用條件邏輯（需要在 prompt 中說明）：

```
If the text contains code blocks:
  - Do not translate code
  - Only translate comments

If the text is a user message:
  - Use friendly tone
  - Keep it concise
```

### 2. 特定領域術語

```yaml
prompt:
  custom_prompt: |
    專業領域：醫療/金融/法律
    
    翻譯到 {target_lang}，注意：
    - 使用該領域的專業術語
    - 保持嚴謹性
    - 必要時加註原文
    
    文本：{text}
```

### 3. 品質控制

```
After translating, perform a self-check:
1. Is the structure preserved?
2. Are technical terms correct?
3. Is the language natural?
4. Does it match previous translations?

Only return the final translation.
```

## 📊 優先級順序

當多個配置同時存在時，優先級為：

1. **prompt_template_file** （最高優先級）
2. **custom_prompt**
3. **prompt.rules**
4. **默認 prompt** （最低優先級）

## ✅ 最佳實踐

### 1. 開發階段

```yaml
# 使用靈活的規則列表
prompt:
  rules:
    - "Rule 1..."
    - "Rule 2..."
```

### 2. 生產環境

```yaml
# 使用穩定的模板文件
prompt:
  template_file: "./prompts/production_template.txt"
```

### 3. 測試不同 Prompt

```bash
# 測試 prompt A
yaml-translate test.yaml --config config_a.yaml -o output_a.yaml

# 測試 prompt B  
yaml-translate test.yaml --config config_b.yaml -o output_b.yaml

# 比較結果
diff output_a.yaml output_b.yaml
```

## 🎨 範例模板集合

專案提供了以下預設模板（在 `prompts/` 目錄）：

- `default_template.txt` - 默認英文模板
- `chinese_template.txt` - 中文提示詞模板
- 你可以複製並修改這些模板

## 🐛 故障排除

### 問題 1：模板文件找不到

```
⚠️  Failed to load prompt template file: [Errno 2] No such file or directory
```

**解決：** 檢查路徑是否正確，使用絕對路徑或相對於專案根目錄的路徑。

### 問題 2：變數未被替換

確保在模板中使用正確的變數格式：`{variable_name}`

### 問題 3：翻譯品質不佳

嘗試：
1. 增加更具體的規則
2. 提供更多上下文
3. 調整語言模型的 temperature（在代碼中）
4. 使用更強大的模型（如 gpt-4）

## 📚 延伸閱讀

- [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Best Practices for Prompts](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-openai-api)

---

需要幫助？查看 [README.md](../README.md) 或提交 Issue。
