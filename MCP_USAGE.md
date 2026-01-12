# MCP WebSearch 使用指南

## ⚠️ SSE Endpoint调用限制

项目已实现通过HTTP SSE Endpoint调用MCP WebSearch的框架，但**SSE Endpoint可能需要通过MCP协议调用，而不是直接HTTP POST**。

**SSE Endpoint**: `https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse`

**鉴权方式**: 使用 `DASHSCOPE_API_KEY` 在请求头中鉴权（Bearer Token方式）

**实现位置**: `backend/services/mcp_proxy.py`

**当前状态**: 直接HTTP调用可能返回空响应，需要通过MCP SDK或MCP服务器代理调用。

## 配置说明

1. **配置API Key**: 在项目根目录的 `.env` 文件中设置：
   ```env
   DASHSCOPE_API_KEY=your_api_key_here
   ```

2. **安装依赖**: 确保已安装 `requests` 库：
   ```bash
   pip install requests
   ```

3. **测试调用**: 运行测试脚本验证配置：
   ```bash
   cd backend
   python test_mcp.py
   ```

## 工作原理

1. 前端调用 `/api/search/suppliers` API
2. 后端通过 `MCPProxyService` 调用SSE Endpoint
3. 解析SSE流式响应，提取搜索结果
4. 将结果转换为 `SupplierInfo` 对象并返回

## API调用示例

```python
from services.mcp_proxy import MCPProxyService

mcp_proxy = MCPProxyService()
suppliers = mcp_proxy.search_web("钢管 供应商", count=5)

for supplier in suppliers:
    print(f"{supplier.name}: {supplier.url}")
```

## 其他解决方案（已弃用，仅供参考）

### 方案1：通过AI助手调用（已不需要）

在需要搜索供应商时，可以通过AI助手（如Cursor AI）来调用MCP工具：

1. **在前端添加提示**：当用户点击"网络搜索供应商"按钮时，显示提示信息
2. **通过AI助手调用**：在AI助手中输入搜索请求，AI助手会调用MCP工具
3. **手动输入结果**：将搜索结果手动输入到系统中

### 方案2：创建MCP客户端服务（推荐用于生产）

创建一个独立的Python服务，使用MCP SDK来调用工具：

```python
# mcp_client_service.py
from mcp import Client
import asyncio

class MCPClientService:
    def __init__(self):
        # 初始化MCP客户端
        self.client = Client(
            server_url="http://localhost:3000",  # MCP服务器地址
            # 其他配置...
        )
    
    async def web_search(self, query: str, count: int = 5):
        """调用MCP WebSearch工具"""
        result = await self.client.call_tool(
            "bailian_web_search",
            {"query": query, "count": count}
        )
        return result
```

然后在后端API中调用这个服务。

### 方案3：使用MCP HTTP接口（如果MCP服务器支持）

如果MCP服务器提供HTTP接口，可以直接通过HTTP请求调用：

```python
import requests

def search_web(query: str):
    response = requests.post(
        "http://localhost:3000/mcp/bailian_web_search",
        json={"query": query, "count": 5}
    )
    return response.json()
```

### 方案4：使用替代搜索API

如果无法使用MCP工具，可以使用其他搜索API：

- **Google Custom Search API**
- **Bing Web Search API**  
- **百度搜索API**
- **SerpAPI**
- **DuckDuckGo API**

## 当前实现状态

当前代码中：
- `backend/api/search.py` - 提供了搜索API端点框架
- `backend/services/mcp_proxy.py` - 提供了MCP代理服务框架
- `frontend/src/components/WebSearchButton.tsx` - 前端搜索按钮组件

这些组件都已经准备好，只需要配置实际的MCP调用方式即可。

## 快速测试方案

为了快速测试功能，你可以：

1. **临时使用模拟数据**：修改 `backend/services/mcp_proxy.py`，返回模拟的搜索结果
2. **手动输入数据**：通过前端界面手动输入搜索结果
3. **使用AI助手**：在需要时通过AI助手调用MCP工具，然后手动输入结果

## 下一步行动

1. **检查MCP服务器配置**：确认MCP服务器是否提供HTTP接口或SDK
2. **选择集成方案**：根据你的环境选择合适的方案
3. **实现集成**：根据选择的方案实现实际的调用逻辑

## 示例：通过AI助手调用MCP工具

当你在Cursor中时，可以这样调用：

```
请帮我搜索"钢管 供应商"，使用MCP WebSearch工具
```

AI助手会调用MCP工具并返回结果，然后你可以将结果输入到系统中。

