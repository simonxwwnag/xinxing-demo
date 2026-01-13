# 腾讯云轻量服务器部署指南

本文档提供在腾讯云轻量服务器上部署采购清单智能分析系统的详细步骤。

## 前置准备

### 1. 服务器信息收集

在开始部署前，请准备以下信息：

- **服务器IP地址**: 您的腾讯云服务器公网IP
- **SSH登录方式**: 
  - 密码登录：用户名和密码
  - 密钥登录：SSH私钥文件路径
- **域名（可选）**: 如果已绑定域名，请提供域名地址
- **环境变量配置**: 
  - 火山引擎API密钥（VIKING_AK, VIKING_SK）
  - 阿里云百炼API密钥（DASHSCOPE_API_KEY）
  - 知识库集合ID和文档ID

### 2. 服务器要求

- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **内存**: 至少 2GB（推荐 4GB+）
- **磁盘**: 至少 20GB 可用空间
- **网络**: 可访问外网（用于下载依赖和API调用）

## 部署方式

### 方式一：使用部署脚本（推荐）

#### 步骤1：上传项目到服务器

**选项A：使用Git（推荐）**

```bash
# 在服务器上执行
cd /var/www
git clone <your-repo-url> xinxing_demo
cd xinxing_demo
```

**选项B：使用SCP上传**

```bash
# 在本地执行
scp -r /Users/simon/xinxing_demo root@<服务器IP>:/var/www/
```

**选项C：使用rsync（推荐，可排除不需要的文件）**

```bash
# 在本地执行
rsync -av --exclude='node_modules' --exclude='venv' --exclude='__pycache__' \
    --exclude='.git' --exclude='*.log' \
    /Users/simon/xinxing_demo/ root@<服务器IP>:/var/www/xinxing_demo/
```

#### 步骤2：运行部署脚本

```bash
# SSH登录服务器
ssh root@<服务器IP>

# 进入项目目录
cd /var/www/xinxing_demo

# 给脚本执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

脚本会自动完成：
- 系统更新和依赖安装
- Python虚拟环境配置
- Node.js安装和前端构建
- Nginx配置
- Systemd服务配置
- 服务启动

### 方式二：手动部署

#### 步骤1：安装基础软件

```bash
# Ubuntu/Debian
apt-get update
apt-get install -y python3 python3-pip python3-venv git curl wget nginx

# CentOS/RHEL
yum update -y
yum install -y python3 python3-pip git curl wget nginx
```

#### 步骤2：安装Node.js

```bash
# 安装Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs  # Ubuntu/Debian
# 或
yum install -y nodejs  # CentOS
```

#### 步骤3：配置后端

```bash
cd /var/www/xinxing_demo/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env  # 如果有示例文件
nano .env  # 编辑环境变量
```

#### 步骤4：配置前端

```bash
cd /var/www/xinxing_demo/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

#### 步骤5：配置Nginx

创建配置文件 `/etc/nginx/sites-available/xinxing_demo`:

```nginx
server {
    listen 80;
    server_name <您的域名或IP>;  # 替换为实际值

    # 前端静态文件
    root /var/www/xinxing_demo/frontend/dist;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 增加超时时间
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

启用配置：

```bash
ln -s /etc/nginx/sites-available/xinxing_demo /etc/nginx/sites-enabled/
nginx -t  # 测试配置
systemctl restart nginx
```

#### 步骤6：配置Systemd服务

创建服务文件 `/etc/systemd/system/xinxing-backend.service`:

```ini
[Unit]
Description=Xinxing Demo Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/xinxing_demo/backend
Environment="PATH=/var/www/xinxing_demo/backend/venv/bin"
ExecStart=/var/www/xinxing_demo/backend/venv/bin/python /var/www/xinxing_demo/backend/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/www/xinxing_demo/logs/backend.log
StandardError=append:/var/www/xinxing_demo/logs/backend.log

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
systemctl daemon-reload
systemctl enable xinxing-backend
systemctl start xinxing-backend
systemctl status xinxing-backend
```

## 环境变量配置

在 `/var/www/xinxing_demo/backend/.env` 文件中配置：

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

# 证书文件目录（可选，默认使用项目目录下的certificates文件夹）
# CERTIFICATE_DIR=/var/www/xinxing_demo/certificates
```

## 证书文件目录配置

如果您的项目需要使用证书文件功能，需要：

