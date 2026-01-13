#!/bin/bash
# 自动化部署脚本 - 交互式执行
# 使用方法: ./auto_deploy.sh

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SERVER_IP="124.220.51.21"
SERVER_USER="root"
SERVER_PATH="/var/www/xinxing_demo"
LOCAL_PATH="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}=========================================="
echo "自动化部署脚本"
echo "==========================================${NC}"
echo ""
echo "服务器信息:"
echo "  IP: $SERVER_IP"
echo "  用户: $SERVER_USER"
echo "  路径: $SERVER_PATH"
echo ""

# 步骤1: 上传文件
echo -e "${GREEN}[步骤 1/4] 上传项目文件到服务器...${NC}"
echo -e "${YELLOW}提示: 如果提示输入密码，请输入您的服务器密码${NC}"
echo ""

read -p "按回车键开始上传..." 

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
  --exclude='*.swp' \
  --exclude='*.swo' \
  --progress \
  "$LOCAL_PATH/" \
  $SERVER_USER@$SERVER_IP:$SERVER_PATH/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 文件上传成功！${NC}"
else
    echo -e "${RED}✗ 文件上传失败，请检查网络连接和SSH配置${NC}"
    exit 1
fi

echo ""

# 步骤2: 创建环境变量模板
echo -e "${GREEN}[步骤 2/4] 创建环境变量模板文件...${NC}"
echo -e "${YELLOW}提示: 环境变量文件已创建，请稍后编辑${NC}"
echo ""

# 步骤3: 执行部署脚本
echo -e "${GREEN}[步骤 3/4] 在服务器上执行部署脚本...${NC}"
echo -e "${YELLOW}提示: 这可能需要几分钟，请耐心等待${NC}"
echo ""

ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /var/www/xinxing_demo
chmod +x deploy.sh
./deploy.sh
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 部署脚本执行成功！${NC}"
else
    echo -e "${RED}✗ 部署脚本执行失败${NC}"
    exit 1
fi

echo ""

# 步骤4: 创建环境变量文件
echo -e "${GREEN}[步骤 4/4] 配置环境变量...${NC}"
echo -e "${YELLOW}提示: 将在服务器上创建.env文件模板，您需要填入实际的API密钥${NC}"
echo ""

ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /var/www/xinxing_demo/backend

# 如果.env不存在，创建模板
if [ ! -f .env ]; then
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

# 证书文件目录（可选，默认使用 /var/www/xinxing_demo/certificates）
# CERTIFICATE_DIR=/var/www/xinxing_demo/certificates
ENVEOF
    chmod 600 .env
    echo "✓ .env文件模板已创建"
else
    echo "✓ .env文件已存在"
fi
ENDSSH

echo ""
echo -e "${GREEN}=========================================="
echo "部署完成！"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}重要: 请完成以下步骤：${NC}"
echo ""
echo "1. 编辑环境变量文件:"
echo "   ssh $SERVER_USER@$SERVER_IP"
echo "   cd /var/www/xinxing_demo/backend"
echo "   nano .env"
echo "   # 填入您的实际API密钥"
echo ""
echo "2. 重启后端服务:"
echo "   systemctl restart xinxing-backend"
echo ""
echo "3. 上传证书文件（如果需要）:"
echo "   scp -r \"/Users/simon/Downloads/部分人员证书\"/* $SERVER_USER@$SERVER_IP:/var/www/xinxing_demo/certificates/"
echo ""
echo "4. 访问应用:"
echo "   前端: http://$SERVER_IP"
echo "   API文档: http://$SERVER_IP/docs"
echo ""

