# 知识库搜索 API 超时问题分析

## 问题描述

前端调用 `/api/knowledge/search` API 时出现超时错误。

**请求参数：**
- `product_name`: "光纤收发器"
- `product_features`: "1.名称:光纤收发器\n2.规格:详设计"

**前端超时设置：** 120秒（120000ms）

## API 调用流程分析

### 1. API 入口 (`/api/knowledge/search`)

```20:160:backend/api/knowledge.py
@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    # 1. 调用 search_specs() - 搜索规格参数
    specs = knowledge_service.search_specs(
        request.product_name,
        request.product_features
    )
    
    # 2. 调用 search_suppliers_from_docs() - 搜索供应商
    suppliers = knowledge_service.search_suppliers_from_docs(
        request.product_name,
        request.product_features
    )
```

### 2. 规格搜索 (`search_specs`)

**耗时点：**
- 知识库 API 调用：`self.service.search_knowledge()` 
- 超时设置：120秒（socket_timeout）
- 返回结果：最多 4 条规格

**预计耗时：** 5-30秒（取决于知识库响应速度）

### 3. 供应商搜索 (`search_suppliers_from_docs`)

**流程：**
1. 搜索集团定商采购文档（`_search_suppliers_in_doc`）
2. 搜索油田定商采购文档（`_search_suppliers_in_doc`）

**每个文档搜索：**
- 知识库 API 调用：返回最多 30 个结果（`limit=30`）
- 对每个 `structured` 类型的 chunk，调用 `_extract_supplier_from_structured()`
- 每个 `_extract_supplier_from_structured()` 调用 LLM API（超时 180 秒）

### 4. 供应商提取 (`_extract_supplier_from_structured`)

**关键问题：串行处理**

```697:705:backend/services/knowledge_service.py
if chunk_type == 'structured':
    # 传递产品信息，让LLM在提取时同时判断相关性
    supplier = self._extract_supplier_from_structured(
        point, doc_id, doc_name, point_slice_id, 
        product_name=product_name, 
        product_features=product_features
    )
    if supplier:
        suppliers.append(supplier)
```

**LLM API 调用：**
```904:913:backend/services/knowledge_service.py
response = client.chat.completions.create(
    model=Config.ARK_MODEL,
    messages=[...],
    temperature=0.1,
    max_tokens=500,
    timeout=180.0  # 设置180秒超时
)
```

## 超时原因分析

### 主要原因：串行 LLM 调用

1. **返回结果数量多**：每个文档最多返回 30 个结果
2. **串行处理**：每个 structured chunk 都要串行调用 LLM API
3. **LLM 调用耗时长**：每次调用最多 180 秒，实际可能需要 5-30 秒
4. **累计时间过长**：
   - 如果返回 30 个 structured chunks
   - 每个 LLM 调用平均 10 秒
   - 总耗时：30 × 10 = 300 秒（5 分钟）
   - **超过前端 120 秒超时限制**

### 时间线估算

| 步骤 | 预计耗时 | 累计耗时 |
|------|---------|---------|
| 规格搜索 | 10-30秒 | 10-30秒 |
| 集团文档知识库搜索 | 5-15秒 | 15-45秒 |
| 集团文档 LLM 提取（30个，每个10秒） | 300秒 | 315秒 |
| 油田文档知识库搜索 | 5-15秒 | 320秒 |
| 油田文档 LLM 提取（30个，每个10秒） | 300秒 | **620秒** |

**结论：** 即使每个 LLM 调用只需要 5 秒，30 个调用也需要 150 秒，超过前端 120 秒超时。

## 解决方案

### 方案 1：减少返回结果数量（推荐）

**修改位置：** `backend/services/knowledge_service.py`

```python
# 当前：limit=30
search_params = {
    "query": query,
    "limit": 30,  # 返回30个结果，后续通过AI过滤
    ...
}

# 建议：limit=10
search_params = {
    "query": query,
    "limit": 10,  # 减少返回结果，降低LLM调用次数
    ...
}
```

**优点：**
- 简单快速
- 减少 LLM 调用次数
- 降低总耗时

**缺点：**
- 可能遗漏一些供应商

### 方案 2：并行处理 LLM 调用

**修改位置：** `backend/services/knowledge_service.py`

使用 `asyncio` 或 `concurrent.futures` 并行处理多个 LLM 调用。

**优点：**
- 大幅减少总耗时
- 保持结果完整性

**缺点：**
- 需要重构代码
- 增加并发压力

### 方案 3：增加前端超时时间

**修改位置：** `frontend/src/services/api.ts`

```typescript
// 当前：120秒
timeout: 120000,

// 建议：300秒（5分钟）
timeout: 300000,
```

**优点：**
- 简单快速
- 不需要修改后端

**缺点：**
- 用户体验差（等待时间长）
- 治标不治本

### 方案 4：添加超时控制（推荐组合）

**修改位置：** `backend/services/knowledge_service.py`

1. 减少返回结果数量（limit=10）
2. 添加每个 LLM 调用的超时控制（30秒）
3. 添加总超时控制（100秒）

**优点：**
- 平衡性能和结果完整性
- 避免无限等待

## 推荐实施方案

**组合方案：**
1. **减少返回结果数量**：`limit=10`（减少 LLM 调用次数）
2. **降低 LLM 超时时间**：`timeout=30.0`（避免单个调用耗时过长）
3. **增加前端超时时间**：`timeout=180000`（3分钟，给后端更多时间）
4. **添加总超时控制**：在 `_search_suppliers_in_doc` 中添加总超时检查

这样可以：
- 将 LLM 调用次数从 60 次（30×2）减少到 20 次（10×2）
- 将单个 LLM 调用超时从 180 秒降低到 30 秒
- 预计总耗时：10（规格）+ 10（知识库搜索）×2 + 10（LLM调用）×10×2 = 约 130 秒
- 前端超时 180 秒，留有安全余量

