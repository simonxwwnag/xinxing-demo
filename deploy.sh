#!/bin/bash
# 腾讯云轻量服务器部署脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "开始部署采购清单智能分析系统"
echo "=========================================="

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}警告: 建议使用root用户运行此脚本，某些操作可能需要sudo权限${NC}"
fi

# 1. 更新系统
echo -e "\n${GREEN}[1/8] 更新系统包...${NC}"
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get upgrade -y
elif command -v yum &> /dev/null; then
    yum update -y
else
    echo -e "${YELLOW}未检测到包管理器，跳过系统更新${NC}"
fi

# 2. 安装基础依赖
echo -e "\n${GREEN}[2/8] 安装基础依赖...${NC}"
if command -v apt-get &> /dev/null; then
    apt-get install -y python3 python3-pip python3-venv git curl wget nginx
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip git curl wget nginx
fi

# 3. 安装Node.js (如果未安装)
echo -e "\n${GREEN}[3/8] 检查并安装Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo "安装Node.js 18.x..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    if command -v apt-get &> /dev/null; then
        apt-get install -y nodejs
    elif command -v yum &> /dev/null; then
        yum install -y nodejs
    fi
else
    echo "Node.js 已安装: $(node --version)"
fi

# 4. 创建项目目录
echo -e "\n${GREEN}[4/8] 创建项目目录...${NC}"
PROJECT_DIR="/var/www/xinxing_demo"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/data
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/certificates  # 证书文件目录

# 5. 复制项目文件（假设当前在项目根目录）
echo -e "\n${GREEN}[5/8] 复制项目文件...${NC}"
if [ -d "$PROJECT_DIR/backend" ]; then
    echo "项目已存在，备份旧版本..."
    mv $PROJECT_DIR $PROJECT_DIR.backup.$(date +%Y%m%d_%H%M%S)
fi

# 复制文件（排除node_modules, venv等）
# 注意：如果使用rsync上传，这部分可以注释掉
# 这里假设文件已经通过其他方式上传到服务器
if [ ! -d "$PROJECT_DIR/backend" ]; then
    echo "项目文件未找到，请先上传项目文件到 $PROJECT_DIR"
    echo "可以使用以下命令上传："
    echo "  rsync -av --exclude='node_modules' --exclude='venv' --exclude='__pycache__' \\"
    echo "    --exclude='.git' --exclude='*.log' --exclude='.env' \\"
    echo "    --exclude='backend/test_*.py' --exclude='backend/analyze_*.py' \\"
    echo "    /本地路径/xinxing_demo/ $PROJECT_DIR/"
    exit 1
fi

# 6. 设置后端环境
echo -e "\n${GREEN}[6/8] 设置后端环境...${NC}"
cd $PROJECT_DIR/backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: 未找到.env文件，请手动创建并配置环境变量${NC}"
    echo "创建.env文件..."
    cat > .env << 'ENVEOF'
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
ENVEOF
    echo -e "${RED}请编辑 $PROJECT_DIR/backend/.env 文件，填入正确的配置信息${NC}"
    echo "使用命令: nano $PROJECT_DIR/backend/.env"
    chmod 600 .env  # 保护环境变量文件
fi

# 7. 构建前端
echo -e "\n${GREEN}[7/8] 构建前端...${NC}"
cd $PROJECT_DIR/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 8. 配置Nginx
echo -e "\n${GREEN}[8/8] 配置Nginx...${NC}"
NGINX_CONFIG="/etc/nginx/sites-available/xinxing_demo"

# 创建Nginx配置
cat > $NGINX_CONFIG << 'EOF'
server {
    listen 80;
    server_name _;  # 替换为您的域名或IP

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
        
        # 增加超时时间（用于长时间运行的API）
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
EOF

# 创建符号链接（如果使用sites-enabled）
if [ -d "/etc/nginx/sites-enabled" ]; then
    ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/
    # 删除默认配置
    rm -f /etc/nginx/sites-enabled/default
fi

# 测试Nginx配置
nginx -t

# 9. 创建systemd服务文件
echo -e "\n${GREEN}[9/9] 创建systemd服务...${NC}"
SERVICE_FILE="/etc/systemd/system/xinxing-backend.service"

cat > $SERVICE_FILE << EOF
[Unit]
Description=Xinxing Demo Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/venv/bin"
ExecStart=$PROJECT_DIR/backend/venv/bin/python $PROJECT_DIR/backend/main.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/backend.log
StandardError=append:$PROJECT_DIR/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

# 设置文件权限
chown -R www-data:www-data $PROJECT_DIR
chmod +x $PROJECT_DIR/backend/main.py

# 10. 启动服务
echo -e "\n${GREEN}启动服务...${NC}"
systemctl daemon-reload
systemctl enable xinxing-backend
systemctl restart xinxing-backend
systemctl restart nginx

# 检查服务状态
echo -e "\n${GREEN}检查服务状态...${NC}"
sleep 2
systemctl status xinxing-backend --no-pager -l

echo -e "\n${GREEN}=========================================="
echo "部署完成！"
echo "==========================================${NC}"
echo ""
echo "服务信息："
echo "  - 前端地址: http://$(hostname -I | awk '{print $1}')"
echo "  - 后端API: http://$(hostname -I | awk '{print $1}')/api"
echo "  - API文档: http://$(hostname -I | awk '{print $1}')/docs"
echo ""
echo "常用命令："
echo "  - 查看后端日志: tail -f $PROJECT_DIR/logs/backend.log"
echo "  - 重启后端服务: systemctl restart xinxing-backend"
echo "  - 重启Nginx: systemctl restart nginx"
echo "  - 查看服务状态: systemctl status xinxing-backend"
echo ""
echo -e "${YELLOW}重要提醒：${NC}"
echo "1. 请确保已配置.env文件（包含API密钥等）"
echo "2. 如果使用域名，请修改Nginx配置中的server_name"
echo "3. 如需HTTPS，请配置SSL证书"
echo "4. 如果使用证书功能，请上传证书文件到: $PROJECT_DIR/certificates"
echo "   或配置 CERTIFICATE_DIR 环境变量指定其他路径"
echo ""

