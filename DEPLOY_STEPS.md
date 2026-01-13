# 一键部署执行步骤

## 方式一：使用自动化脚本（推荐）

我已经为您创建了自动化部署脚本，只需执行：

```bash
cd /Users/simon/xinxing_demo
./auto_deploy.sh
```

脚本会自动：
1. ✅ 上传项目文件到服务器
2. ✅ 在服务器上执行部署脚本
3. ✅ 创建环境变量模板文件

**注意**: 执行过程中会提示输入服务器密码，请准备好您的服务器root密码。

## 方式二：分步执行（如果自动化脚本遇到问题）

### 步骤1: 上传文件

```bash
cd /Users/simon/xinxing_demo
./upload_to_server.sh
```

### 步骤2: SSH登录并部署

```bash
ssh root@124.220.51.21
cd /var/www/xinxing_demo
chmod +x deploy.sh
./deploy.sh
```

### 步骤3: 配置环境变量

```bash
# 在服务器上执行
cd /var/www/xinxing_demo/backend
nano .env
```

填入您的实际配置值（参考 `.env.template` 文件）。

### 步骤4: 重启服务

```bash
systemctl restart xinxing-backend
```

## 需要您提供的环境变量

部署完成后，您需要编辑服务器上的 `/var/www/xinxing_demo/backend/.env` 文件，填入以下实际值：

1. **VIKING_AK** - 火山引擎Access Key
2. **VIKING_SK** - 火山引擎Secret Key  
3. **DASHSCOPE_API_KEY** - 阿里云百炼API密钥
4. **KNOWLEDGE_COLLECTION_ID** - 知识库集合ID
5. **GROUP_SUPPLIER_DOC_ID** - 集团供应商文档ID
6. **OILFIELD_SUPPLIER_DOC_ID** - 油田供应商文档ID

## 验证部署

部署完成后，访问：
- 前端: http://124.220.51.21
- API文档: http://124.220.51.21/docs
- 健康检查: http://124.220.51.21/health

