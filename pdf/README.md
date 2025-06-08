# PDF論文摘要工具

這是一個用於處理學術論文PDF檔案並生成摘要的Python工具。它可以提取PDF文字內容，並使用OpenAI的GPT模型為每篇論文生成摘要。

## 功能

- 批量處理多個PDF檔案
- 提取PDF文字內容
- 使用OpenAI GPT模型生成摘要
- 支援為每個PDF生成單獨摘要或生成所有PDF的組合摘要
- 自動處理長文本，分段提交給GPT模型
- 可選擇生成段落級別的摘要，快速查看各段重點

## 安裝

1. 確保您已安裝Python 3.6+
2. 安裝所需依賴：

```bash
pip install PyMuPDF openai python-dotenv
```

## 配置

1. 創建一個`.env`檔案在與腳本相同的目錄中
2. 在`.env`檔案中添加您的OpenAI API密鑰：

```
OPENAI_API_KEY=your_api_key_here
```

3. 在目錄下創建一個名為`journals`的資料夾
4. 將您需要分析的PDF論文放入`journals`資料夾中

## 使用方法

基本用法：

```bash
python pdf-summary.py
```

### 選項

- `-c, --combined`: 生成所有PDF的組合摘要
- `-p, --paragraph`: 同時生成段落摘要
- `-m, --model`: 指定使用的OpenAI模型（默認為"gpt-3.5-turbo"）

### 示例

1. 處理journals資料夾中的所有PDF並為每個檔案生成單獨摘要：

```bash
python pdf-summary.py
```

2. 生成所有PDF的組合摘要：

```bash
python pdf-summary.py -c
```

3. 生成每篇論文的段落摘要：

```bash
python pdf-summary.py -p
```

4. 使用特定模型並生成組合摘要和段落摘要：

```bash
python pdf-summary.py -c -p -m gpt-4
```

## 輸出

- 單個PDF摘要將保存在`journals/summaries`子目錄下，檔名為`{原檔名}_summary.txt`
- 段落摘要將保存為`{原檔名}_paragraph_summary.txt`
- 組合摘要將保存為`summaries/combined_summary.txt`
- 所有摘要的綜合報告將保存為`summaries/summary_report.txt`

## 注意事項

- 處理大型PDF檔案時可能需要更多時間
- API請求可能會產生費用，請注意您的OpenAI API使用量
- 對於非常長的文本，腳本會自動分段處理，並在最後合併摘要 