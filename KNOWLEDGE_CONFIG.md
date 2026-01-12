# 知识库搜索参数配置说明

## 参数位置

知识库搜索的相关参数配置在以下位置：

1. **环境变量配置**：在 `.env` 文件中设置
2. **代码配置**：`backend/utils/config.py` 中读取环境变量
3. **实际使用**：`backend/services/knowledge_service.py` 中调用知识库API时使用

## 可配置参数

### 1. `KNOWLEDGE_SEARCH_LIMIT`
- **说明**：返回结果数量限制
- **默认值**：`10`
- **类型**：整数
- **作用**：控制知识库搜索返回的最大结果数量
- **配置示例**：
  ```env
  KNOWLEDGE_SEARCH_LIMIT=20
  ```

### 2. `KNOWLEDGE_RERANK_SWITCH`
- **说明**：是否启用重排序（Rerank）
- **默认值**：`False`
- **类型**：布尔值（true/false）
- **作用**：
  - `False`：仅使用向量检索，速度快但精度可能稍低
  - `True`：启用重排序模型，结果更精准但速度稍慢
- **推荐**：对于精度要求高的场景，建议设置为 `true`
- **配置示例**：
  ```env
  KNOWLEDGE_RERANK_SWITCH=true
  ```

### 3. `KNOWLEDGE_DENSE_WEIGHT`
- **说明**：稠密向量检索权重
- **默认值**：`0.5`
- **类型**：浮点数（0-1之间）
- **作用**：
  - `0.0`：完全依赖关键词检索（BM25）
  - `1.0`：完全依赖向量相似度检索
  - `0.5`：平衡两种检索方式
- **推荐**：
  - 如果查询词与文档内容匹配度高，可以增大（如0.7-0.8）
  - 如果查询词与文档内容差异大，可以减小（如0.2-0.3）
- **配置示例**：
  ```env
  KNOWLEDGE_DENSE_WEIGHT=0.7
  ```

### 4. `KNOWLEDGE_RERANK_MODEL`
- **说明**：重排序模型名称
- **默认值**：`Doubao-pro-4k-rerank`
- **类型**：字符串
- **作用**：指定使用的重排序模型
- **可选值**：根据火山引擎知识库支持的模型选择
- **配置示例**：
  ```env
  KNOWLEDGE_RERANK_MODEL=Doubao-pro-4k-rerank
  ```

### 5. `KNOWLEDGE_RETRIEVE_COUNT`
- **说明**：检索数量（重排序前的候选数量）
- **默认值**：`空`（使用系统默认值）
- **类型**：整数（可选）
- **作用**：
  - 如果启用了重排序，此参数控制重排序前的候选数量
  - 例如：`retrieve_count=50, limit=10` 表示先检索50个候选，然后重排序后返回前10个
- **推荐**：如果启用了重排序，可以设置为 `limit` 的3-5倍
- **配置示例**：
  ```env
  KNOWLEDGE_RETRIEVE_COUNT=50
  ```

### 6. `KNOWLEDGE_USE_QWEN_FILTER`
- **说明**：是否启用qwen模型筛选
- **默认值**：`True`
- **类型**：布尔值（true/false）
- **作用**：
  - `True`：使用qwen模型对知识库检索结果进行二次筛选，只保留与产品名称真正相关的内容
  - `False`：不使用筛选，直接返回前5条结果
- **推荐**：建议保持 `true`，可以过滤掉不相关的内容，提高结果质量
- **配置示例**：
  ```env
  KNOWLEDGE_USE_QWEN_FILTER=true
  ```

### 7. `KNOWLEDGE_QWEN_MODEL`
- **说明**：qwen筛选模型名称
- **默认值**：`qwen-plus`
- **类型**：字符串
- **作用**：指定用于筛选的qwen模型
- **可选值**：`qwen-plus`, `qwen-max`, `qwen-turbo` 等
- **配置示例**：
  ```env
  KNOWLEDGE_QWEN_MODEL=qwen-plus
  ```

## 完整配置示例

在 `backend/.env` 文件中添加以下配置：

