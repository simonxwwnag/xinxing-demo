# 部署文件处理指南

本文档说明哪些文件需要上传到服务器，哪些不需要，以及如何处理。

## 📦 不需要上传的文件（会在服务器上重新生成）

### 1. Python虚拟环境
- ❌ `backend/venv/` - **不要上传**
- ✅ 服务器上会重新创建虚拟环境并安装依赖

### 2. Node.js依赖
- ❌ `frontend/node_modules/` - **不要上传**
- ✅ 服务器上会运行 `npm install` 重新安装

### 3. Python缓存文件
- ❌ `**/__pycache__/` - **不要上传**
- ✅ 服务器上运行时会自动生成

### 4. 日志文件
- ❌ `*.log` - **不要上传**
  - `backend.log`
  - `frontend.log`
  - `backend/backend.log`
  - `backend/test_output.log`
- ✅ 服务器上运行时会自动生成

### 5. 测试文件（可选）
- ⚠️ `backend/test_*.py` - **可选上传**
  - 生产环境通常不需要测试文件
  - 如果需要调试，可以上传

### 6. 分析脚本（可选）
- ⚠️ `backend/analyze_*.py` - **可选上传**
  - `analyze_output.py`
  - `analyze_timing.py`
  - `quick_analyze.py`
- ✅ 这些是开发调试工具，生产环境不需要

## 🔐 需要单独处理的文件

### 1. 环境变量文件（重要！）
- ❌ `.env` - **不要上传**（包含敏感信息）
- ✅ **需要在服务器上手动创建**

在服务器上创建 `/var/www/xinxing_demo/backend/.env`：

```bash
# 在服务器上执行
cd /var/www/xinxing_demo/backend
nano .env
```

内容示例：
```env
# 火山引擎知识库配置
VIKING_AK=your_ak_here
VIKING_SK=your_sk_here
VIKING_HOST=api-knowledgebase.mlp.cn-beijing.volces.com

# 阿里云百炼配置
DASHSCOPE_API_KEY=your_api_key_here

# 知识库集合和文档ID
KNOWLEDGE_COLLECTION_ID=your_collection_id
GROUP_SUPPLIER_DOC_ID=your_group_doc_id
OILFIELD_SUPPLIER_DOC_ID=your_oilfield_doc_id
```

### 2. 数据文件（可选）
- ⚠️ `data/*.json` - **可选上传**
  - `data/products.json` - 产品数据（如果已有数据需要保留）
  - `data/projects.json` - 项目数据（如果已有数据需要保留）
- ✅ 如果数据为空或可以重新生成，可以不传
- ✅ 如果需要保留现有数据，需要上传

### 3. 证书文件（如果使用证书功能）
- ⚠️ 证书文件目录 - **需要单独上传**
  - 本地路径：`/Users/simon/Downloads/部分人员证书`（示例）
  - 服务器路径：`/var/www/xinxing_demo/certificates`（默认）
- ✅ 使用SCP或rsync上传证书文件：
  ```bash
  scp -r /本地证书目录/* root@<服务器IP>:/var/www/xinxing_demo/certificates/
  ```
- ✅ 如果证书文件在其他位置，可在 `.env` 中配置 `CERTIFICATE_DIR` 环境变量

## ✅ 必须上传的文件

### 1. 源代码文件
- ✅ `backend/` 目录下的所有 `.py` 文件（除了测试文件）
- ✅ `frontend/src/` 目录下的所有文件
- ✅ `frontend/` 目录下的配置文件：
  - `package.json`
  - `package-lock.json`
  - `vite.config.ts`
  - `tsconfig.json`
  - `tailwind.config.js`
  - `postcss.config.js`
  - `index.html`

### 2. 配置文件
- ✅ `backend/requirements.txt` - Python依赖列表
- ✅ `backend/main.py` - 主程序入口
- ✅ `backend/utils/config.py` - 配置读取

