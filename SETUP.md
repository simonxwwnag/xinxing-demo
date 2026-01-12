# 项目设置指南

## 快速开始

### 1. 环境要求

- Python 3.7+
- Node.js 16+
- npm 或 yarn

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example ../.env
# 编辑 .env 文件，填入你的配置信息

# 运行后端服务
# 方式1：从backend目录运行
python main.py

# 方式2：从项目根目录运行（推荐）
cd ..
python -m backend.main

# 方式3：使用启动脚本（Linux/Mac）
../start_backend.sh
```

后端服务将在 http://localhost:8000 启动

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 http://localhost:3000 启动

### 4. 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# 火山引擎知识库配置
VIKING_AK=your_ak_here
VIKING_SK=your_sk_here
VIKING_HOST=api-knowledgebase.mlp.cn-beijing.volces.com

# 阿里云百炼配置
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 知识库集合和文档ID
KNOWLEDGE_COLLECTION_ID=your_collection_id_here
GROUP_SUPPLIER_DOC_ID=your_group_supplier_doc_id_here
OILFIELD_SUPPLIER_DOC_ID=your_oilfield_supplier_doc_id_here
```

## Excel文件格式要求

Excel文件必须包含以下字段（严格匹配字段名）：

- 项目编码
- 项目名称
- 项目特征
- 计量单位
- 工程量

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看Swagger API文档。

## 注意事项

1. **MCP WebSearch集成**：网络搜索功能需要配置MCP WebSearch工具，详见 `MCP_INTEGRATION.md`

2. **知识库API**：知识库服务的API方法可能需要根据实际SDK版本调整，详见代码注释

3. **数据存储**：产品数据存储在 `data/products.json` 文件中

4. **CORS配置**：当前配置允许所有来源，生产环境应限制具体域名

## 故障排查

### 后端问题

- 检查Python版本是否符合要求
- 确认所有依赖已正确安装
- 检查环境变量配置是否正确
- 查看控制台错误信息

### 前端问题

- 检查Node.js版本是否符合要求
- 清除node_modules并重新安装
- 检查后端服务是否正常运行
- 查看浏览器控制台错误信息

### 知识库连接问题

- 确认AK/SK配置正确
- 检查网络连接
- 验证知识库集合ID和文档ID是否正确
- 查看后端日志中的错误信息

