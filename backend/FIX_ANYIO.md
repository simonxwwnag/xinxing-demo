# 修复 anyio 版本冲突

## 问题

`qwen-agent` 和 `mcp` 库对 `anyio` 版本要求冲突：
- `qwen-agent` 需要 `anyio<4` (安装的是 3.7.1)
- `mcp` 库需要 `anyio>=4.5`
- Python 3.12 中，`anyio` 3.7.1 不支持类型参数语法

## 解决方案

### 方案1：升级 anyio（推荐用于测试）

```bash
pip install "anyio>=4.5"
```

然后重新测试：
```bash
python test_qwen_agent_mcp.py
```

**注意**：这可能会破坏 `qwen-agent` 的其他功能，需要测试。

### 方案2：使用虚拟环境隔离

创建独立的虚拟环境专门用于 MCP 调用：

```bash
python -m venv venv_mcp
source venv_mcp/bin/activate
pip install qwen-agent "anyio>=4.5"
```

### 方案3：等待库更新

等待 `qwen-agent` 更新以支持更新的 `anyio` 版本。

### 方案4：使用 Cursor AI 助手（当前推荐）

由于版本冲突难以解决，**演示时建议使用 Cursor AI 助手调用 MCP 工具**：

1. 在 Cursor 中通过 AI 助手调用 MCP 工具
2. 将结果通过 `/api/mcp/parse-response` API 输入系统
3. 系统会自动解析

详见 `CURSOR_MCP_USAGE.md`

## 当前状态

- ✅ `qwen_agent` 已安装
- ✅ MCP 配置格式正确
- ⚠️ 由于 `anyio` 版本冲突，初始化失败
- ✅ 解析逻辑已实现并测试通过
- ✅ 提供了回退方案（Cursor AI 助手 + 手动输入）

