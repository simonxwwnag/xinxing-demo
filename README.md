# 采购清单智能分析系统

一个基于FastAPI和React的采购清单智能分析演示系统，支持Excel上传、知识库规格匹配、供应商搜索、价格管理等功能。

## 功能特性

- 📊 Excel文件上传和解析
- 🔍 知识库规格匹配（带切片来源）
- 🏢 供应商信息查询（知识库 + 网络搜索）
- 💰 价格和备注管理
- ✅ 询价完成状态标记
- 🎨 科技风UI设计

## 技术栈

### 后端
- FastAPI
- Python 3.7+
- 火山引擎VikingDB知识库SDK
- 阿里云百炼API

### 前端
- React 18 + TypeScript
- Vite
- Tailwind CSS

## 环境变量配置

创建 `.env` 文件在项目根目录：

```env
# 火山引擎知识库配置
VIKING_AK=your_ak
VIKING_SK=your_sk
VIKING_HOST=api-knowledgebase.mlp.cn-beijing.volces.com

# 阿里云百炼配置
DASHSCOPE_API_KEY=your_api_key

# 知识库集合和文档ID
KNOWLEDGE_COLLECTION_ID=your_collection_id
GROUP_SUPPLIER_DOC_ID=your_group_doc_id
OILFIELD_SUPPLIER_DOC_ID=your_oilfield_doc_id
```

## 安装和运行

### 后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

后端服务将在 http://localhost:8000 启动

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端应用将在 http://localhost:3000 启动

## 项目结构

```
xinxing_demo/
├── backend/          # FastAPI后端
├── frontend/         # React前端
├── data/            # 数据存储目录
└── README.md        # 项目说明
```

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看Swagger API文档。

## 重要说明

1. **MCP WebSearch集成**：✅ 已实现通过 `qwen_agent` 调用MCP WebSearch工具
   - 使用 `qwen-agent` 库的 `Assistant` 类调用MCP服务器
   - SSE Endpoint: `https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse`
   - 需要在 `.env` 中配置 `DASHSCOPE_API_KEY`
   - 安装: `pip install qwen-agent "anyio>=4.5" "openai>=1.12.0"`
   - 详见 [QWEN_AGENT_MCP.md](QWEN_AGENT_MCP.md)

2. **知识库API**：知识库服务的API方法可能需要根据实际SDK版本调整，详见代码注释

3. **数据存储**：产品数据存储在 `data/products.json` 文件中

4. **测试MCP调用**：运行 `python backend/test_mcp.py` 测试MCP搜索功能

