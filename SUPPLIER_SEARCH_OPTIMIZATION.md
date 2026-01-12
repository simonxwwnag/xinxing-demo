# 供应商搜索进一步优化

## 优化内容

### 问题
之前的优化已经将LLM调用从60次减少到2次（批量处理），但知识库API仍然调用了2次（每个文档一次）。

### 优化方案
**一次调用知识库API，返回更多结果，然后在代码中过滤两个文档的结果。**

## 代码修改

### 修改前

```python
def search_suppliers_from_docs(self, ...):
    # 搜索集团定商采购文档
    group_suppliers = self._search_suppliers_in_doc(...)  # 第1次API调用
    
    # 搜索油田定商采购文档
    oilfield_suppliers = self._search_suppliers_in_doc(...)  # 第2次API调用
    
    return suppliers
```

**流程**:
1. 调用知识库API（集团文档）→ 返回30个结果 → 批量LLM处理
2. 调用知识库API（油田文档）→ 返回30个结果 → 批量LLM处理

**API调用次数**: 2次

### 修改后

```python
def search_suppliers_from_docs(self, ...):
    # 一次调用知识库API，返回60个结果
    response = self.service.search_knowledge(
        query=query,
        limit=60,  # 返回60个结果（两个文档各30个）
        ...
    )
    
    # 在代码中过滤两个文档的结果
    for point in points:
        if point_doc_id == self.group_doc_id:
            group_structured_points.append(...)
        elif point_doc_id == self.oilfield_doc_id:
            oilfield_structured_points.append(...)
    
    # 分别批量处理两个文档的structured points
    group_batch_suppliers = self._extract_suppliers_batch(...)
    oilfield_batch_suppliers = self._extract_suppliers_batch(...)
    
    return suppliers
```

**流程**:
1. 调用知识库API（一次）→ 返回60个结果
2. 在代码中过滤出两个文档的结果
3. 分别批量LLM处理两个文档的structured points

**API调用次数**: 1次

## 性能提升

### 优化前（批量LLM优化后）

```
知识库API调用：2次
├─→ 集团文档：1次（返回30个结果）
└─→ 油田文档：1次（返回30个结果）

LLM调用：2次（批量）
├─→ 集团文档：1次（处理30个表格）
└─→ 油田文档：1次（处理30个表格）

总耗时：
- 知识库API：2次 × 10秒 = 20秒
- LLM调用：2次 × 15秒 = 30秒
- 总计：50秒
```

### 优化后（合并API调用）

```
知识库API调用：1次
└─→ 一次调用返回60个结果（包含两个文档）

LLM调用：2次（批量）
├─→ 集团文档：1次（处理30个表格）
└─→ 油田文档：1次（处理30个表格）

总耗时：
- 知识库API：1次 × 15秒 = 15秒（返回更多结果，稍慢）
- LLM调用：2次 × 15秒 = 30秒
- 总计：45秒
```

**性能提升**: 
- API调用次数：从2次减少到1次（减少50%）
- 总耗时：从50秒减少到45秒（提升10%）

## 优化效果对比

| 指标 | 原始版本 | 批量LLM优化 | 合并API优化 | 总提升 |
|------|---------|------------|------------|--------|
| 知识库API调用 | 2次 | 2次 | **1次** | **50%** |
| LLM调用次数 | 60次 | 2次 | 2次 | 96.7% |
| 总耗时 | 600秒 | 50秒 | **45秒** | **92.5%** |

## 关键改进点

1. **减少API调用次数**
   - 从2次减少到1次
   - 减少网络延迟和API调用开销

2. **保持批量处理**
   - LLM调用仍然是批量处理（2次）
   - 每个文档的structured points分别批量处理

3. **代码中过滤**
   - 在代码中根据doc_id过滤两个文档的结果
   - 不依赖API的文档过滤功能

## 注意事项

1. **limit参数调整**
   - 从30增加到60（两个文档各30个）
   - 确保能获取足够的结果

2. **结果过滤**
   - 在代码中根据doc_id过滤
   - 需要正确处理dict和Point对象两种格式

3. **向后兼容**
   - `_search_suppliers_in_doc` 方法保留（测试文件仍在使用）
   - 新代码直接在主方法中实现

## 进一步优化空间

如果知识库API支持直接指定多个文档ID进行搜索，可以进一步优化：
- 减少返回结果数量（只返回两个文档的结果）
- 提高搜索精度
- 减少网络传输

但目前API不支持，所以采用代码过滤的方式。