### 3. 文档文件（可选但推荐）
- ✅ `README.md` - 项目说明
- ✅ `DEPLOY.md` - 部署文档
- ✅ 其他 `.md` 文档文件

## 🚀 推荐的上传方式

### 方式一：使用 rsync（推荐，自动排除不需要的文件）

```bash
# 在本地执行
rsync -av \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.log' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='backend/test_*.py' \
  --exclude='backend/analyze_*.py' \
  --exclude='backend/quick_analyze.py' \
  --exclude='.DS_Store' \
  --exclude='.vscode' \
  --exclude='.idea' \
  /Users/simon/xinxing_demo/ \
  root@<服务器IP>:/var/www/xinxing_demo/
```

### 方式二：使用 Git（如果项目在Git仓库中）

```bash
# 在服务器上执行
cd /var/www
git clone <your-repo-url> xinxing_demo
cd xinxing_demo
```

### 方式三：使用 tar 压缩（适合一次性上传）

```bash
# 在本地执行 - 创建压缩包（排除不需要的文件）
tar --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='.env' \
    --exclude='backend/test_*.py' \
    --exclude='backend/analyze_*.py' \
    -czf xinxing_demo.tar.gz \
    -C /Users/simon xinxing_demo

# 上传压缩包
scp xinxing_demo.tar.gz root@<服务器IP>:/var/www/

# 在服务器上解压
ssh root@<服务器IP>
cd /var/www
tar -xzf xinxing_demo.tar.gz
```

## 📋 部署前检查清单

上传文件前，请确认：

- [ ] 已排除 `venv/` 目录
- [ ] 已排除 `node_modules/` 目录
- [ ] 已排除 `.env` 文件（敏感信息）
- [ ] 已排除 `*.log` 日志文件
- [ ] 已包含 `requirements.txt`
- [ ] 已包含 `package.json`
- [ ] 已包含所有源代码文件
- [ ] 已准备好环境变量配置（在服务器上手动创建）

## 🔄 部署后需要做的事情

1. **创建环境变量文件**
   ```bash
   cd /var/www/xinxing_demo/backend
   nano .env
   # 粘贴您的环境变量配置
   ```

2. **创建必要的目录**
   ```bash
   mkdir -p /var/www/xinxing_demo/data
   mkdir -p /var/www/xinxing_demo/logs
   ```

3. **设置文件权限**
   ```bash
   chown -R www-data:www-data /var/www/xinxing_demo
   chmod 600 /var/www/xinxing_demo/backend/.env  # 保护环境变量文件
   ```

4. **初始化数据文件（如果需要）**
   ```bash
   # 如果 data 目录为空，创建空文件
   echo '[]' > /var/www/xinxing_demo/data/products.json
   echo '[]' > /var/www/xinxing_demo/data/projects.json
   ```

## 💡 快速上传脚本

创建一个本地脚本 `upload_to_server.sh`：

```bash
#!/bin/bash
# 上传项目到服务器

SERVER_IP="your_server_ip"  # 替换为您的服务器IP
SERVER_USER="root"           # 替换为您的SSH用户名
SERVER_PATH="/var/www/xinxing_demo"

echo "开始上传项目到服务器..."

rsync -av \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.log' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='backend/test_*.py' \
  --exclude='backend/analyze_*.py' \
  --exclude='backend/quick_analyze.py' \
  --exclude='.DS_Store' \
  --exclude='.vscode' \
  --exclude='.idea' \
  --progress \
  /Users/simon/xinxing_demo/ \
  ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/

echo "上传完成！"
echo "请在服务器上："
echo "1. 创建 .env 文件: cd ${SERVER_PATH}/backend && nano .env"
echo "2. 运行部署脚本: cd ${SERVER_PATH} && ./deploy.sh"
```

使用方法：
```bash
chmod +x upload_to_server.sh
# 编辑脚本，填入服务器IP
nano upload_to_server.sh
# 运行
./upload_to_server.sh
```

