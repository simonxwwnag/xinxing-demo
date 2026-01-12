# qwen_agent MCP 调用问题说明

## 问题

使用 `qwen_agent` 调用 MCP WebSearch 时遇到错误：

```
TypeError: 'function' object is not subscriptable
```

## 原因

这是由于 `anyio` 版本冲突导致的：

- `qwen-agent` 需要 `anyio<4` (当前安装的是 3.7.1)
- `mcp` 库需要 `anyio>=4.5`
- Python 3.12 中，`anyio` 3.7.1 不支持类型参数语法 `anyio.create_memory_object_stream[JSONRPCResponse]`

## 解决方案

### 方案1：升级 anyio（可能破坏其他依赖）

```bash
pip install "anyio>=4.5"
```

但这可能导致 `qwen-agent` 不兼容。

### 方案2：使用其他方式调用 MCP

由于版本冲突难以解决，建议：

1. **通过 Cursor AI 助手调用**（推荐）
   - 在 Cursor 中通过 AI 助手调用 MCP 工具
   - 将结果手动输入系统
   - 详见 `CURSOR_MCP_USAGE.md`

2. **使用 MCP 响应解析 API**
   - 通过 `/api/mcp/parse-response` 端点手动输入 MCP 响应
   - 系统会自动解析

3. **等待 qwen_agent 更新**
   - 等待 `qwen-agent` 库更新以支持更新的 `anyio` 版本

## 当前状态

- ✅ `qwen_agent` 已安装
- ✅ MCP 配置格式正确
- ❌ 由于 `anyio` 版本冲突，无法正常初始化
- ✅ 解析逻辑已实现并测试通过

## 建议

**演示时使用方案1**：通过 Cursor AI 助手调用 MCP 工具，然后手动输入结果。这是最可靠的方式。

