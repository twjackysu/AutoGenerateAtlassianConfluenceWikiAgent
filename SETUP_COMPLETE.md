"""
Final Setup Instructions and Usage Guide
Auto-Generate Atlassian Confluence Wiki Agent
"""

# 🚀 Auto-Generate Atlassian Confluence Wiki Agent

## ✅ 系統已成功建立！

您的多代理文檔生成系統已經完成設置，包含以下核心組件：

### 🏗️ 已實作的代理架構

1. **Code Retrieval Agent** (`src/agents/code_retrieval_agent.py`)
   - 支援 GitHub 倉庫克隆和本地目錄分析
   - 智能檔案過濾和內容讀取

2. **Codebase Analysis Agent** (`src/agents/codebase_analysis_agent.py`)
   - Python AST 解析
   - JavaScript/TypeScript 基本分析
   - 依賴關係提取和專案結構分析

3. **Documentation Generation Agent** (`src/agents/documentation_generation_agent.py`)
   - 多種文檔類型生成（架構、API、組件、設置指南）
   - 智能內容結構化

4. **Confluence Publishing Agent** (`src/agents/confluence_publishing_agent.py`)
   - Atlassian MCP Server 整合
   - Confluence Wiki 格式轉換
   - 頁面層次結構管理

5. **Query Refinement Agent** (`src/agents/query_refinement_agent.py`)
   - 用戶需求澄清和精煉
   - 智能問題生成

### 🛠️ 技術棧整合

- **OpenAI Agent SDK**: 多代理編排框架
- **Claude 4 (Anthropic)**: 主要 LLM 模型
- **Atlassian MCP Server**: Confluence 整合
- **Python 3.13+**: 核心運行環境

## 🎯 快速開始

### 1. 運行演示版本
```bash
# 基本演示（無需 API 密鑰）
uv run python demo.py
```

### 2. 完整功能設置
```bash
# 1. 配置環境變數
cp .env.example .env
# 編輯 .env 檔案並添加您的 API 密鑰

# 2. 運行完整版本
uv run python main.py

# 3. 或使用互動式啟動器
uv run python start.py
```

### 3. 程式化使用
```python
from src.main import WikiGenerationOrchestrator

orchestrator = WikiGenerationOrchestrator()

user_request = {
    "repository": "https://github.com/your-repo.git",
    "documentation_scope": {
        "include_architecture": True,
        "include_api": True,
        "include_components": True,
        "include_setup": True
    },
    "confluence_settings": {
        "space": "YOUR-SPACE-KEY"
    }
}

result = await orchestrator.generate_wiki_documentation(user_request)
```

## 📋 必要配置

在 `.env` 檔案中設置以下變數：

```bash
# Anthropic Claude API Key（必需）
ANTHROPIC_API_KEY=your-anthropic-api-key

# Confluence 設置（必需）
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token

# OpenAI API Key（如果使用 Agent SDK）
OPENAI_API_KEY=your-openai-api-key

# MCP Server URL（可選）
MCP_SERVER_URL=your-mcp-server-url
```

## 🔧 支援的功能

### 文檔類型
- ✅ 專案概覽
- ✅ 架構文檔
- ✅ API 文檔
- ✅ 組件文檔  
- ✅ 安裝設置指南
- ✅ 數據流程文檔

### 支援的程式語言
- ✅ Python
- ✅ JavaScript/TypeScript
- ✅ Java
- ✅ Go
- ✅ C/C++
- ✅ 以及更多...

### 輸出格式
- ✅ Confluence Wiki 格式
- ✅ Markdown 文檔
- ✅ 結構化頁面層次

## 🧪 測試和開發

```bash
# 運行基本測試
uv run python tests/test_basic.py

# 代碼格式化
uv run black src/

# 代碼檢查
uv run flake8 src/
```

## 📁 專案結構

```
AutoGenerateAtlassianConfluenceWikiAgent/
├── src/
│   ├── agents/           # 所有代理實作
│   ├── models/           # LLM 模型包裝器
│   ├── config.py         # 配置管理
│   └── main.py          # 主控制器
├── tests/               # 測試檔案
├── generated_docs/      # 生成的文檔輸出
├── demo.py             # 演示版本
├── start.py            # 互動式啟動器
├── example_usage.py    # 使用範例
└── main.py            # 應用程式入口點
```

## 🚀 下一步

1. **配置您的 API 密鑰** 在 `.env` 檔案中
2. **測試基本功能** 使用 `demo.py`
3. **運行完整系統** 使用 `main.py`
4. **自定義文檔需求** 修改 `user_request` 配置
5. **擴展支援語言** 在分析代理中添加更多解析器

## 💡 進階功能

- **自定義文檔模板**: 修改 `DocumentationGenerationAgent`
- **新增程式語言支援**: 擴展 `CodebaseAnalysisAgent`
- **整合其他文檔平台**: 創建新的發布代理
- **增強 AI 分析**: 調整 Claude 模型提示詞

## 📞 支援

如果遇到問題：
1. 檢查 `.env` 配置是否正確
2. 確認所有依賴項已安裝 (`uv sync`)
3. 查看生成的錯誤日誌
4. 使用 `demo.py` 測試基本功能

## 🎉 恭喜！

您的 Auto-Generate Atlassian Confluence Wiki Agent 已經準備就緒！
這是一個功能完整的多代理系統，能夠：

- 🔍 智能分析代碼庫
- 📚 生成結構化文檔  
- 🌐 自動發布到 Confluence
- 🤖 使用 Claude 4 進行智能內容生成
- 🔧 支援多種程式語言和專案類型

開始探索您的新文檔生成助手吧！
