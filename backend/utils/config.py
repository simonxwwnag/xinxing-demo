import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 火山引擎知识库配置
    VIKING_AK = os.getenv("VIKING_AK", "")
    VIKING_SK = os.getenv("VIKING_SK", "")
    VIKING_HOST = os.getenv("VIKING_HOST", "api-knowledgebase.mlp.cn-beijing.volces.com")
    
    # 火山引擎Ark模型配置（用于知识库问答）
    ARK_API_KEY = os.getenv("ARK_API_KEY", "")
    ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    ARK_MODEL = os.getenv("ARK_MODEL", "doubao-seed-1-6-flash-250828")
    
    # 阿里云百炼配置（用于MCP WebSearch网络搜索）
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    
    # 知识库集合和文档ID
    KNOWLEDGE_COLLECTION_ID = os.getenv("KNOWLEDGE_COLLECTION_ID", "")
    GROUP_SUPPLIER_DOC_ID = os.getenv("GROUP_SUPPLIER_DOC_ID", "")
    OILFIELD_SUPPLIER_DOC_ID = os.getenv("OILFIELD_SUPPLIER_DOC_ID", "")
    
    # 知识库搜索参数配置
    # limit: 返回结果数量限制（默认10）
    KNOWLEDGE_SEARCH_LIMIT = int(os.getenv("KNOWLEDGE_SEARCH_LIMIT", "10"))
    # rerank_switch: 是否启用重排序（默认False，启用后结果更精准但速度稍慢）
    KNOWLEDGE_RERANK_SWITCH = os.getenv("KNOWLEDGE_RERANK_SWITCH", "False").lower() == "true"
    # dense_weight: 稠密向量检索权重（0-1之间，默认0.5，值越大越依赖向量相似度）
    KNOWLEDGE_DENSE_WEIGHT = float(os.getenv("KNOWLEDGE_DENSE_WEIGHT", "0.5"))
    # rerank_model: 重排序模型（默认Doubao-pro-4k-rerank）
    KNOWLEDGE_RERANK_MODEL = os.getenv("KNOWLEDGE_RERANK_MODEL", "Doubao-pro-4k-rerank")
    # retrieve_count: 检索数量（重排序前的候选数量，默认None使用系统默认值）
    KNOWLEDGE_RETRIEVE_COUNT = os.getenv("KNOWLEDGE_RETRIEVE_COUNT", "15")
    KNOWLEDGE_RETRIEVE_COUNT = int(KNOWLEDGE_RETRIEVE_COUNT) if KNOWLEDGE_RETRIEVE_COUNT else None
    
    # 数据存储路径
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
    PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
    PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")

