# 快速部署指南 - 腾讯云服务器

## 服务器信息
- **IP地址**: 124.220.51.21
- **项目路径**: /var/www/xinxing_demo

## 快速部署步骤

### 步骤1：上传项目文件到服务器

#### 方式A：使用提供的上传脚本（推荐）

```bash
# 在本地项目目录执行
cd /Users/simon/xinxing_demo

# 编辑上传脚本（已配置IP，可直接使用）
# 或直接运行（已配置好IP地址）
./upload_to_server.sh
```

#### 方式B：使用rsync手动上传

```bash
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
  root@124.220.51.21:/var/www/xinxing_demo/
```

#### 方式C：使用SCP上传（如果rsync不可用）

```bash
# 先压缩项目（排除不需要的文件）
cd /Users/simon
tar --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='.env' \
    --exclude='backend/test_*.py' \
    --exclude='backend/analyze_*.py' \
    -czf xinxing_demo.tar.gz \
    xinxing_demo

# 上传压缩包
scp xinxing_demo.tar.gz root@124.220.51.21:/var/www/

# SSH登录服务器解压
ssh root@124.220.51.21
cd /var/www
tar -xzf xinxing_demo.tar.gz
```

### 步骤2：SSH登录服务器

```bash
ssh root@124.220.51.21
```

### 步骤3：运行部署脚本

```bash
cd /var/www/xinxing_demo
chmod +x deploy.sh
./deploy.sh
```

部署脚本会自动完成：
- ✅ 安装系统依赖（Python、Node.js、Nginx等）
- ✅ 创建Python虚拟环境并安装依赖
- ✅ 构建前端项目
- ✅ 配置Nginx
- ✅ 配置Systemd服务
- ✅ 启动服务

### 步骤4：配置环境变量

部署脚本运行后，需要配置环境变量：

```bash
cd /var/www/xinxing_demo/backend
nano .env
```

填入以下配置（替换为您的实际值）：

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

# 证书文件目录（可选，默认使用 /var/www/xinxing_demo/certificates）
# CERTIFICATE_DIR=/var/www/xinxing_demo/certificates
```

保存后（Ctrl+O, Enter, Ctrl+X），重启后端服务：

```bash
systemctl restart xinxing-backend
```

### 步骤5：上传证书文件（如果使用证书功能）

```bash
# 在本地执行
scp -r "/Users/simon/Downloads/部分人员证书"/* root@124.220.51.21:/var/www/xinxing_demo/certificates/
```

### 步骤6：验证部署

访问以下地址验证部署：

- **前端地址**: http://124.220.51.21
- **API文档**: http://124.220.51.21/docs
- **健康检查**: http://124.220.51.21/health

## 常用运维命令

```bash
# 查看后端服务状态
systemctl status xinxing-backend

# 查看后端日志
tail -f /var/www/xinxing_demo/logs/backend.log

# 重启后端服务
systemctl restart xinxing-backend

# 重启Nginx
systemctl restart nginx

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log
```

## 防火墙配置

确保服务器防火墙开放了80端口（HTTP）：

```bash
# Ubuntu/Debian
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable

# CentOS
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ssh
firewall-cmd --reload
```

## 故障排查

### 如果无法访问

1. **检查服务状态**:
   ```bash
   systemctl status xinxing-backend
   systemctl status nginx
   ```

2. **检查端口监听**:
   ```bash
   netstat -tlnp | grep 8000  # 后端端口
   netstat -tlnp | grep 80    # Nginx端口
   ```

3. **检查防火墙**:
   ```bash
   # Ubuntu/Debian
   ufw status
   
   # CentOS
   firewall-cmd --list-all
   ```

4. **检查日志**:
   ```bash
   tail -f /var/www/xinxing_demo/logs/backend.log
   tail -f /var/log/nginx/error.log
   ```

## 下一步

部署成功后，您可以：

1. **配置域名**（如果有）：
   - 修改 `/etc/nginx/sites-available/xinxing_demo` 中的 `server_name`
   - 重启Nginx: `systemctl restart nginx`

2. **配置HTTPS**（推荐）：
   ```bash
   apt-get install -y certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

3. **设置自动备份**（可选）：
   - 定期备份 `/var/www/xinxing_demo/data` 目录

## 需要帮助？

如果遇到问题，请检查：
- [ ] 环境变量是否正确配置
- [ ] 服务是否正常运行
- [ ] 防火墙是否开放端口
- [ ] 日志中是否有错误信息

