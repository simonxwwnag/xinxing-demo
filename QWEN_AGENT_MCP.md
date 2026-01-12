# 使用 qwen_agent 调用 MCP WebSearch

## 概述

参考 `qwen_agent` 库的 `Assistant` 类来调用 MCP WebSearch 工具。这种方式可以正确调用 MCP 服务器，因为 `qwen_agent` 支持 MCP 协议。

## 安装

```bash
pip install qwen-agent
```

## 配置

### 1. 环境变量

确保在 `.env` 文件中配置了 `DASHSCOPE_API_KEY`：

```env
DASHSCOPE_API_KEY=your_api_key_here
```

### 2. MCP 服务器配置

在代码中配置 MCP 服务器（已在 `mcp_qwen_agent.py` 中实现）：

```python
mcp_tools = [
    {
        "mcpServers": {
            "bailian-web-search": {
                "type": "sse",
                "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
                "headers": {
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
                }
            }
        }
    }
]
```

## 使用方法

### 方式1：通过 MCPProxyService（自动选择）

`MCPProxyService` 会自动尝试使用 `qwen_agent`，如果可用则优先使用：

```python
from services.mcp_proxy import MCPProxyService

suppliers = MCPProxyService.search_web("钢管 供应商", count=5)
```

### 方式2：直接使用 QwenAgentMCPService

```python
from services.mcp_qwen_agent import QwenAgentMCPService

service = QwenAgentMCPService()
suppliers = service.search_web("钢管 供应商", count=5)
```

## 测试

运行测试脚本：

```bash
cd backend
python test_qwen_agent_mcp.py
```

## 工作原理

1. **初始化 Assistant**：使用 `qwen_agent.agents.Assistant` 创建助手实例
2. **配置 MCP 工具**：在 `function_list` 中配置 MCP 服务器
3. **发送请求**：通过自然语言请求助手调用 MCP 工具
4. **获取响应**：从流式响应中提取工具调用结果
5. **解析数据**：使用已有的解析逻辑处理 MCP 响应格式

## 优势

- ✅ 正确支持 MCP 协议
- ✅ 可以调用 Cursor 中配置的 MCP 服务器
- ✅ 自动处理工具调用流程
- ✅ 流式响应支持

## 注意事项

1. 需要安装 `qwen-agent` 库
2. 需要配置 `DASHSCOPE_API_KEY`
3. MCP 服务器配置格式需要与 `qwen_agent` 兼容
4. 如果 `qwen_agent` 不可用，会自动回退到直接 HTTP 调用

