# 在Cursor中使用MCP WebSearch

## MCP配置

你已经在Cursor中配置了MCP服务器：

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

## 使用方式

### 方式1：通过AI助手调用（推荐用于演示）

在Cursor的AI助手中，直接输入搜索请求：

```
请帮我搜索"钢管 供应商"，使用MCP WebSearch工具
```

AI助手会自动调用MCP工具并返回结果，格式如下：

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

然后将结果手动输入到系统中。

### 方式2：在代码中通过MCP SDK调用（如果可用）

如果安装了MCP Python SDK，可以在代码中直接调用：

```python
from mcp import Client

client = Client(
    server_url="https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
    headers={"Authorization": f"Bearer {api_key}"}
)

result = client.call_tool("bailian_web_search", {
    "query": "钢管 供应商",
    "count": 5
})
```

### 方式3：创建MCP服务器代理

创建一个独立的MCP服务器来代理调用，然后后端通过HTTP调用这个代理服务器。

## 当前实现状态

✅ **解析逻辑**：已实现，可以正确解析MCP响应格式
✅ **API框架**：已实现，等待正确的调用方式
⚠️ **实际调用**：需要通过MCP环境调用（Cursor AI或MCP SDK）

## 演示建议

在演示时：
1. 用户点击"网络搜索供应商"按钮
2. 前端显示提示："正在通过AI助手搜索..."
3. 在Cursor AI中输入搜索请求
4. 获取搜索结果后，手动输入到系统中
5. 或者，如果实现了MCP SDK调用，可以自动完成

## 下一步

1. 查找MCP Python SDK（如果可用）
2. 或实现MCP服务器代理
3. 或使用手动输入方式（演示用）

