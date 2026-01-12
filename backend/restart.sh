#!/bin/bash
# 重启后端服务脚本

echo "正在停止现有后端进程..."
pkill -f "python main.py" || true
sleep 2

echo "正在启动后端服务..."
cd "$(dirname "$0")"
python main.py &
sleep 3

if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ 后端服务已成功启动"
else
    echo "❌ 后端服务启动失败，请检查日志"
fi

