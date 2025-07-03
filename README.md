# Auto Generate Atlassian Confluence Wiki Agent

🚀 **現代化智能程式碼文件生成系統** - 使用 OpenAI Agent SDK + Claude + MCP，自動掃描程式碼庫並生成結構化的 Wiki 文件，支援發布到 Atlassian Confluence。

## ✨ 最新功能特色

### 🎯 現代化架構
- **OpenAI Agent SDK**: 使用最新的 Agent 框架，更強大的多代理協作
- **Claude 4 整合**: 採用 Anthropic Claude 作為主要 AI 引擎，更精準的程式碼理解
- **MCP 協議支援**: 支援 Model Context Protocol，可整合 Atlassian Remote MCP Server
- **異步處理**: 完全異步架構，更好的效能和響應速度

### 🤖 智能代理系統

1. **Code Analysis Agent** - 程式碼分析代理
   - 使用 Claude 進行深度程式碼理解
   - AST 語法分析和模式識別
   - 智能依賴關係提取
   - API 端點自動發現

2. **Documentation Generator Agent** - 文件生成代理
   - 智能文件結構設計
   - 多類型文件自動生成
   - Markdown 格式最佳化
   - 程式碼範例自動提取

3. **Confluence Publisher Agent** - Confluence 發布代理
   - 透過 MCP 協議與 Atlassian 整合
   - 自動頁面階層建立
   - 版本控制和更新管理
   - 權限和標籤自動設定

## 🚀 快速開始

### 1. 環境設定

```bash
# 克隆專案
git clone <repository-url>
cd AutoGenerateAtlassianConfluenceWikiAgent

# 使用 uv 安裝依賴
uv sync
```

### 2. 配置 API 金鑰

複製並編輯環境變數：

```bash
cp .env.example .env
```

設定必要的 API 金鑰：

```env
# OpenAI API Key (Agent SDK 需要)
OPENAI_API_KEY=your-openai-api-key

# Anthropic Claude API Key (主要 AI 引擎)
ANTHROPIC_API_KEY=your-anthropic-api-key

# Confluence 設定 (可選，使用 MCP)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
```

### 3. 執行系統測試

```bash
# 測試所有功能
uv run test_modern_system.py
```

### 4. 使用現代化系統

```bash
# 啟動現代化 Wiki 生成器
uv run src/modern_wiki_generator.py
```

## 📖 使用指南

### 基本工作流程

1. **智能查詢分析**: 系統會分析您的文件需求
2. **程式碼深度掃描**: 使用 Claude 進行智能程式碼理解
3. **多類型文件生成**: 自動生成架構、API、指南等文件
4. **MCP 協議發布**: 透過 MCP 無縫發布到 Confluence

### 支援的文件類型

- **架構概覽** - 系統設計和技術棧分析
- **API 文件** - 自動發現和文件化 REST API
- **使用者指南** - 基於程式碼自動生成使用說明
- **開發者指南** - 程式碼結構和開發流程
- **部署指南** - 自動識別部署配置

### 程式化使用範例

```python
import asyncio
from src.modern_wiki_generator import ModernWikiGenerator

async def generate_docs():
    generator = ModernWikiGenerator()
    
    # 執行完整工作流程
    results = await generator.generate_wiki_workflow(
        user_request="為這個 Python 專案生成完整的技術文件，包括 API 說明和部署指南",
        project_path="./my-project",
        project_name="My Awesome Project",
        confluence_config={
            'url': 'https://mycompany.atlassian.net',
            'username': 'developer@company.com',
            'api_token': 'your-token',
            'space_key': 'DEV'
        }
    )
    
    return results

# 執行
results = asyncio.run(generate_docs())
```

## 🔧 進階配置

### MCP Server 設定

系統支援 Atlassian Remote MCP Server，可以透過 MCP 協議進行 Confluence 整合：

```python
# MCP 連線配置
mcp_config = {
    'server_command': 'atlassian-mcp-server',
    'confluence_url': 'https://your-domain.atlassian.net',
    'auth_token': 'your-api-token'
}
```

