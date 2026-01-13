#!/bin/bash
# 上传项目到腾讯云服务器的脚本
# 使用方法: ./upload_to_server.sh

set -e

# ============================================
# 配置区域 - 请修改以下配置
# ============================================
SERVER_IP="124.220.51.21"  # 您的服务器IP地址
SERVER_USER="root"     # SSH用户名，通常是 root
SERVER_PATH="/var/www/xinxing_demo"  # 服务器上的项目路径
LOCAL_PATH="$(cd "$(dirname "$0")" && pwd)"  # 本地项目路径（自动获取）

# ============================================
# 颜色输出
# ============================================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ============================================
# 检查配置
# ============================================
if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}错误: 请先设置服务器IP地址${NC}"
    echo "编辑此脚本，修改 SERVER_IP 变量"
    exit 1
fi

# ============================================
# 显示配置信息
# ============================================
echo -e "${GREEN}=========================================="
echo "项目上传配置"
echo "==========================================${NC}"
echo "服务器IP: $SERVER_IP"
echo "SSH用户: $SERVER_USER"
echo "服务器路径: $SERVER_PATH"
echo "本地路径: $LOCAL_PATH"
echo ""
read -p "确认上传? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 1
fi

# ============================================
# 检查SSH连接
# ============================================
echo -e "\n${GREEN}[1/3] 检查SSH连接...${NC}"
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $SERVER_USER@$SERVER_IP echo "连接成功" 2>/dev/null; then
    echo -e "${YELLOW}SSH连接测试失败，可能需要输入密码或配置SSH密钥${NC}"
    echo "继续尝试上传..."
fi

# ============================================
# 创建服务器目录
# ============================================
echo -e "\n${GREEN}[2/3] 创建服务器目录...${NC}"
ssh $SERVER_USER@$SERVER_IP "mkdir -p $SERVER_PATH/data $SERVER_PATH/logs"

# ============================================
# 上传文件
# ============================================
echo -e "\n${GREEN}[3/3] 上传项目文件...${NC}"
echo "这可能需要几分钟，请耐心等待..."

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

# ============================================
# 完成
# ============================================
echo -e "\n${GREEN}=========================================="
echo "上传完成！"
echo "==========================================${NC}"
echo ""
echo "下一步操作："
echo "1. SSH登录服务器:"
echo "   ssh $SERVER_USER@$SERVER_IP"
echo ""
echo "2. 创建环境变量文件:"
echo "   cd $SERVER_PATH/backend"
echo "   nano .env"
echo "   # 填入您的API密钥等配置"
echo ""
echo "3. 运行部署脚本:"
echo "   cd $SERVER_PATH"
echo "   chmod +x deploy.sh"
echo "   ./deploy.sh"
echo ""
echo -e "${YELLOW}提示: 环境变量文件(.env)包含敏感信息，不会自动上传${NC}"
echo "     请在服务器上手动创建并配置"
echo ""

