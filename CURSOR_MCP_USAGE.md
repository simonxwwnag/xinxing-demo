# Cursor MCP WebSearch 使用指南

## 配置状态

✅ MCP服务器已在Cursor中配置完成

配置信息：
```json
{
  "mcpServers": {
    "type": "sse",
    "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
    "headers": {
      "Authorization": "Bearer ${DASHSCOPE_API_KEY}"
    }
  }
}
```

## 调用方式

### 方式1：通过Cursor AI助手调用（推荐）

在Cursor中，可以通过AI助手来调用MCP工具：

1. **在Cursor中打开AI助手**
2. **输入请求**：
   ```
   请使用MCP工具 bailian_web_search 搜索"钢管 供应商"，返回5个结果
   ```
3. **AI助手会调用MCP工具并返回结果**
4. **将结果复制到系统中**

### 方式2：手动调用MCP工具

如果Cursor支持直接调用MCP工具：

1. 在Cursor中找到MCP工具面板
2. 选择 `bailian_web_search` 工具
3. 输入参数：
   - query: "钢管 供应商"
   - count: 5
4. 执行并获取结果

### 方式3：通过API端点手动输入（当前实现）

系统提供了API端点，可以手动输入搜索结果：

**API端点**: `POST /api/search/suppliers`

**请求体**:
```json
{
  "product_name": "钢管",
  "limit": 5
}
```

**响应格式**:
```json
{
  "suppliers": [
    {
      "name": "供应商名称",
      "source": "web_search",
      "url": "https://...",
      "description": "供应商描述"
    }
  ]
}
```

## 在系统中使用

### 步骤1：通过Cursor调用MCP工具

在Cursor中请求AI助手：
```
请使用 bailian_web_search 工具搜索"钢管 供应商"，返回5个结果
```

### 步骤2：获取MCP响应

AI助手会返回类似以下格式的数据：
```json
{
  "isError": false,
  "content": [
    {
      "text": "{\"status\":0,\"pages\":[{\"snippet\":\"...\", \"url\":\"...\"}]}",
      "type": "text"
    }
  ]
}
```

### 步骤3：解析并输入系统

系统已经实现了自动解析逻辑，可以：
1. 将MCP响应数据保存为JSON文件
2. 通过API端点上传
3. 或者在前端界面手动输入供应商信息

## 自动化方案（未来）

如果Cursor提供MCP API接口，可以：

1. **创建MCP客户端**：连接到Cursor的MCP服务器
2. **自动调用**：后端代码直接调用MCP工具
3. **自动解析**：使用已有的解析逻辑处理结果

## 当前工作流程

```
用户在前端点击"网络搜索供应商"
  ↓
显示提示：需要通过Cursor AI助手调用MCP工具
  ↓
用户在Cursor中请求AI助手调用 bailian_web_search
  ↓
AI助手返回搜索结果
  ↓
用户将结果手动输入到系统中
  ↓
系统保存供应商信息
```

## 测试

可以使用测试脚本验证解析逻辑：

```bash
cd backend
python test_mcp_mock.py
```

这会使用模拟数据测试解析逻辑，确保一旦获取到MCP响应，能够正确解析。

