# 知识库API超时问题修复

## 问题描述
- 前端显示超时，但实际知识库搜索和AI总结功能正常
- 后端日志显示：`Read timed out. (read timeout=30)`
- 知识库API的超时设置太短（30秒），导致请求在知识库API层面超时

## 根本原因
知识库服务的超时设置：
- `connection_timeout=30` - 连接超时30秒
- `socket_timeout=30` - 读取超时30秒

但实际请求（特别是包含AI重排序的请求）可能需要更长时间，导致在知识库API层面就超时了。

## 修复方案

### 1. 增加知识库API超时设置
**文件**: `backend/services/knowledge_service.py`

**修改前**:
```python
self.service = VikingKnowledgeBaseService(
    host=Config.VIKING_HOST,
    scheme="https",
    connection_timeout=30,
    socket_timeout=30
)
```

**修改后**:
```python
self.service = VikingKnowledgeBaseService(
    host=Config.VIKING_HOST,
    scheme="https",
    connection_timeout=60,  # 连接超时60秒
    socket_timeout=120  # 读取超时120秒，支持AI重排序等耗时操作
)
```

### 2. 超时设置说明
- **connection_timeout=60**: 连接超时60秒，足够建立连接
- **socket_timeout=120**: 读取超时120秒，支持：
  - AI重排序（rerank）
  - 知识库搜索
  - 大量数据处理

### 3. 其他超时设置
- **前端axios超时**: 120秒（已设置）
- **AI模型调用超时**: 180秒（已设置）
- **知识库API超时**: 120秒（已修复）

## 测试建议

1. **重启后端服务**（使新的超时设置生效）
2. **测试知识库搜索功能**
3. **查看后端日志**，确认不再有超时错误

## 注意事项

如果问题仍然存在，可能的原因：
1. 知识库服务本身响应慢（需要检查知识库服务状态）
2. 网络连接问题
3. 需要进一步增加超时时间