1. **创建证书目录**：
   ```bash
   mkdir -p /var/www/xinxing_demo/certificates
   ```

2. **上传证书文件**：
   将证书文件（PDF、图片等）上传到该目录：
   ```bash
   # 使用SCP上传
   scp -r /本地证书目录/* root@<服务器IP>:/var/www/xinxing_demo/certificates/
   ```

3. **配置环境变量（可选）**：
   如果证书文件不在默认位置，可以在 `.env` 文件中设置：
   ```env
   CERTIFICATE_DIR=/path/to/your/certificates
   ```

4. **设置权限**：
   ```bash
   chown -R www-data:www-data /var/www/xinxing_demo/certificates
   chmod -R 755 /var/www/xinxing_demo/certificates
   ```

## 防火墙配置

确保开放必要的端口：

```bash
# Ubuntu/Debian (ufw)
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable

# CentOS (firewalld)
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ssh
firewall-cmd --reload
```

## 验证部署

1. **检查服务状态**:
   ```bash
   systemctl status xinxing-backend
   systemctl status nginx
   ```

2. **检查日志**:
   ```bash
   tail -f /var/www/xinxing_demo/logs/backend.log
   tail -f /var/log/nginx/error.log
   ```

3. **访问测试**:
   - 前端: `http://<服务器IP>`
   - API文档: `http://<服务器IP>/docs`
   - 健康检查: `http://<服务器IP>/health`

## 常用运维命令

```bash
# 重启后端服务
systemctl restart xinxing-backend

# 重启Nginx
systemctl restart nginx

# 查看后端日志
tail -f /var/www/xinxing_demo/logs/backend.log

# 查看Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 停止服务
systemctl stop xinxing-backend

# 启动服务
systemctl start xinxing-backend

# 查看服务状态
systemctl status xinxing-backend
```

## HTTPS配置（可选）

如果需要配置HTTPS，可以使用Let's Encrypt免费证书：

```bash
# 安装Certbot
apt-get install -y certbot python3-certbot-nginx  # Ubuntu/Debian
# 或
yum install -y certbot python3-certbot-nginx  # CentOS

# 获取证书（替换为您的域名）
certbot --nginx -d yourdomain.com

# 自动续期
certbot renew --dry-run
```

## 故障排查

### 1. 后端服务无法启动

```bash
# 检查日志
journalctl -u xinxing-backend -n 50

# 检查Python环境
cd /var/www/xinxing_demo/backend
source venv/bin/activate
python --version
pip list
```

### 2. Nginx 502错误

- 检查后端服务是否运行: `systemctl status xinxing-backend`
- 检查端口8000是否监听: `netstat -tlnp | grep 8000`
- 检查Nginx错误日志: `tail -f /var/log/nginx/error.log`

### 3. 前端页面空白

- 检查前端构建文件: `ls -la /var/www/xinxing_demo/frontend/dist`
- 检查Nginx配置中的root路径是否正确
- 检查浏览器控制台错误信息

### 4. API请求超时

- 检查Nginx超时配置（已在配置中设置为300秒）
- 检查后端日志查看是否有错误
- 检查网络连接和API密钥配置

## 更新部署

当代码更新后，重新部署：

```bash
# 1. 拉取最新代码（如果使用Git）
cd /var/www/xinxing_demo
git pull

# 2. 更新后端依赖（如果有变化）
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 3. 重新构建前端
cd ../frontend
npm install
npm run build

# 4. 重启服务
systemctl restart xinxing-backend
systemctl restart nginx
```

## 安全建议

1. **修改默认端口**: 考虑修改SSH默认端口22
2. **使用密钥登录**: 禁用密码登录，使用SSH密钥
3. **配置防火墙**: 只开放必要端口
4. **定期更新**: 保持系统和依赖包更新
5. **备份数据**: 定期备份 `/var/www/xinxing_demo/data` 目录
6. **限制CORS**: 生产环境修改 `backend/main.py` 中的CORS配置，限制允许的域名

## 需要的信息清单

为了更好的协助您部署，请提供：

- [ ] 服务器IP地址
- [ ] SSH登录方式（密码/密钥）
- [ ] 服务器操作系统版本
- [ ] 是否已绑定域名
- [ ] 环境变量配置（API密钥等）
- [ ] 是否需要HTTPS
- [ ] 服务器内存和磁盘大小

提供这些信息后，我可以为您生成更具体的部署命令和配置。

