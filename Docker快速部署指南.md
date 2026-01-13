# Docker快速部署指南

## ✅ 优势

使用Docker部署的优势：
1. **环境隔离** - 不污染系统环境
2. **一键部署** - 自动构建和启动所有服务
3. **易于维护** - 更新代码只需重新构建
4. **一致性** - 开发和生产环境完全一致
5. **外部访问** - 自动配置Nginx，通过80端口访问

## 🚀 快速开始

### 步骤1: 上传Docker相关文件到服务器

在本地执行：

```bash
# 上传Docker配置文件
scp docker-compose.yml Dockerfile.backend Dockerfile.frontend .dockerignore root@124.220.51.21:/root/xinxing_demo/

# 上传nginx配置
scp -r docker/ root@124.220.51.21:/root/xinxing_demo/

# 上传部署脚本
scp docker一键部署.sh root@124.220.51.21:/root/xinxing_demo/
```

### 步骤2: SSH登录并执行部署

```bash
ssh root@124.220.51.21
cd /root/xinxing_demo
chmod +x docker一键部署.sh
./docker一键部署.sh
```

脚本会自动：
- ✅ 安装Docker和Docker Compose
- ✅ 检查必要文件
- ✅ 创建必要目录
- ✅ 构建Docker镜像
- ✅ 启动所有服务

### 步骤3: 配置环境变量

部署脚本会创建.env模板，需要填入实际值：

```bash
cd /root/xinxing_demo/backend
nano .env
```

填入您的实际API密钥，然后重启后端服务：

```bash
cd /root/xinxing_demo
docker-compose restart backend
```

### 步骤4: 验证部署

访问：
- **前端**: http://124.220.51.21
- **API文档**: http://124.220.51.21/docs
- **健康检查**: http://124.220.51.21/health

## 📋 常用命令

### 查看服务状态
```bash
cd /root/xinxing_demo
docker-compose ps
```

### 查看日志
```bash
# 查看所有日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 停止服务
```bash
docker-compose down
```

### 更新代码后重新部署
```bash
cd /root/xinxing_demo
docker-compose down
docker-compose up -d --build
```

## 🔧 故障排查

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

### 进入容器调试
```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh
```

### 重新构建
```bash
# 强制重新构建
docker-compose build --no-cache

# 重新启动
docker-compose up -d
```

## 📁 文件结构

```
/root/xinxing_demo/
├── docker-compose.yml      # Docker Compose配置
├── Dockerfile.backend      # 后端Dockerfile
├── Dockerfile.frontend     # 前端Dockerfile
├── .dockerignore           # Docker忽略文件
├── docker/
│   └── nginx.conf          # Nginx配置
├── backend/
│   ├── .env                # 环境变量（需要配置）
│   └── ...                 # 后端代码
├── frontend/
│   └── ...                 # 前端代码
├── data/                   # 数据目录（持久化）
├── logs/                   # 日志目录（持久化）
└── certificates/           # 证书目录（持久化）
```

## ✅ 部署检查清单

- [ ] Docker和Docker Compose已安装
- [ ] Docker相关文件已上传
- [ ] 环境变量已配置（.env文件）
- [ ] 证书文件已上传到certificates目录
- [ ] Docker服务已启动
- [ ] 可以通过IP访问前端
- [ ] API文档可以访问

## 🎉 完成！

部署完成后，您的应用就可以通过 http://124.220.51.21 访问了！

