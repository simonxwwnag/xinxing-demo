# 🚀 快速部署指南

## 一键执行部署

我已经为您准备好了所有部署文件，现在只需要执行一个命令：

```bash
cd /Users/simon/xinxing_demo
./执行部署.sh
```

**注意**: 
- 首次连接会提示接受SSH主机密钥，输入 `yes`
- 上传文件时会提示输入服务器密码，请输入您的服务器root密码
- 整个过程大约需要5-10分钟

## 部署流程说明

脚本会自动执行以下步骤：

1. ✅ **接受SSH主机密钥** - 首次连接需要
2. ✅ **上传项目文件** - 排除不需要的文件（node_modules、venv等）
3. ✅ **执行部署脚本** - 自动安装依赖、配置Nginx、启动服务
4. ✅ **创建环境变量模板** - 在服务器上创建.env文件模板

## 部署后需要您完成的操作

### 1. 配置环境变量（必须）

SSH登录服务器：
```bash
ssh root@124.220.51.21
```

编辑环境变量文件：
```bash
cd /var/www/xinxing_demo/backend
nano .env
```

填入您的实际配置值（参考本地 `env.template` 文件）：

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
```

保存后（Ctrl+O, Enter, Ctrl+X），重启服务：
```bash
systemctl restart xinxing-backend
```

### 2. 上传证书文件（可选，如果使用证书功能）

在本地执行：
```bash
scp -r "/Users/simon/Downloads/部分人员证书"/* root@124.220.51.21:/var/www/xinxing_demo/certificates/
```

### 3. 验证部署

访问以下地址验证：
- **前端**: http://124.220.51.21
- **API文档**: http://124.220.51.21/docs
- **健康检查**: http://124.220.51.21/health

## 如果遇到问题

### 问题1: SSH连接失败
```bash
# 手动接受主机密钥
ssh root@124.220.51.21
# 输入 yes 接受密钥
```

### 问题2: 上传失败
检查：
- 网络连接是否正常
- 服务器IP是否正确
- 服务器是否允许SSH连接
- 防火墙是否开放22端口

### 问题3: 部署脚本执行失败
查看服务器日志：
```bash
ssh root@124.220.51.21
tail -f /var/www/xinxing_demo/logs/backend.log
```

### 问题4: 服务无法访问
检查服务状态：
```bash
ssh root@124.220.51.21
systemctl status xinxing-backend
systemctl status nginx
```

## 常用运维命令

```bash
# 查看后端日志
ssh root@124.220.51.21 "tail -f /var/www/xinxing_demo/logs/backend.log"

# 重启后端服务
ssh root@124.220.51.21 "systemctl restart xinxing-backend"

# 重启Nginx
ssh root@124.220.51.21 "systemctl restart nginx"

# 查看服务状态
ssh root@124.220.51.21 "systemctl status xinxing-backend"
```

## 需要您提供的环境变量值

部署完成后，您需要提供以下环境变量的实际值：

1. **VIKING_AK** - 火山引擎Access Key
2. **VIKING_SK** - 火山引擎Secret Key
3. **DASHSCOPE_API_KEY** - 阿里云百炼API密钥
4. **KNOWLEDGE_COLLECTION_ID** - 知识库集合ID
5. **GROUP_SUPPLIER_DOC_ID** - 集团供应商文档ID
6. **OILFIELD_SUPPLIER_DOC_ID** - 油田供应商文档ID

这些值可以在您本地的 `.env` 文件中找到，或者从您的API服务提供商获取。