### Claude 模型配置

可以選擇不同的 Claude 模型：

```python
# 在 Agent 設定中指定模型
agent = Agent(
    name="Advanced Code Analyzer",
    model="claude-3-5-sonnet-20241022",  # 或其他 Claude 版本
    instructions="..."
)
```

### 程式碼分析客製化

```python
# 客製化檔案過濾
file_patterns = [
    "src/**/*.py",      # 只分析 src 下的 Python 檔案
    "api/**/*.js",      # API 相關的 JavaScript 檔案
    "docs/**/*.md"      # 現有文件
]

analysis = generator.analyze_codebase_function(
    project_path="./project",
    file_patterns=file_patterns
)
```

## 🧪 測試和驗證

### 執行完整測試套件

```bash
# 基本功能測試
uv run test_modern_system.py

# 特定組件測試
python -c "
import asyncio
from src.utils.code_scanner import CodeScanner
scanner = CodeScanner()
result = scanner.scan_directory('.')
print(f'掃描完成：{result[\"statistics\"][\"total_files\"]} 個檔案')
"
```

### 系統效能監控

系統提供詳細的執行log和統計資訊：

```
🔍 開始程式碼分析...
✅ 程式碼分析完成 (16 個檔案，3,104 行程式碼)
📖 開始生成文件...
✅ 文件生成完成 (5 種文件類型)
🚀 開始發布到 Confluence...
✅ Confluence 發布完成 (3 個頁面)
```

## 🔍 疑難排解

### 常見問題

1. **Claude API 連線問題**
   ```bash
   # 檢查 API Key 設定
   echo $ANTHROPIC_API_KEY
   
   # 測試 API 連線
   python -c "import anthropic; print('Claude API 可用')"
   ```

2. **MCP 協議連線失敗**
   ```bash
   # 確認 MCP Server 安裝
   which atlassian-mcp-server
   
   # 檢查連線設定
   atlassian-mcp-server --test-connection
   ```

3. **Agent SDK 問題**
   ```bash
   # 重新安裝 OpenAI Agent SDK
   uv add --upgrade openai-agents
   ```

### 效能最佳化

- **大型專案**: 使用檔案模式過濾，只分析重要檔案
- **記憶體控制**: 對於超大專案，考慮分批處理
- **網路最佳化**: 使用本地 MCP Server 減少網路延遲

## 🆚 版本比較

| 功能 | 舊版本 | 現代化版本 |
|------|--------|------------|
| AI 引擎 | 自建分析 | Claude 4 |
| 架構 | 單執行緒 | 異步多代理 |
| Confluence 整合 | 直接 API | MCP 協議 |
| 程式碼理解 | 基礎 AST | 深度語義分析 |
| 文件品質 | 模板化 | AI 生成 |
| 擴展性 | 有限 | 高度模組化 |

## 📝 開發路線圖

- **v1.0**: ✅ 基礎功能和 Claude 整合
- **v1.1**: 🔄 更多 MCP Server 支援 (Jira, GitHub 等)
- **v1.2**: 📅 圖表和視覺化自動生成
- **v1.3**: 📅 多語言深度分析支援
- **v1.4**: 📅 AI 驅動的程式碼品質建議

## 🤝 貢獻指南

我們歡迎社群貢獻！特別是：

1. **新 MCP Server 整合**
2. **程式語言支援擴展**
3. **文件模板改進**
4. **效能最佳化**

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案。

## 🙏 致謝

- **Anthropic** 提供強大的 Claude AI 模型
- **OpenAI** 提供 Agent SDK 框架  
- **Model Context Protocol** 提供標準化整合協議
- **Atlassian** 提供 Confluence API 和 MCP Server 支援

---

**🚀 體驗下一代 AI 驅動的程式碼文件生成！**

*現代化版本提供更智能的分析、更高品質的文件，以及更無縫的 Confluence 整合體驗。*
