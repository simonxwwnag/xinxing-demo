# Docker部署指南

使用Docker部署可以更好地管理依赖、环境隔离，并且部署更简单。

## 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+

## 快速部署

### 步骤1: 安装Docker和Docker Compose

在服务器上执行：

```bash
# 安装Docker
curl -fsSL https://get.docker.com | bash

# 启动Docker服务
systemctl start docker
systemctl enable docker

# 安装Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 步骤2: 准备项目文件

确保项目已上传到服务器 `/root/xinxing_demo/`，并且包含：
- `docker-compose.yml`
- `Dockerfile.backend`
- `Dockerfile.frontend`
- `docker/nginx.conf`
- `backend/.env` (环境变量文件)

### 步骤3: 配置环境变量

```bash
cd /root/xinxing_demo/backend

# 创建.env文件（如果还没有）
nano .env
```

填入您的实际配置：

```env
# 火山引擎知识库配置
VIKING_AK=你的实际AK
VIKING_SK=你的实际SK
VIKING_HOST=api-knowledgebase.mlp.cn-beijing.volces.com

# 阿里云百炼配置
DASHSCOPE_API_KEY=你的实际API密钥

# 知识库集合和文档ID
KNOWLEDGE_COLLECTION_ID=你的集合ID
GROUP_SUPPLIER_DOC_ID=你的文档ID
OILFIELD_SUPPLIER_DOC_ID=你的文档ID

# 证书文件目录（Docker中会自动挂载）
# CERTIFICATE_DIR=/app/certificates
```

### 步骤4: 构建和启动

```bash
cd /root/xinxing_demo

# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 步骤5: 验证部署

访问：
- **前端**: http://124.220.51.21
- **API文档**: http://124.220.51.21/docs
- **健康检查**: http://124.220.51.21/health

## 常用命令

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart frontend
```

### 停止服务
```bash
docker-compose down
```

### 更新代码后重新部署
```bash
# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### 进入容器
```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh
```

## 数据持久化

以下目录会挂载到宿主机，数据会持久保存：
- `./data` - 产品数据
- `./logs` - 日志文件
- `./certificates` - 证书文件
- `./backend/.env` - 环境变量

## 防火墙配置

确保开放80端口：

```bash
# firewalld
firewall-cmd --permanent --add-service=http
firewall-cmd --reload

# 或ufw
ufw allow 80/tcp
```

## 故障排查

### 查看容器日志
```bash
docker-compose logs backend
docker-compose logs frontend
```

### 检查容器状态
```bash
docker-compose ps
docker ps -a
```

### 重新构建
```bash
# 强制重新构建
docker-compose build --no-cache

# 重新启动
docker-compose up -d
```

### 清理并重新开始
```bash
# 停止并删除容器
docker-compose down

# 删除镜像（可选）
docker-compose down --rmi all

# 重新构建和启动
docker-compose up -d --build
```

## 优势

使用Docker部署的优势：
1. ✅ **环境隔离** - 不污染系统环境
2. ✅ **易于部署** - 一键启动所有服务
3. ✅ **易于维护** - 更新代码只需重新构建
4. ✅ **易于扩展** - 可以轻松添加更多服务
5. ✅ **一致性** - 开发和生产环境一致

## 生产环境建议

1. **使用.env文件管理敏感信息**（已配置）
2. **配置日志轮转**（Docker自动管理）
3. **设置资源限制**（在docker-compose.yml中添加）
4. **配置健康检查**（已配置）
5. **使用HTTPS**（可以添加nginx-proxy或traefik）

## 更新部署脚本

如果需要更新代码：

```bash
cd /root/xinxing_demo

# 拉取最新代码（如果使用Git）
git pull

# 重新构建并启动
docker-compose up -d --build
```