```env
# 知识库搜索参数配置
# 返回结果数量
KNOWLEDGE_SEARCH_LIMIT=10

# 是否启用重排序（true/false）
KNOWLEDGE_RERANK_SWITCH=true

# 稠密向量检索权重（0-1之间）
KNOWLEDGE_DENSE_WEIGHT=0.6

# 重排序模型
KNOWLEDGE_RERANK_MODEL=Doubao-pro-4k-rerank

# 检索数量（重排序前的候选数量，可选）
KNOWLEDGE_RETRIEVE_COUNT=50

# Qwen模型筛选配置
# 是否启用qwen模型筛选（true/false）
KNOWLEDGE_USE_QWEN_FILTER=true
# qwen筛选模型
KNOWLEDGE_QWEN_MODEL=qwen-plus
```

## 参数调优建议

### 场景1：快速检索，精度要求一般
```env
KNOWLEDGE_RERANK_SWITCH=false
KNOWLEDGE_DENSE_WEIGHT=0.5
KNOWLEDGE_SEARCH_LIMIT=10
```

### 场景2：高精度检索，速度要求不高
```env
KNOWLEDGE_RERANK_SWITCH=true
KNOWLEDGE_DENSE_WEIGHT=0.7
KNOWLEDGE_SEARCH_LIMIT=10
KNOWLEDGE_RETRIEVE_COUNT=50
```

### 场景3：关键词匹配为主
```env
KNOWLEDGE_RERANK_SWITCH=false
KNOWLEDGE_DENSE_WEIGHT=0.3
KNOWLEDGE_SEARCH_LIMIT=15
```

### 场景4：语义相似度为主
```env
KNOWLEDGE_RERANK_SWITCH=true
KNOWLEDGE_DENSE_WEIGHT=0.8
KNOWLEDGE_SEARCH_LIMIT=10
KNOWLEDGE_RETRIEVE_COUNT=30
```

## 代码中的使用位置

### 1. 配置读取
文件：`backend/utils/config.py`
```python
KNOWLEDGE_SEARCH_LIMIT = int(os.getenv("KNOWLEDGE_SEARCH_LIMIT", "10"))
KNOWLEDGE_RERANK_SWITCH = os.getenv("KNOWLEDGE_RERANK_SWITCH", "False").lower() == "true"
KNOWLEDGE_DENSE_WEIGHT = float(os.getenv("KNOWLEDGE_DENSE_WEIGHT", "0.5"))
# ...
```

### 2. API调用
文件：`backend/services/knowledge_service.py`
```python
search_params = {
    "query": query,
    "limit": Config.KNOWLEDGE_SEARCH_LIMIT,
    "rerank_switch": Config.KNOWLEDGE_RERANK_SWITCH,
    "dense_weight": Config.KNOWLEDGE_DENSE_WEIGHT,
    "rerank_model": Config.KNOWLEDGE_RERANK_MODEL,
}
response = self.service.search_collection(**search_params)
```

## Qwen模型筛选功能

系统会自动使用qwen模型对知识库检索结果进行二次筛选，确保只返回与产品名称真正相关的内容。

### 工作流程

1. **知识库检索**：从知识库中检索相关结果（默认10条）
2. **Qwen筛选**：使用qwen模型分析每条结果，判断是否与产品名称真正相关
3. **返回结果**：只返回筛选后的相关结果（最多5条）

### 筛选标准

- ✅ **保留**：内容明确提到产品名称或相关关键词
- ✅ **保留**：内容描述与产品相关的技术规格、参数、配置要求
- ✅ **保留**：内容涉及产品的使用场景、安装要求、接口规范等
- ❌ **排除**：仅包含公司信息、文档编号等与产品无关的内容
- ❌ **排除**：内容模糊，无法确定与产品的关系

### 优势

- **提高精度**：过滤掉不相关的内容，只保留真正有用的信息
- **减少噪音**：避免显示通用文档信息或与产品无关的内容
- **智能判断**：使用AI模型理解语义，而不仅仅是关键词匹配

## 注意事项

1. **修改配置后需要重启后端服务**才能生效
2. **rerank_switch=true** 会增加API调用时间和成本
3. **dense_weight** 需要根据实际数据特点调整，建议先测试不同值的效果
4. **retrieve_count** 只在启用重排序时才有意义
5. **KNOWLEDGE_USE_QWEN_FILTER=true** 会增加一次qwen API调用，但能显著提高结果质量
6. **需要配置DASHSCOPE_API_KEY**才能使用qwen筛选功能

## 测试配置效果

可以使用以下命令测试不同配置的效果：

```bash
cd backend
python test_knowledge.py
```

或者通过API测试：
```bash
curl -X POST http://localhost:8000/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"product_name":"光纤收发器","product_features":"光纤收发器"}'
```

