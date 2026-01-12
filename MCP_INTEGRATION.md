# MCP WebSearch 集成说明

## 概述

由于 MCP (Model Context Protocol) WebSearch 工具需要通过 AI 助手环境调用，而 FastAPI 后端无法直接调用 MCP 工具，因此需要特殊的集成方案。

## 集成方案

### 方案1：前端直接调用 MCP 工具（推荐）

如果前端环境支持 MCP 工具调用，可以在前端直接调用：

```typescript
// 在前端组件中
import { web_search } from '@mcp/websearch';

const searchSuppliers = async (productName: string) => {
  const results = await web_search({
    search_term: `${productName} 供应商 厂家`
  });
  
  // 处理搜索结果
  return results;
};
```

### 方案2：创建中间服务

创建一个独立的服务来处理 MCP 工具调用：

```python
# mcp_service.py
async def call_mcp_websearch(search_term: str):
    # 通过 HTTP 或其他方式调用 MCP 服务
    # 或者使用 MCP SDK
    pass
```

### 方案3：使用替代搜索API

使用其他网络搜索 API 替代 MCP WebSearch：

- Google Custom Search API
- Bing Web Search API
- 百度搜索 API
- 其他搜索服务

## 当前实现

当前实现中，`backend/api/search.py` 提供了接口框架，但返回空结果。需要根据实际环境选择合适的集成方案。

## 使用建议

1. **开发阶段**：可以先使用模拟数据或替代搜索 API
2. **生产环境**：根据实际架构选择合适的集成方案
3. **演示环境**：如果支持，使用前端直接调用 MCP 工具

