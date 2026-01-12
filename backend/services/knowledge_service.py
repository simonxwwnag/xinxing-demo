from typing import List, Dict, Any, Optional
from volcengine.viking_knowledgebase import VikingKnowledgeBaseService
from models.schemas import SpecSource, SupplierInfo
from utils.config import Config
import os
import time
from datetime import datetime
from openai import OpenAI

def log_with_time(message: str):
    """带时间戳的日志输出"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] {message}")

def extract_chunk_info(point: Any) -> Dict[str, Any]:
    """
    从point对象中提取完整的chunk信息
    支持对象和字典两种格式
    返回包含content、md_content、html_content等字段的字典
    """
    chunk_info = {
        "content": "",
        "slice_id": "",
        "doc_id": "",
        "doc_name": "",
        "image_url": None,
        "chunk_type": None,
        "md_content": None,
        "html_content": None,
        "point_id": None
    }
    
    # 判断是对象还是字典
    if isinstance(point, dict):
        # 字典格式
        # 提取文档信息
        doc_info = point.get('doc_info', {})
        if isinstance(doc_info, dict):
            chunk_info["doc_name"] = doc_info.get('doc_name', doc_info.get('name', ''))
            chunk_info["doc_id"] = doc_info.get('doc_id', point.get('doc_id', ''))
        else:
            chunk_info["doc_name"] = point.get('doc_name', point.get('document_name', ''))
            chunk_info["doc_id"] = point.get('doc_id', point.get('document_id', ''))
        
        # 提取内容
        content = point.get('content', point.get('text', point.get('chunk', '')))
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except:
                try:
                    content = content.decode('gbk')
                except:
                    content = content.decode('utf-8', errors='ignore')
        chunk_info["content"] = content
        
        # 提取其他格式的内容
        chunk_info["md_content"] = point.get('md_content', point.get('markdown_content'))
        chunk_info["html_content"] = point.get('html_content', point.get('html'))
        
        # 提取ID
        chunk_info["slice_id"] = point.get('point_id', point.get('id', point.get('chunk_id', '')))
        chunk_info["point_id"] = point.get('point_id', point.get('id'))
        
        # 提取chunk_type
        chunk_info["chunk_type"] = point.get('chunk_type')
        
        # 提取图片链接（需要设置get_attachment_link=True才能获取）
        chunk_attachment = point.get('chunk_attachment', [])
        if isinstance(chunk_attachment, list) and len(chunk_attachment) > 0:
            attachment = chunk_attachment[0]
            if isinstance(attachment, dict):
                chunk_info["image_url"] = attachment.get('link', '')
                if chunk_info["image_url"]:
                    print(f"[extract_chunk_info] 提取到图片链接: {chunk_info['image_url'][:50]}...")
            elif hasattr(attachment, 'link'):
                chunk_info["image_url"] = attachment.link
                if chunk_info["image_url"]:
                    print(f"[extract_chunk_info] 提取到图片链接(对象): {chunk_info['image_url'][:50]}...")
    else:
        # 对象格式
        # 提取文档信息
        if hasattr(point, 'doc_info') and point.doc_info:
            if isinstance(point.doc_info, dict):
                chunk_info["doc_name"] = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
            elif hasattr(point.doc_info, 'doc_name'):
                chunk_info["doc_name"] = point.doc_info.doc_name
            elif hasattr(point.doc_info, 'name'):
                chunk_info["doc_name"] = point.doc_info.name
        
        if not chunk_info["doc_name"]:
            if hasattr(point, 'doc_name'):
                chunk_info["doc_name"] = point.doc_name
        
        chunk_info["doc_id"] = getattr(point, 'doc_id', '')
        
        # 提取内容
        content = getattr(point, 'content', '') or ''
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except:
                try:
                    content = content.decode('gbk')
                except:
                    content = content.decode('utf-8', errors='ignore')
        chunk_info["content"] = content
        
        # 提取其他格式的内容
        chunk_info["md_content"] = getattr(point, 'md_content', None) or getattr(point, 'markdown_content', None)
        chunk_info["html_content"] = getattr(point, 'html_content', None) or getattr(point, 'html', None)
        
        # 提取ID
        chunk_info["slice_id"] = getattr(point, 'point_id', None) or getattr(point, 'chunk_id', None) or ''
        chunk_info["point_id"] = getattr(point, 'point_id', None)
        
        # 提取chunk_type
        chunk_info["chunk_type"] = getattr(point, 'chunk_type', None)
        
        # 提取图片链接（需要设置get_attachment_link=True才能获取）
        if hasattr(point, 'chunk_attachment') and point.chunk_attachment:
            if isinstance(point.chunk_attachment, list) and len(point.chunk_attachment) > 0:
                attachment = point.chunk_attachment[0]
                if isinstance(attachment, dict):
                    chunk_info["image_url"] = attachment.get('link', '')
                    if chunk_info["image_url"]:
                        print(f"[extract_chunk_info] 提取到图片链接: {chunk_info['image_url'][:50]}...")
                elif hasattr(attachment, 'link'):
                    chunk_info["image_url"] = attachment.link
                    if chunk_info["image_url"]:
                        print(f"[extract_chunk_info] 提取到图片链接(对象): {chunk_info['image_url'][:50]}...")
    
    return chunk_info

def refresh_image_link(knowledge_service: Any, slice_id: str) -> Optional[str]:
    """
    根据slice_id重新获取图片链接
    当图片链接过期时，可以调用此函数刷新链接
    
    Args:
        knowledge_service: KnowledgeService实例
        slice_id: 切片ID
        
    Returns:
        新的图片链接，如果获取失败返回None
    """
    try:
        # 使用slice_id作为查询条件，搜索对应的chunk
        # 注意：这里需要根据实际API调整查询方式
        # 由于知识库API可能不支持直接通过point_id查询，我们需要使用一个特殊的查询
        
        # 构建post_processing参数
        post_processing = {
            "chunk_group": True,
            "get_attachment_link": True,  # 获取图片链接
        }
        
        # 尝试使用slice_id作为查询（如果API支持）
        # 如果不支持，可能需要存储slice_id到doc_id的映射
        search_params = {
            "query": slice_id,  # 使用slice_id作为查询
            "limit": 1,  # 只需要一个结果
            "post_processing": post_processing,
        }
        
        if knowledge_service.collection_name:
            search_params["collection_name"] = knowledge_service.collection_name
            response = knowledge_service.service.search_knowledge(**search_params)
        else:
            search_params["collection_name"] = "default"
            search_params["resource_id"] = knowledge_service.collection_id
            response = knowledge_service.service.search_knowledge(**search_params)
        
        # 解析响应，查找匹配的slice_id
        if response:
            if isinstance(response, list):
                points = response
            elif isinstance(response, dict):
                points = response.get('result_list', response.get('results', []))
            else:
                points = []
            
            for point in points:
                # 提取point_id
                point_id = None
                if isinstance(point, dict):
                    point_id = point.get('point_id', point.get('id', point.get('chunk_id', '')))
                elif hasattr(point, 'point_id'):
                    point_id = point.point_id or getattr(point, 'chunk_id', None)
                
                # 如果匹配，提取图片链接
                if point_id == slice_id:
                    chunk_info = extract_chunk_info(point)
                    if chunk_info.get('image_url'):
                        return chunk_info['image_url']
        
        return None
    except Exception as e:
        print(f"[refresh_image_link] 刷新图片链接失败: {e}")
        import traceback
        traceback.print_exc()
        return None

class KnowledgeService:
    """知识库服务"""
    
    def __init__(self):
        # 增加超时设置，知识库API可能需要较长时间
        # connection_timeout: 连接超时（秒）
        # socket_timeout: 读取超时（秒），设置为120秒以支持AI重排序等耗时操作
        self.service = VikingKnowledgeBaseService(
            host=Config.VIKING_HOST,
            scheme="https",
            connection_timeout=60,  # 连接超时60秒
            socket_timeout=120  # 读取超时120秒，支持AI重排序等耗时操作
        )
        self.service.set_ak(Config.VIKING_AK)
        self.service.set_sk(Config.VIKING_SK)
        self.collection_id = Config.KNOWLEDGE_COLLECTION_ID
        self.group_doc_id = Config.GROUP_SUPPLIER_DOC_ID
        self.oilfield_doc_id = Config.OILFIELD_SUPPLIER_DOC_ID
        
        # 尝试获取集合名称（如果collection_id是ID格式）
        self.collection_name = None
        self._init_collection_name()
    
    def _init_collection_name(self):
        """初始化集合名称"""
        try:
            # 如果collection_id看起来像ID（包含连字符），尝试获取集合信息
            if self.collection_id and '-' in self.collection_id:
                # 尝试使用resource_id参数
                # 或者先获取集合信息
                try:
                    collection_info = self.service.get_collection(resource_id=self.collection_id)
                    if collection_info and 'collection_name' in collection_info:
                        self.collection_name = collection_info['collection_name']
                    else:
                        # 如果获取失败，尝试直接使用ID作为resource_id
                        self.collection_name = None  # 将使用resource_id参数
                except:
                    # 如果获取失败，尝试直接使用ID作为resource_id
                    self.collection_name = None
            else:
                # 如果看起来像名称，直接使用
                self.collection_name = self.collection_id
        except Exception as e:
            print(f"初始化集合名称失败: {e}")
            self.collection_name = None
    
    def summarize_specs(self, product_name: str, product_features: str = None) -> Dict[str, Any]:
        """
        搜索并总结产品规格信息
        
        Args:
            product_name: 产品名称
            product_features: 产品特征（可选）
            
        Returns:
            包含总结内容和引用列表的字典
        """
        start_time = time.time()
        log_with_time(f"[规格总结] 开始总结规格参数: {product_name}")
        
        try:
            # 1. 先搜索规格相关的chunk（只使用product_name搜索，product_features是原始需求，稍后会合并）
            search_start = time.time()
            log_with_time(f"[规格总结] [1.1] 开始搜索规格chunk（仅使用产品名称: {product_name}）...")
            if product_features:
                log_with_time(f"[规格总结] [1.1] 原始需求规格: {product_features[:100]}...")
            # 搜索时只使用product_name，product_features作为原始需求稍后合并
            specs = self.search_specs(product_name, None)  # 不传入product_features，只使用product_name搜索
            search_elapsed = time.time() - search_start
            log_with_time(f"[规格总结] [1.1] 搜索完成 (耗时: {search_elapsed:.2f}秒)，找到 {len(specs)} 条规格")
            
            if not specs:
                # 即使知识库没有匹配，如果有原始规格，也应该返回原始规格
                if product_features and product_features.strip():
                    log_with_time(f"[规格总结] 未找到知识库规格，返回原始规格")
                    # 格式化原始规格，使其更易读
                    import re
                    formatted_specs = product_features.strip()
                    # 如果原始规格是多行的，保持格式；如果是单行，尝试格式化
                    if '\n' not in formatted_specs:
                        # 尝试将类似 "1.名称:xxx 2.规格:xxx" 的格式转换为列表
                        formatted_specs = re.sub(r'(\d+)\.', r'\n\1.', formatted_specs)
                        formatted_specs = formatted_specs.strip()
                    
                    return {
                        "summary": f"## 原始规格参数\n\n{formatted_specs}",
                        "references": []
                    }
                else:
                    log_with_time(f"[规格总结] 未找到规格，返回空结果")
                    return {
                        "summary": "没有找到规格参数",
                        "references": []
                    }
            
            # 2. 使用Ark模型总结规格参数
            api_key = Config.ARK_API_KEY
            if not api_key:
                log_with_time(f"[规格总结] 未配置ARK_API_KEY，返回原始chunk")
                # 如果没有配置API key，返回原始chunk内容
                summary = f"找到 {len(specs)} 条规格信息，请查看下方参考内容。"
                return {
                    "summary": summary,
                    "references": specs
                }
            
            # 构建prompt
            prompt_start = time.time()
            log_with_time(f"[规格总结] [1.2] 开始构建prompt...")
            client = OpenAI(
                api_key=api_key,
                base_url=Config.ARK_BASE_URL,
                timeout=180.0,  # 设置180秒超时
            )
            
            # 构建prompt，包含所有相关chunk
            # 注意：search_specs已经限制返回4个chunk，使用全部chunk
            context_parts = []
            
            # 首先添加原始需求规格（如果有），作为基础参考
            if product_features and product_features.strip():
                original_specs = product_features.strip()
                context_parts.append(f"【原始需求规格】\n{original_specs}\n")
                log_with_time(f"[规格总结] 添加原始需求规格，长度: {len(original_specs)} 字符")
            
            # 然后添加从知识库搜索到的规格信息
            for i, spec in enumerate(specs):  # 使用全部chunk（最多4个）
                slice_id = spec.slice_id
                doc_name = spec.doc_name or '未知文档'
                content = spec.content[:800]  # 限制每个chunk长度
                image_url = spec.image_url or ''
                
                # 构建参考内容，包含slice_id
                chunk_text = f"【知识库参考资料 {i+1}】\npoint_id: {slice_id}\n文档名称：{doc_name}\n内容：{content}"
                if image_url:
                    chunk_text += f"\n图片链接：{image_url}"
                context_parts.append(chunk_text)
            
            context_text = "\n\n".join(context_parts)
            
            # 构建用户问题，明确是关于产品规格参数
            user_question = f"{product_name}的详细规格参数和技术要求有哪些？"
            if product_features:
                user_question += f"\n\n注意：原始需求中已提供了部分规格信息（{product_features[:50]}...），请结合知识库中的详细规格信息，对原始规格进行补充和完善。"
            
            prompt = f"""# 任务
你是一位专业的采购专家，你的任务是根据「参考资料」总结产品的详细规格参数和技术要求，这些信息在 <context></context> XML tags 之内。

参考资料包含两部分：
1. 【原始需求规格】：用户提供的原始规格需求（可能不够详细）
2. 【知识库参考资料】：从知识库中搜索到的详细规格信息

你的总结要满足以下要求：
    1. 优先使用知识库中的详细规格信息，对原始需求规格进行补充和完善。
    2. 如果知识库中有更详细的规格参数，应该用知识库的信息补充原始规格。
    3. 如果原始需求规格已经很详细，知识库信息只是补充，则保留原始规格的主要内容，用知识库信息补充细节。
    4. 总结要简洁明了，突出关键的技术参数和规格要求。
    5. 如果参考资料不能帮助你总结规格参数，告知"没有找到额外的规格参数"。
    6. 总结要分点列出，便于阅读。

# 任务执行
现在请你根据提供的参考资料，总结产品的规格参数和技术要求。请将原始需求规格和知识库中的详细规格信息进行整合，形成完整的规格参数总结。

# 参考资料
<context>
{context_text}
</context>
参考资料中提到的图片按上传顺序排列，请结合图片与文本信息综合总结。如参考资料中没有图片，请仅根据参考资料中的文本信息总结。

# 引用要求
1. 当可以总结时，在句子末尾适当引用相关参考资料，每个参考资料引用格式必须使用<reference>标签对，例如: <reference data-ref="{{point_id}}"></reference>
2. 当告知没有额外规格参数时，不允许引用任何参考资料
3. 'data-ref' 字段表示对应参考资料的 point_id
4. 'point_id' 取值必须来源于参考资料对应的'point_id'后的id号
5. 适当合并引用，当引用项相同可以合并引用，只在引用内容结束添加一个引用标签。

# 配图要求
1. 首先对参考资料的每个图片内容含义深入理解，然后从所有图片中筛选出与总结内容直接关联的图片，在总结中的合适位置插入作为配图，图像内容必须支持直接的可视化说明规格参数。若参考资料中无适配图片，或图片仅是间接性关联，则省略配图。
2. 使用 <illustration> 标签对表示插图，例如: <illustration data-ref="{{point_id}}"></illustration>，其中 'point_id' 字段表示对应图片的 point_id，每个配图标签对必须另起一行，相同的图片（以'point_id'区分）只允许使用一次。
3. 'point_id' 取值必须来源于参考资料，形如"_sys_auto_gen_doc_id-1005563729285435073--1"，请注意务必不要虚构，'point_id'值必须与参考资料完全一致

# 用户问题
{user_question}"""
            prompt_elapsed = time.time() - prompt_start
            log_with_time(f"[规格总结] [1.2] Prompt构建完成 (耗时: {prompt_elapsed:.2f}秒)，prompt长度: {len(prompt)} 字符")

            # 调用Ark模型生成总结
            ai_start = time.time()
            log_with_time(f"[规格总结] [1.3] 开始调用AI模型总结 (超时设置: 180秒)...")
            try:
                response = client.chat.completions.create(
                    model=Config.ARK_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一位专业的采购专家，能够基于知识库内容准确总结产品规格参数。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    timeout=180.0  # 设置180秒超时
                )
                ai_elapsed = time.time() - ai_start
                log_with_time(f"[规格总结] [1.3] AI调用完成 (耗时: {ai_elapsed:.2f}秒)")
                
                summary = response.choices[0].message.content.strip()
                log_with_time(f"[规格总结] [1.3] 总结内容长度: {len(summary)} 字符")
                
            except Exception as ai_error:
                ai_elapsed = time.time() - ai_start
                log_with_time(f"[规格总结] [1.3] AI调用失败 (耗时: {ai_elapsed:.2f}秒): {ai_error}")
                raise
            
            total_elapsed = time.time() - start_time
            log_with_time(f"[规格总结] 总结完成 (总耗时: {total_elapsed:.2f}秒)")
            
            # 返回总结和参考chunk
            # 注意：search_specs已经限制返回4个chunk，无需再次截取
            return {
                "summary": summary,
                "references": specs
            }
            
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_with_time(f"[规格总结] 规格总结失败 (总耗时: {total_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            # 如果总结失败，返回原始chunk
            log_with_time(f"[规格总结] 降级处理：返回原始chunk")
            specs = self.search_specs(product_name, None)  # 降级处理时也只使用product_name搜索
            return {
                "summary": f"总结失败，找到 {len(specs)} 条规格信息，请查看下方参考内容。",
                "references": specs  # search_specs已经限制返回4个chunk
            }
    
    def search_specs(self, product_name: str, product_features: str = None) -> List[SpecSource]:
        """
        搜索产品规格信息（原始chunk，不总结）
        注意：会排除供应商文档的内容，只返回规格相关的chunk
        
        Args:
            product_name: 产品名称
            product_features: 产品特征（可选）
            
        Returns:
            规格来源列表
        """
        start_time = time.time()
        specs = []
        
        try:
            # 构建搜索查询 - 明确查找规格相关信息
            query_start = time.time()
            if product_features:
                query = f"{product_name} {product_features} 规格 技术参数 配置要求"
            else:
                query = f"{product_name} 规格 技术参数 配置要求"
            query_elapsed = time.time() - query_start
            
            log_with_time(f"[知识库搜索-规格] 开始搜索，查询内容: {query}")
            log_with_time(f"[知识库搜索-规格] collection_id: {self.collection_id}, collection_name: {self.collection_name}")
            log_with_time(f"[知识库搜索-规格] 将排除供应商文档: group_doc_id={self.group_doc_id}, oilfield_doc_id={self.oilfield_doc_id}")
            
            # 调用知识库搜索API
            # 根据火山引擎知识库SDK文档，使用search_knowledge方法
            # 如果collection_id是ID格式，使用resource_id参数；否则使用collection_name
            try:
                # 构建post_processing参数（根据SDK官方示例）
                post_processing = {
                    "rerank_switch": Config.KNOWLEDGE_RERANK_SWITCH,
                    "rerank_model": Config.KNOWLEDGE_RERANK_MODEL,
                    "rerank_only_chunk": False,
                    "chunk_group": True,
                    "get_attachment_link": True,  # 获取图片链接
                }
                
                # 如果设置了retrieve_count，添加到post_processing中
                if Config.KNOWLEDGE_RETRIEVE_COUNT:
                    post_processing["retrieve_count"] = Config.KNOWLEDGE_RETRIEVE_COUNT
                
                # 构建搜索参数
                search_params = {
                    "query": query,
                    "limit": 4,  # 规格搜索只返回top4
                    "dense_weight": Config.KNOWLEDGE_DENSE_WEIGHT,
                    "post_processing": post_processing,
                }
                
                log_with_time(f"[知识库搜索-规格] 搜索参数: query={query}, limit=4, dense_weight={Config.KNOWLEDGE_DENSE_WEIGHT}")
                log_with_time(f"[知识库搜索-规格] post_processing: {post_processing}")
                
                # 调用知识库API
                api_start = time.time()
                if self.collection_name:
                    search_params["collection_name"] = self.collection_name
                    log_with_time(f"[知识库搜索-规格] 使用 collection_name: {self.collection_name}")
                    log_with_time(f"[知识库搜索-规格] 开始调用知识库API...")
                    response = self.service.search_knowledge(**search_params)
                else:
                    # 使用resource_id参数
                    search_params["collection_name"] = "default"  # 占位符，实际使用resource_id
                    search_params["resource_id"] = self.collection_id
                    log_with_time(f"[知识库搜索-规格] 使用 resource_id: {self.collection_id}")
                    log_with_time(f"[知识库搜索-规格] 开始调用知识库API...")
                    response = self.service.search_knowledge(**search_params)
                
                api_elapsed = time.time() - api_start
                log_with_time(f"[知识库搜索-规格] API调用完成 (耗时: {api_elapsed:.2f}秒)")
                log_with_time(f"[知识库搜索-规格] 响应类型: {type(response)}")
                log_with_time(f"[知识库搜索-规格] 响应是否为None: {response is None}")
                if response is not None:
                    if isinstance(response, list):
                        print(f"[知识库搜索] 响应是列表，长度: {len(response)}")
                        if len(response) == 0:
                            print(f"[知识库搜索] ⚠️ 警告：响应列表为空，没有找到匹配的结果")
                    elif isinstance(response, dict):
                        print(f"[知识库搜索] 响应是字典，键: {list(response.keys())}")
                        print(f"[知识库搜索] 响应字典完整内容: {response}")
                    else:
                        print(f"[知识库搜索] 响应是其他类型: {type(response)}, 值: {str(response)[:500]}")
                else:
                    print(f"[知识库搜索] ⚠️ 警告：API返回None，可能没有找到匹配的结果")
                
                # 解析响应，提取规格信息和切片来源
                # 响应格式可能因SDK版本而异，需要根据实际响应调整
                parse_start = time.time()
                if response:
                    log_with_time(f"[知识库搜索-规格] 开始解析响应，响应不为空")
                    # 如果响应是列表
                    if isinstance(response, list):
                        for point in response:
                            # 处理Point对象
                            if hasattr(point, 'content'):
                                # Point对象，直接访问属性
                                doc_name = None
                                if hasattr(point, 'doc_info') and point.doc_info:
                                    # doc_info是Doc对象
                                    if hasattr(point.doc_info, 'doc_name'):
                                        doc_name = point.doc_info.doc_name
                                    elif hasattr(point.doc_info, 'name'):
                                        doc_name = point.doc_info.name
                                    elif isinstance(point.doc_info, dict):
                                        doc_name = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
                                
                                # 提取图片链接
                                image_url = None
                                chunk_type = None
                                
                                # 调试：打印所有可用属性
                                if hasattr(point, 'chunk_attachment'):
                                    print(f"[知识库调试] chunk_attachment 类型: {type(point.chunk_attachment)}, 值: {point.chunk_attachment}")
                                
                                if hasattr(point, 'chunk_type'):
                                    print(f"[知识库调试] chunk_type: {point.chunk_type}")
                                
                                if hasattr(point, 'chunk_attachment') and point.chunk_attachment:
                                    # chunk_attachment 是列表
                                    if isinstance(point.chunk_attachment, list) and len(point.chunk_attachment) > 0:
                                        attachment = point.chunk_attachment[0]
                                        print(f"[知识库调试] attachment 类型: {type(attachment)}, 值: {attachment}")
                                        if isinstance(attachment, dict):
                                            image_url = attachment.get('link', '')
                                            print(f"[知识库调试] 从字典提取 image_url: {image_url}")
                                        elif hasattr(attachment, 'link'):
                                            image_url = attachment.link
                                            print(f"[知识库调试] 从对象提取 image_url: {image_url}")
                                
                                if hasattr(point, 'chunk_type'):
                                    chunk_type = point.chunk_type
                                
                                # 打印所有point的属性
                                print(f"[知识库调试] Point对象属性: {[attr for attr in dir(point) if not attr.startswith('_')]}")
                                
                                # 检查是否来自供应商文档，如果是则跳过
                                point_doc_id = point.doc_id or ''
                                if point_doc_id == self.group_doc_id or point_doc_id == self.oilfield_doc_id:
                                    print(f"[知识库搜索-规格] 跳过供应商文档的chunk: doc_id={point_doc_id}")
                                    continue
                                
                                # 使用辅助函数提取完整chunk信息
                                chunk_info = extract_chunk_info(point)
                                
                                # 如果doc_name在辅助函数中未提取到，使用之前提取的值
                                if not chunk_info["doc_name"]:
                                    chunk_info["doc_name"] = doc_name
                                if not chunk_info["image_url"]:
                                    chunk_info["image_url"] = image_url
                                
                                spec = SpecSource(
                                    content=chunk_info["content"],
                                    slice_id=chunk_info["slice_id"],
                                    doc_id=chunk_info["doc_id"],
                                    doc_name=chunk_info["doc_name"],
                                    image_url=chunk_info["image_url"],
                                    chunk_type=chunk_info["chunk_type"],
                                    md_content=chunk_info["md_content"],
                                    html_content=chunk_info["html_content"],
                                    point_id=chunk_info["point_id"]
                                )
                                print(f"[知识库调试] 创建的 SpecSource: image_url={chunk_info['image_url']}, chunk_type={chunk_info['chunk_type']}, content长度={len(chunk_info['content'])}")
                                specs.append(spec)
                            elif isinstance(point, dict):
                                # 字典格式
                                print(f"[知识库调试] 点数据键: {list(point.keys())}")
                                print(f"[知识库调试] 点数据完整内容: {point}")
                                
                                # 提取图片链接
                                image_url = None
                                chunk_type = point.get('chunk_type')
                                chunk_attachment = point.get('chunk_attachment', [])
                                print(f"[知识库调试] chunk_attachment: {chunk_attachment}, 类型: {type(chunk_attachment)}")
                                if isinstance(chunk_attachment, list) and len(chunk_attachment) > 0:
                                    attachment = chunk_attachment[0]
                                    print(f"[知识库调试] attachment: {attachment}, 类型: {type(attachment)}")
                                    if isinstance(attachment, dict):
                                        image_url = attachment.get('link', '')
                                        print(f"[知识库调试] 提取的 image_url: {image_url}")
                                
                                # 检查是否来自供应商文档，如果是则跳过
                                point_doc_id = point.get('doc_id', point.get('document_id', ''))
                                if point_doc_id == self.group_doc_id or point_doc_id == self.oilfield_doc_id:
                                    print(f"[知识库搜索-规格] 跳过供应商文档的chunk: doc_id={point_doc_id}")
                                    continue
                                
                                # 使用辅助函数提取完整chunk信息
                                chunk_info = extract_chunk_info(point)
                                
                                spec = SpecSource(
                                    content=chunk_info["content"],
                                    slice_id=chunk_info["slice_id"],
                                    doc_id=chunk_info["doc_id"],
                                    doc_name=chunk_info["doc_name"],
                                    image_url=chunk_info["image_url"],
                                    chunk_type=chunk_info["chunk_type"],
                                    md_content=chunk_info["md_content"],
                                    html_content=chunk_info["html_content"],
                                    point_id=chunk_info["point_id"]
                                )
                                print(f"[知识库调试] 创建的 SpecSource (字典): image_url={chunk_info['image_url']}, chunk_type={chunk_info['chunk_type']}, content长度={len(chunk_info['content'])}")
                                specs.append(spec)
                    # 如果响应是字典
                    elif isinstance(response, dict):
                        print(f"[知识库搜索] 响应是字典格式，开始解析")
                        # 尝试多种可能的键名，包括result_list
                        points = response.get('result_list', response.get('points', response.get('data', response.get('chunks', response.get('results', [])))))
                        print(f"[知识库搜索] 从字典中提取的points类型: {type(points)}, 长度: {len(points) if isinstance(points, list) else 'N/A'}")
                        if isinstance(points, list):
                            print(f"[知识库搜索] points是列表，包含 {len(points)} 个项目")
                            for point in points:
                                # 处理Point对象
                                if hasattr(point, 'content'):
                                    doc_name = None
                                    if hasattr(point, 'doc_info') and point.doc_info:
                                        if isinstance(point.doc_info, dict):
                                            doc_name = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
                                        elif hasattr(point.doc_info, 'doc_name'):
                                            doc_name = point.doc_info.doc_name
                                    
                                    # 提取图片链接
                                    image_url = None
                                    chunk_type = None
                                    if hasattr(point, 'chunk_attachment') and point.chunk_attachment:
                                        if isinstance(point.chunk_attachment, list) and len(point.chunk_attachment) > 0:
                                            attachment = point.chunk_attachment[0]
                                            if isinstance(attachment, dict):
                                                image_url = attachment.get('link', '')
                                            elif hasattr(attachment, 'link'):
                                                image_url = attachment.link
                                    
                                    if hasattr(point, 'chunk_type'):
                                        chunk_type = point.chunk_type
                                    
                                    # 检查是否来自供应商文档，如果是则跳过
                                    point_doc_id = point.doc_id or ''
                                    if point_doc_id == self.group_doc_id or point_doc_id == self.oilfield_doc_id:
                                        print(f"[知识库搜索-规格] 跳过供应商文档的chunk: doc_id={point_doc_id}")
                                        continue
                                    
                                    spec = SpecSource(
                                        content=point.content or '',
                                        slice_id=point.point_id or point.chunk_id or '',
                                        doc_id=point.doc_id or '',
                                        doc_name=doc_name,
                                        image_url=image_url,
                                        chunk_type=chunk_type
                                    )
                                    specs.append(spec)
                                elif isinstance(point, dict):
                                    # 提取文档信息
                                    doc_info = point.get('doc_info', {})
                                    if isinstance(doc_info, dict):
                                        doc_name = doc_info.get('doc_name', doc_info.get('name', ''))
                                        doc_id = doc_info.get('doc_id', point.get('doc_id', ''))
                                    else:
                                        doc_name = point.get('doc_name', point.get('document_name', ''))
                                        doc_id = point.get('doc_id', point.get('document_id', ''))
                                    
                                    # 提取图片链接
                                    image_url = None
                                    chunk_type = point.get('chunk_type')
                                    chunk_attachment = point.get('chunk_attachment', [])
                                    if isinstance(chunk_attachment, list) and len(chunk_attachment) > 0:
                                        attachment = chunk_attachment[0]
                                        if isinstance(attachment, dict):
                                            image_url = attachment.get('link', '')
                                    
                                    # 检查是否来自供应商文档，如果是则跳过
                                    if doc_id == self.group_doc_id or doc_id == self.oilfield_doc_id:
                                        print(f"[知识库搜索-规格] 跳过供应商文档的chunk: doc_id={doc_id}")
                                        continue
                                    
                                    # 处理内容编码问题
                                    content = point.get('content', point.get('text', point.get('chunk', '')))
                                    if isinstance(content, bytes):
                                        try:
                                            content = content.decode('utf-8')
                                        except:
                                            try:
                                                content = content.decode('gbk')
                                            except:
                                                content = content.decode('utf-8', errors='ignore')
                                    
                                    spec = SpecSource(
                                        content=content,
                                        slice_id=point.get('point_id', point.get('id', point.get('chunk_id', ''))),
                                        doc_id=doc_id,
                                        doc_name=doc_name,
                                        image_url=image_url,
                                        chunk_type=chunk_type
                                    )
                                    print(f"[知识库调试] 创建的 SpecSource (字典): doc_name={doc_name}, image_url={image_url}, chunk_type={chunk_type}, content长度={len(content)}")
                                    specs.append(spec)
                else:
                    print(f"[知识库搜索] 响应为空，跳过解析")
            except AttributeError as e:
                # 如果方法名不同，尝试其他可能的方法名
                # search_knowledge, search_collection, search等
                print(f"[知识库搜索] 方法调用失败 (AttributeError): {e}")
                print(f"[知识库搜索] 尝试使用 search_collection 方法...")
                try:
                    # 尝试使用旧的search_collection方法
                    if self.collection_name:
                        response = self.service.search_collection(
                            collection_name=self.collection_name,
                            query=query,
                            limit=5  # 规格搜索只返回top4
                        )
                    else:
                        response = self.service.search_collection(
                            resource_id=self.collection_id,
                            query=query,
                            limit=5    # 规格搜索只返回top4
                        )
                    print(f"[知识库搜索] 使用 search_collection 方法成功")
                except Exception as e2:
                    print(f"[知识库搜索] search_collection 也失败: {e2}")
                    import traceback
                    traceback.print_exc()
            except Exception as e:
                print(f"[知识库搜索] API调用异常: {e}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_with_time(f"[知识库搜索-规格] 知识库规格搜索失败 (总耗时: {total_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
        
        total_elapsed = time.time() - start_time
        log_with_time(f"[知识库搜索-规格] 最终返回 {len(specs)} 条规格 (总耗时: {total_elapsed:.2f}秒)")
        
        # 直接返回搜索结果，不进行筛选
        # 筛选功能由answer_question方法中的Ark模型完成
        # 注意：知识库API已经限制返回4个chunk，无需再次截取
        return specs
    
    def search_suppliers_from_docs(self, product_name: str, product_features: str = None) -> List[SupplierInfo]:
        """
        从指定文档中搜索供应商信息
        只从供应商文档中搜索，并使用AI过滤不相关的供应商
        优化：一次调用知识库API，然后过滤两个文档的结果
        
        Args:
            product_name: 产品名称
            product_features: 产品特征/规格描述（可选）
            
        Returns:
            供应商信息列表（已过滤）
        """
        start_time = time.time()
        log_with_time(f"[供应商搜索] 开始搜索供应商: {product_name}")
        suppliers = []
        
        # 优化：一次调用知识库API，返回更多结果，然后过滤两个文档
        # 这样可以减少一次知识库API调用
        try:
            # 构建搜索查询
            if product_features:
                query = f"{product_name} {product_features} 供应商 厂家 定商"
            else:
                query = f"{product_name} 供应商 厂家 定商"
            
            log_with_time(f"[供应商搜索] 开始调用知识库API（使用doc_filter直接指定两个定商文档）...")
            
            # 构建doc_filter，直接指定只搜索两个定商文档
            doc_filter = {
                "op": "must",  # 查询算子 must/must_not/range/range_out
                "field": "doc_id",
                "conds": [self.group_doc_id, self.oilfield_doc_id]  # 指定两个定商文档ID
            }
            
            # 使用search_knowledge方法搜索
            post_processing = {
                "rerank_switch": Config.KNOWLEDGE_RERANK_SWITCH,
                "rerank_model": Config.KNOWLEDGE_RERANK_MODEL,
                "rerank_only_chunk": False,
                "chunk_group": True,
                "get_attachment_link": True,
            }
            
            # query_param中包含doc_filter
            query_param = {
                "doc_filter": doc_filter
            }
            
            search_params = {
                "query": query,
                "limit": 15,  # 返回15个结果（两个文档合计）
                "dense_weight": Config.KNOWLEDGE_DENSE_WEIGHT,
                "post_processing": post_processing,
                "query_param": query_param,  # 添加query_param，包含doc_filter
            }
            
            api_start = time.time()
            if self.collection_name:
                search_params["collection_name"] = self.collection_name
                response = self.service.search_knowledge(**search_params)
            else:
                search_params["collection_name"] = "default"
                search_params["resource_id"] = self.collection_id
                response = self.service.search_knowledge(**search_params)
            api_elapsed = time.time() - api_start
            log_with_time(f"[供应商搜索] 知识库API调用完成 (耗时: {api_elapsed:.2f}秒)")
            
            # 解析响应，收集所有结果（不再区分文档）
            # 注意：由于使用了doc_filter，返回的结果已经都是这两个文档的了
            if response:
                # 收集所有structured points和text suppliers
                all_structured_points = []  # [(point, slice_id, doc_id, doc_name), ...]
                text_suppliers = []
                
                # 文档ID到文档名称的映射
                doc_id_to_name = {
                    self.group_doc_id: "集团定商采购",
                    self.oilfield_doc_id: "油田定商采购"
                }
                
                # 处理字典响应
                if isinstance(response, dict):
                    points = response.get('result_list', response.get('points', []))
                    for point in points:
                        if isinstance(point, dict):
                            # 获取文档ID和文档名称
                            doc_info = point.get('doc_info', {})
                            point_doc_id = doc_info.get('doc_id', '') if isinstance(doc_info, dict) else point.get('doc_id', '')
                            point_doc_name = doc_id_to_name.get(point_doc_id, "未知文档")
                            
                            chunk_type = point.get('chunk_type', '')
                            point_slice_id = point.get('point_id', point.get('id', point.get('chunk_id', '')))
                            
                            if chunk_type == 'structured':
                                # 收集structured points，包含doc_id和doc_name信息
                                all_structured_points.append((point, point_slice_id, point_doc_id, point_doc_name))
                            else:
                                # 处理文本类型的供应商
                                content = point.get('content', '')
                                supplier_name = self._extract_supplier_name(content)
                                if supplier_name:
                                    text_suppliers.append(SupplierInfo(
                                        name=supplier_name,
                                        source="knowledge_base",
                                        doc_id=point_doc_id,
                                        doc_name=point_doc_name,
                                        description=content[:200],
                                        slice_id=point_slice_id,
                                        content=content
                                    ))
                
                # 处理列表响应（Point对象列表）
                elif isinstance(response, list):
                    for point in response:
                        if hasattr(point, 'content'):
                            content = point.content or ''
                            point_doc_id = getattr(point, 'doc_id', '')
                            point_doc_name = doc_id_to_name.get(point_doc_id, "未知文档")
                            
                            chunk_type = getattr(point, 'chunk_type', '')
                            slice_id = point.point_id or point.chunk_id or ''
                            
                            if chunk_type == 'structured':
                                # 收集structured points，包含doc_id和doc_name信息
                                all_structured_points.append((point, slice_id, point_doc_id, point_doc_name))
                            else:
                                # 处理文本类型的供应商
                                supplier_name = self._extract_supplier_name(content)
                                if supplier_name:
                                    text_suppliers.append(SupplierInfo(
                                        name=supplier_name,
                                        source="knowledge_base",
                                        doc_id=point_doc_id,
                                        doc_name=point_doc_name,
                                        description=content[:200],
                                        slice_id=slice_id,
                                        content=content
                                    ))
                
                # 批量处理所有structured points（一次性调用LLM，不再区分文档）
                if all_structured_points:
                    log_with_time(f"[供应商搜索] 找到 {len(all_structured_points)} 个structured类型的chunks，开始批量提取...")
                    batch_suppliers = self._extract_suppliers_batch(
                        all_structured_points,
                        product_name=product_name,
                        product_features=product_features
                    )
                    suppliers.extend(batch_suppliers)
                    log_with_time(f"[供应商搜索] 批量提取完成，找到 {len(batch_suppliers)} 个相关供应商")
                
                # 添加文本类型的供应商
                suppliers.extend(text_suppliers)
                
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_with_time(f"[供应商搜索] 搜索失败 (总耗时: {total_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
        
        total_elapsed = time.time() - start_time
        log_with_time(f"[供应商搜索] 搜索完成 (总耗时: {total_elapsed:.2f}秒)，共找到 {len(suppliers)} 个供应商")
        
        return suppliers
    
    def _search_suppliers_in_doc(self, product_name: str, product_features: str = None, doc_id: str = None, doc_name: str = None) -> List[SupplierInfo]:
        """
        在指定文档中搜索供应商
        
        Args:
            product_name: 产品名称
            product_features: 产品特征/规格描述（可选）
            doc_id: 文档ID
            doc_name: 文档名称
            
        Returns:
            供应商信息列表
        """
        start_time = time.time()
        suppliers = []
        
        try:
            if not doc_id:
                log_with_time(f"[供应商搜索-{doc_name}] doc_id为空，跳过搜索")
                return suppliers
            
            # 构建搜索查询 - 根据产品名称和规格描述判断产品类型，然后找供应商
            # 首先根据产品名称和规格描述判断产品类型，然后搜索对应的供应商
            if product_features:
                # 结合产品名称和规格描述，判断产品类型并搜索供应商
                query = f"{product_name} {product_features} 供应商 厂家 定商"
            else:
                # 仅根据产品名称判断产品类型并搜索供应商
                query = f"{product_name} 供应商 厂家 定商"
            
            log_with_time(f"[供应商搜索-{doc_name}] 在文档中搜索，查询内容: {query}")
            
            # 搜索文档中的相关信息
            # 注意：实际API方法可能需要根据SDK版本调整
            try:
                # 使用search_knowledge方法搜索（根据SDK官方示例）
                post_processing = {
                    "rerank_switch": Config.KNOWLEDGE_RERANK_SWITCH,
                    "rerank_model": Config.KNOWLEDGE_RERANK_MODEL,
                    "rerank_only_chunk": False,
                    "chunk_group": True,
                    "get_attachment_link": True,
                }
                
                search_params = {
                    "query": query,
                    "limit": 30,  # 返回30个结果，后续通过AI过滤
                    "dense_weight": Config.KNOWLEDGE_DENSE_WEIGHT,
                    "post_processing": post_processing,
                }
                
                api_start = time.time()
                if self.collection_name:
                    search_params["collection_name"] = self.collection_name
                    log_with_time(f"[供应商搜索-{doc_name}] 开始调用知识库API...")
                    response = self.service.search_knowledge(**search_params)
                else:
                    search_params["collection_name"] = "default"
                    search_params["resource_id"] = self.collection_id
                    log_with_time(f"[供应商搜索-{doc_name}] 开始调用知识库API...")
                    response = self.service.search_knowledge(**search_params)
                api_elapsed = time.time() - api_start
                log_with_time(f"[供应商搜索-{doc_name}] API调用完成 (耗时: {api_elapsed:.2f}秒)")
            except AttributeError:
                # 如果方法不存在，尝试其他方法
                log_with_time(f"[供应商搜索-{doc_name}] 知识库文档搜索方法调用失败，请检查SDK版本")
                return suppliers
            
            # 解析响应，提取供应商信息
            if response:
                # 先收集所有structured类型的points，然后批量处理
                structured_points = []
                text_points = []
                
                # 处理字典响应（包含result_list）
                if isinstance(response, dict):
                    points = response.get('result_list', response.get('points', []))
                    for point in points:
                        if isinstance(point, dict):
                            # 检查是否属于指定文档
                            doc_info = point.get('doc_info', {})
                            point_doc_id = doc_info.get('doc_id', '') if isinstance(doc_info, dict) else point.get('doc_id', '')
                            
                            if point_doc_id == doc_id:
                                chunk_type = point.get('chunk_type', '')
                                point_slice_id = point.get('point_id', point.get('id', point.get('chunk_id', '')))
                                if chunk_type == 'structured':
                                    # 收集structured类型的points，后续批量处理
                                    structured_points.append((point, point_slice_id))
                                else:
                                    # 处理普通文本数据
                                    content = point.get('content', '')
                                    supplier_name = self._extract_supplier_name(content)
                                    if supplier_name:
                                        supplier = SupplierInfo(
                                            name=supplier_name,
                                            source="knowledge_base",
                                            doc_id=doc_id,
                                            doc_name=doc_name,
                                            description=content[:200],
                                            slice_id=point_slice_id,
                                            content=content
                                        )
                                        suppliers.append(supplier)
                # 处理列表响应（Point对象列表）
                elif isinstance(response, list):
                    for point in response:
                        # 处理Point对象
                        if hasattr(point, 'content'):
                            content = point.content or ''
                            # 检查是否属于指定文档
                            if hasattr(point, 'doc_id') and point.doc_id == doc_id:
                                chunk_type = getattr(point, 'chunk_type', '')
                                slice_id = point.point_id or point.chunk_id or ''
                                if chunk_type == 'structured':
                                    # 收集structured类型的points
                                    structured_points.append((point, slice_id))
                                else:
                                    supplier_name = self._extract_supplier_name(content)
                                    if supplier_name:
                                        supplier = SupplierInfo(
                                            name=supplier_name,
                                            source="knowledge_base",
                                            doc_id=doc_id,
                                            doc_name=doc_name,
                                            description=content[:200],
                                            slice_id=slice_id,
                                            content=content
                                        )
                                        suppliers.append(supplier)
                
                # 批量处理所有structured类型的points（一次性调用LLM）
                if structured_points:
                    log_with_time(f"[供应商搜索-{doc_name}] 找到 {len(structured_points)} 个structured类型的chunks，开始批量提取供应商...")
                    # 转换为新格式：[(point, slice_id, doc_id, doc_name), ...]
                    points_with_info = [(point, slice_id, doc_id, doc_name) for point, slice_id in structured_points]
                    batch_suppliers = self._extract_suppliers_batch(
                        points_with_info,
                        product_name=product_name,
                        product_features=product_features
                    )
                    suppliers.extend(batch_suppliers)
                    log_with_time(f"[供应商搜索-{doc_name}] 批量提取完成，找到 {len(batch_suppliers)} 个相关供应商")
        
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_with_time(f"[供应商搜索-{doc_name}] 在文档中搜索供应商失败 (总耗时: {total_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
        
        total_elapsed = time.time() - start_time
        log_with_time(f"[供应商搜索-{doc_name}] 搜索完成 (总耗时: {total_elapsed:.2f}秒)，找到 {len(suppliers)} 个供应商")
        return suppliers
    
    def _extract_suppliers_batch(self, points_with_info: List[tuple], product_name: str = None, product_features: str = None) -> List[SupplierInfo]:
        """
        批量从多个structured类型的points中提取供应商信息
        一次性调用LLM，大幅减少调用次数
        支持处理来自不同文档的points
        
        Args:
            points_with_info: [(point, slice_id, doc_id, doc_name), ...] 元组列表
            product_name: 产品名称（用于判断相关性）
            product_features: 产品特征（用于判断相关性）
            
        Returns:
            供应商信息列表（已过滤，只返回相关的供应商）
        """
        start_time = time.time()
        suppliers = []
        
        try:
            if not points_with_info:
                return suppliers
            
            api_key = Config.ARK_API_KEY
            if not api_key:
                # 如果没有配置API key，使用旧的逐个提取方法
                log_with_time(f"[供应商批量提取] 未配置ARK_API_KEY，使用逐个提取方法")
                for point, slice_id, doc_id, doc_name in points_with_info:
                    supplier = self._extract_supplier_from_structured(
                        point, doc_id, doc_name, slice_id,
                        product_name=product_name,
                        product_features=product_features
                    )
                    if supplier:
                        suppliers.append(supplier)
                return suppliers
            
            client = OpenAI(
                api_key=api_key,
                base_url=Config.ARK_BASE_URL,
                timeout=180.0,  # 设置180秒超时
            )
            
            # 构建所有表格数据的文本
            MAX_FIELD_LENGTH = 200  # 每个字段值最多200字符
            MAX_TABLE_LENGTH = 500  # 每个表格最多500字符
            MAX_TOTAL_LENGTH = 8000  # 总长度最多8000字符（支持更多表格）
            
            tables_data = []
            for idx, (point, slice_id, doc_id, doc_name) in enumerate(points_with_info):
                # 获取表格字段和内容（兼容dict和对象）
                if isinstance(point, dict):
                    table_fields = point.get('table_chunk_fields', [])
                    content = point.get('content', '')
                else:
                    # Point对象
                    table_fields = getattr(point, 'table_chunk_fields', [])
                    content = getattr(point, 'content', '')
                    # 如果table_chunk_fields是对象列表，转换为字典列表
                    if table_fields and not isinstance(table_fields[0] if table_fields else None, dict):
                        table_fields = [{'field_value': str(field)} for field in table_fields]
                
                if not table_fields and not content:
                    continue
                
                # 构建单个表格数据文本
                table_data_text = ""
                if table_fields:
                    field_values = []
                    for field in table_fields:
                        field_value = field.get('field_value', '').strip() if isinstance(field, dict) else str(field).strip()
                        if field_value:
                            # 限制每个字段值的长度
                            if len(field_value) > MAX_FIELD_LENGTH:
                                field_value = field_value[:MAX_FIELD_LENGTH] + "..."
                            field_values.append(field_value)
                    table_data_text = " | ".join(field_values)
                    
                    # 限制单个表格长度
                    if len(table_data_text) > MAX_TABLE_LENGTH:
                        table_data_text = table_data_text[:MAX_TABLE_LENGTH] + "..."
                
                if content:
                    content_limited = content[:MAX_FIELD_LENGTH] if len(content) > MAX_FIELD_LENGTH else content
                    if table_data_text:
                        combined = f"{table_data_text}\n内容: {content_limited}"
                        if len(combined) > MAX_TABLE_LENGTH:
                            combined = table_data_text  # 只保留表格数据
                        table_data_text = combined
                    else:
                        table_data_text = content_limited[:MAX_TABLE_LENGTH]
                
                if table_data_text:
                    tables_data.append(f"表格{idx+1}:\n{table_data_text}")
            
            if not tables_data:
                log_with_time(f"[供应商批量提取] 没有有效的表格数据")
                return suppliers
            
            # 合并所有表格数据
            all_tables_text = "\n\n".join(tables_data)
            
            # 如果总长度超过限制，截断
            if len(all_tables_text) > MAX_TOTAL_LENGTH:
                all_tables_text = all_tables_text[:MAX_TOTAL_LENGTH] + "..."
                log_with_time(f"[供应商批量提取] 表格数据总长度超过限制，已截断")
            
            # 构建产品查询信息（用于判断相关性）
            product_query = product_name or ""
            if product_features:
                product_query += f" {product_features}"
            
            # 构建prompt，一次性处理所有表格
            if product_query:
                prompt = f"""请从以下多个表格数据中提取所有与产品"{product_query}"相关的供应商信息。

表格数据：
{all_tables_text}

任务要求：
1. 从所有表格中提取供应商信息（如果存在）
2. 判断每个供应商与产品"{product_query}"的相关性：
   - "强相关"：产品名称判断属于供应商的物资类别
   - "可能相关"：产品名称判断不属于供应商的物资类别，但存在一定关联性
3. 优先返回"强相关"的供应商
4. 如果没有"强相关"的供应商，返回top 5个"可能相关"的供应商（按相关性排序）
5. 完全不相关的供应商不返回

请提取以下字段（如果存在）：
- supplier_name: 供应商名称（必填）
- supplier_type: 供应商类型（制造商/供货商）
- sub_category_name: 子分类名称（物资类别）
- valid_from: 有效期开始日期
- valid_to: 有效期结束日期
- contact_person: 联系人
- table_index: 表格编号（1, 2, 3...）
- relevance: 相关性标记（"强相关" 或 "可能相关"）

返回格式（JSON数组）：
[
    {{
        "supplier_name": "供应商名称",
        "supplier_type": "制造商或供货商",
        "sub_category_name": "子分类名称（物资类别）",
        "valid_from": "有效期开始",
        "valid_to": "有效期结束",
        "contact_person": "联系人",
        "table_index": 1,
        "relevance": "强相关"
    }},
    ...
]

如果找不到任何相关供应商，返回空数组：[]"""
            else:
                prompt = f"""请从以下多个表格数据中提取所有供应商信息，并以JSON数组格式返回。

表格数据：
{all_tables_text}

请提取以下字段（如果存在）：
- supplier_name: 供应商名称（必填）
- supplier_type: 供应商类型（制造商/供货商）
- sub_category_name: 子分类名称（物资类别）
- valid_from: 有效期开始日期
- valid_to: 有效期结束日期
- contact_person: 联系人
- table_index: 表格编号（1, 2, 3...）

返回格式（JSON数组）：
[
    {{
        "supplier_name": "供应商名称",
        "supplier_type": "制造商或供货商",
        "sub_category_name": "子分类名称（物资类别）",
        "valid_from": "有效期开始",
        "valid_to": "有效期结束",
        "contact_person": "联系人",
        "table_index": 1
    }},
    ...
]

如果找不到任何供应商，返回空数组：[]"""
            
            log_with_time(f"[供应商批量提取] 开始调用LLM，表格数量: {len(tables_data)}，总长度: {len(all_tables_text)} 字符")
            
            # 调用AI批量解析
            max_retries = 2
            retry_delay = 2
            
            for attempt in range(max_retries + 1):
                try:
                    llm_start = time.time()
                    response = client.chat.completions.create(
                        model=Config.ARK_MODEL,
                        messages=[
                            {"role": "system", "content": "你是一个专业的数据提取助手，能够准确从多个表格数据中批量提取供应商信息，并判断供应商与产品的相关性。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=2000,  # 增加token数量以支持多个供应商
                        timeout=180.0  # 设置180秒超时
                    )
                    llm_elapsed = time.time() - llm_start
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    # 解析JSON结果
                    import json
                    try:
                        # 尝试提取JSON部分
                        if result_text.startswith("```json"):
                            result_text = result_text.replace("```json", "").replace("```", "").strip()
                        elif result_text.startswith("```"):
                            result_text = result_text.replace("```", "").strip()
                        
                        # 解析JSON数组
                        results = json.loads(result_text)
                        
                        if not isinstance(results, list):
                            results = [results] if results else []
                        
                        log_with_time(f"[供应商批量提取] LLM调用完成 (耗时: {llm_elapsed:.2f}秒)，返回 {len(results)} 个供应商")
                        
                        # 分离强相关和可能相关的供应商
                        strong_relevant = []
                        possible_relevant = []
                        
                        # 转换为SupplierInfo对象
                        for result in results:
                            if not result.get("supplier_name"):
                                continue
                            
                            # 获取对应的slice_id、doc_id和doc_name，以及原始内容
                            table_index = result.get("table_index", 1) - 1  # 转换为0-based索引
                            if 0 <= table_index < len(points_with_info):
                                point, slice_id, doc_id, doc_name = points_with_info[table_index]
                                
                                # 使用extract_chunk_info获取完整的point信息
                                chunk_info = extract_chunk_info(point)
                                
                                # 获取原始内容用于查看原文（完整数据，不截断）
                                if isinstance(point, dict):
                                    table_fields = point.get('table_chunk_fields', [])
                                    content = point.get('content', '') or chunk_info.get('content', '')
                                else:
                                    table_fields = getattr(point, 'table_chunk_fields', [])
                                    content = getattr(point, 'content', '') or chunk_info.get('content', '')
                                
                                # 构建完整的原始内容（包含字段名和字段值）
                                original_content_parts = []
                                
                                # 优先使用table_fields（如果有）
                                if table_fields:
                                    for field in table_fields:
                                        if isinstance(field, dict):
                                            field_name = field.get('field_name', '')
                                            field_value = field.get('field_value', '')
                                            if field_name and field_value:
                                                original_content_parts.append(f"{field_name}: {field_value}")
                                            elif field_value:
                                                original_content_parts.append(str(field_value))
                                        else:
                                            field_str = str(field).strip()
                                            if field_str:
                                                original_content_parts.append(field_str)
                                
                                # 添加content内容
                                if content:
                                    original_content_parts.append(content)
                                
                                # 如果仍然为空，尝试从chunk_info获取
                                if not original_content_parts:
                                    if chunk_info.get('content'):
                                        original_content_parts.append(chunk_info['content'])
                                    if chunk_info.get('md_content'):
                                        original_content_parts.append(f"Markdown:\n{chunk_info['md_content']}")
                                    if chunk_info.get('html_content'):
                                        original_content_parts.append(f"HTML:\n{chunk_info['html_content']}")
                                
                                original_content = "\n".join(original_content_parts) if original_content_parts else ""
                                
                                # 如果仍然为空，尝试序列化整个point对象（作为最后手段）
                                if not original_content:
                                    try:
                                        import json
                                        if isinstance(point, dict):
                                            original_content = json.dumps(point, ensure_ascii=False, indent=2)
                                        else:
                                            # 尝试将对象转换为字典
                                            point_dict = {}
                                            if hasattr(point, '__dict__'):
                                                point_dict = point.__dict__
                                            elif hasattr(point, '__slots__'):
                                                point_dict = {slot: getattr(point, slot, None) for slot in point.__slots__}
                                            if point_dict:
                                                original_content = json.dumps(point_dict, ensure_ascii=False, indent=2, default=str)
                                            else:
                                                original_content = str(point)
                                    except Exception as e:
                                        log_with_time(f"[供应商批量提取] 序列化point失败: {e}")
                                        original_content = f"无法提取原始内容，point类型: {type(point)}"
                            else:
                                slice_id = ""
                                doc_id = ""
                                doc_name = ""
                                original_content = ""
                            
                            # 获取相关性标记
                            relevance = result.get("relevance", "可能相关")
                            
                            # 记录原始内容长度，用于调试
                            content_len = len(original_content) if original_content else 0
                            log_with_time(f"[供应商批量提取] 供应商 {result['supplier_name']}, content长度: {content_len}, slice_id: {slice_id[:20] if slice_id else 'N/A'}...")
                            
                            supplier = SupplierInfo(
                                name=result["supplier_name"],
                                source="knowledge_base",
                                doc_id=doc_id,
                                doc_name=doc_name,
                                description=None,  # 不再使用description字段
                                slice_id=slice_id,
                                content=original_content,  # 保存完整的原始内容，用于查看原文
                                supplier_type=result.get("supplier_type"),
                                sub_category_name=result.get("sub_category_name"),
                                valid_from=result.get("valid_from"),
                                valid_to=result.get("valid_to"),
                                contact_person=result.get("contact_person"),
                                relevance=relevance  # 添加相关性标记
                            )
                            
                            # 根据相关性分类
                            if relevance == "强相关":
                                strong_relevant.append(supplier)
                            else:
                                possible_relevant.append(supplier)
                        
                        # 返回逻辑：优先返回强相关的，如果没有则返回top 5可能相关的
                        if strong_relevant:
                            suppliers = strong_relevant
                            log_with_time(f"[供应商批量提取] 找到 {len(strong_relevant)} 个强相关供应商")
                        else:
                            suppliers = possible_relevant[:5]  # 返回top 5可能相关的
                            log_with_time(f"[供应商批量提取] 未找到强相关供应商，返回 {len(suppliers)} 个可能相关的供应商")
                        
                        total_elapsed = time.time() - start_time
                        log_with_time(f"[供应商批量提取] 批量提取完成 (总耗时: {total_elapsed:.2f}秒)，成功提取 {len(suppliers)} 个供应商")
                        return suppliers
                        
                    except json.JSONDecodeError as e:
                        log_with_time(f"[供应商批量提取] AI返回的JSON解析失败: {e}, 返回内容: {result_text[:500]}")
                        if attempt < max_retries:
                            log_with_time(f"[供应商批量提取] 第{attempt + 1}次尝试失败，{retry_delay}秒后重试...")
                            time.sleep(retry_delay)
                            continue
                        # 如果JSON解析失败，回退到逐个提取
                        log_with_time(f"[供应商批量提取] JSON解析失败，回退到逐个提取方法")
                        break
                    
                except Exception as e:
                    error_msg = str(e)
                    log_with_time(f"[供应商批量提取] 第{attempt + 1}次尝试失败: {error_msg}")
                    
                    # 如果是超时错误且还有重试机会，则重试
                    if ("timeout" in error_msg.lower() or "timed out" in error_msg.lower()) and attempt < max_retries:
                        log_with_time(f"[供应商批量提取] {retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # 其他错误，回退到逐个提取
                        log_with_time(f"[供应商批量提取] LLM调用失败，回退到逐个提取方法")
                        break
            
            # 如果批量提取失败，回退到逐个提取
            log_with_time(f"[供应商批量提取] 批量提取失败，使用逐个提取方法作为备选")
            for point, slice_id, doc_id, doc_name in points_with_info:
                try:
                    supplier = self._extract_supplier_from_structured(
                        point, doc_id, doc_name, slice_id,
                        product_name=product_name,
                        product_features=product_features
                    )
                    if supplier:
                        suppliers.append(supplier)
                except Exception as e:
                    log_with_time(f"[供应商批量提取] 逐个提取失败: {e}")
                    continue
            
            total_elapsed = time.time() - start_time
            log_with_time(f"[供应商批量提取] 完成 (总耗时: {total_elapsed:.2f}秒)，找到 {len(suppliers)} 个供应商")
            return suppliers
            
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_with_time(f"[供应商批量提取] 批量提取失败 (总耗时: {total_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            return suppliers
    
    def _extract_supplier_from_structured(self, point: dict, doc_id: str, doc_name: str, slice_id: str = '', product_name: str = None, product_features: str = None) -> Optional[SupplierInfo]:
        """
        从structured类型的数据中提取供应商信息，并同时判断是否与产品相关
        使用AI来解析表格格式，避免编码解析错位问题
        合并了提取和过滤两个步骤，减少LLM调用次数
        
        Args:
            point: 知识库返回的point数据
            doc_id: 文档ID
            doc_name: 文档名称
            slice_id: 切片ID
            product_name: 产品名称（用于判断相关性）
            product_features: 产品特征（用于判断相关性）
        """
        try:
            # 获取表格字段和内容
            table_fields = point.get('table_chunk_fields', [])
            content = point.get('content', '')
            
            if not table_fields and not content:
                return None
            
            # 使用AI解析表格数据
            api_key = Config.ARK_API_KEY
            if not api_key:
                # 如果没有配置API key，使用旧的解析方法
                slice_id = point.get('point_id', point.get('id', point.get('chunk_id', '')))
                return self._extract_supplier_from_structured_legacy(point, doc_id, doc_name, slice_id)
            
            client = OpenAI(
                api_key=api_key,
                base_url=Config.ARK_BASE_URL,
                timeout=180.0,  # 设置180秒超时
            )
            
            # 构建表格数据文本，限制长度
            MAX_FIELD_LENGTH = 200  # 每个字段值最多200字符
            MAX_TOTAL_LENGTH = 2000  # 总长度最多2000字符
            
            table_data_text = ""
            if table_fields:
                field_values = []
                for field in table_fields:
                    field_value = field.get('field_value', '').strip()
                    if field_value:
                        # 限制每个字段值的长度
                        if len(field_value) > MAX_FIELD_LENGTH:
                            field_value = field_value[:MAX_FIELD_LENGTH] + "..."
                        field_values.append(field_value)
                table_data_text = " | ".join(field_values)
                
                # 如果总长度超过限制，截断
                if len(table_data_text) > MAX_TOTAL_LENGTH:
                    table_data_text = table_data_text[:MAX_TOTAL_LENGTH] + "..."
            
            if content:
                # 限制content长度
                content_limited = content[:MAX_FIELD_LENGTH] if len(content) > MAX_FIELD_LENGTH else content
                if table_data_text:
                    # 检查总长度
                    combined = f"{table_data_text}\n内容: {content_limited}"
                    if len(combined) > MAX_TOTAL_LENGTH:
                        # 如果超长，只保留table_data_text
                        pass  # 不添加content
                    else:
                        table_data_text = combined
                else:
                    table_data_text = content_limited[:MAX_TOTAL_LENGTH]
            
            # 构建产品查询信息（用于判断相关性）
            product_query = product_name or ""
            if product_features:
                product_query += f" {product_features}"
            
            # 构建prompt，同时要求提取供应商信息和判断相关性
            if product_query:
                prompt = f"""请从以下表格数据中提取供应商信息，并判断该供应商是否与产品"{product_query}"相关。

表格数据：
{table_data_text}

任务要求：
1. 提取供应商信息（如果存在）
2. 判断该供应商是否与产品"{product_query}"相关
3. 如果供应商与产品不相关，返回null

请提取以下字段（如果存在）：
- supplier_name: 供应商名称（必填）
- supplier_type: 供应商类型（制造商/供货商）
- sub_category_name: 子分类名称（物资类别）
- valid_from: 有效期开始日期
- valid_to: 有效期结束日期
- contact_person: 联系人
- is_relevant: 是否与产品相关（true/false）

返回格式（JSON）：
{{
    "supplier_name": "供应商名称",
    "supplier_type": "制造商或供货商",
    "sub_category_name": "子分类名称（物资类别）",
    "valid_from": "有效期开始",
    "valid_to": "有效期结束",
    "contact_person": "联系人",
    "is_relevant": true
}}

如果无法提取供应商信息，或供应商与产品不相关（is_relevant为false），返回：null"""
            else:
                # 如果没有产品信息，只提取供应商信息
                prompt = f"""请从以下表格数据中提取供应商信息，并以JSON格式返回。如果无法提取供应商信息，返回null。

表格数据：
{table_data_text}

请提取以下字段（如果存在）：
- supplier_name: 供应商名称（必填）
- supplier_type: 供应商类型（制造商/供货商）
- sub_category_name: 子分类名称（物资类别）
- valid_from: 有效期开始日期
- valid_to: 有效期结束日期
- contact_person: 联系人

返回格式（JSON）：
{{
    "supplier_name": "供应商名称",
    "supplier_type": "制造商或供货商",
    "sub_category_name": "子分类名称（物资类别）",
    "valid_from": "有效期开始",
    "valid_to": "有效期结束",
    "contact_person": "联系人"
}}

如果无法提取供应商信息，返回：null"""

            # 记录内容长度，方便调试
            print(f"[供应商提取] 表格数据长度: {len(table_data_text)} 字符，产品查询: {product_query}")
            
            # 调用AI解析（合并提取和过滤）
            max_retries = 2
            retry_delay = 2
            
            for attempt in range(max_retries + 1):
                try:
                    response = client.chat.completions.create(
                        model=Config.ARK_MODEL,
                        messages=[
                            {"role": "system", "content": "你是一个专业的数据提取助手，能够准确从表格数据中提取供应商信息，并判断供应商与产品的相关性。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=500,
                        timeout=180.0  # 设置180秒超时
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    # 解析JSON结果
                    import json
                    try:
                        # 尝试提取JSON部分
                        if result_text.startswith("```json"):
                            result_text = result_text.replace("```json", "").replace("```", "").strip()
                        elif result_text.startswith("```"):
                            result_text = result_text.replace("```", "").strip()
                        
                        if result_text.lower() == "null":
                            return None
                        
                        result = json.loads(result_text)
                        
                        if not result.get("supplier_name"):
                            return None
                        
                        # 检查相关性（如果提供了产品信息）
                        if product_query and result.get("is_relevant") is False:
                            print(f"[供应商提取] 供应商 {result.get('supplier_name')} 与产品 {product_query} 不相关，跳过")
                            return None
                
                        print(f"[供应商提取] 成功提取供应商: {result['supplier_name']}, 相关性: {result.get('is_relevant', 'N/A')}")
                        
                        return SupplierInfo(
                            name=result["supplier_name"],
                            source="knowledge_base",
                            doc_id=doc_id,
                            doc_name=doc_name,
                            description=None,  # 不再使用description字段
                            slice_id=slice_id,
                            content=table_data_text,  # 保存原始表格数据，用于查看原文时显示所有信息
                            supplier_type=result.get("supplier_type"),
                            sub_category_name=result.get("sub_category_name"),
                            valid_from=result.get("valid_from"),
                            valid_to=result.get("valid_to"),
                            contact_person=result.get("contact_person")
                        )
                    except json.JSONDecodeError as e:
                        print(f"[供应商提取] AI返回的JSON解析失败: {e}, 返回内容: {result_text}")
                        if attempt < max_retries:
                            print(f"[供应商提取] 第{attempt + 1}次尝试失败，{retry_delay}秒后重试...")
                            import time
                            time.sleep(retry_delay)
                            continue
                        return None
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"[供应商提取] 第{attempt + 1}次尝试失败: {error_msg}")
                    
                    # 如果是超时错误且还有重试机会，则重试
                    if ("timeout" in error_msg.lower() or "timed out" in error_msg.lower()) and attempt < max_retries:
                        print(f"[供应商提取] {retry_delay}秒后重试...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        # 其他错误或重试次数用完，直接返回None
                        if attempt == max_retries:
                            print(f"[供应商提取] 达到最大重试次数，放弃提取")
                        raise
            
            return None
            
        except Exception as e:
            print(f"[供应商提取] 从structured数据提取供应商失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_supplier_from_structured_legacy(self, point: dict, doc_id: str, doc_name: str, slice_id: str = '') -> Optional[SupplierInfo]:
        """
        旧的解析方法（备用）
        """
        try:
            # 获取表格字段
            table_fields = point.get('table_chunk_fields', [])
            if not table_fields:
                return None
            
            # 将所有字段值按顺序收集
            field_values = []
            for field in table_fields:
                field_value = field.get('field_value', '').strip()
                if field_value:
                    field_values.append(field_value)
            
            if not field_values:
                return None
            
            # 简单的供应商名称提取
            supplier_name = None
            for value in field_values:
                if ('公司' in value or '集团' in value or '有限公司' in value) and value not in ['制造商', '供货商', '定商定价']:
                    supplier_name = value
                    break
            
            if not supplier_name:
                return None
            
            content = point.get('content', '')
            table_content = " | ".join(field_values)
            if content:
                full_content = f"{table_content}\n{content}"
            else:
                full_content = table_content
            
            return SupplierInfo(
                name=supplier_name,
                source="knowledge_base",
                doc_id=doc_id,
                doc_name=doc_name,
                description=" | ".join(field_values[:3]),
                slice_id=slice_id,
                content=full_content
            )
        except Exception as e:
            print(f"[供应商提取] 旧方法提取失败: {e}")
            return None
    
    def _filter_suppliers_by_ai(self, suppliers: List[SupplierInfo], product_name: str, product_features: str = None) -> List[SupplierInfo]:
        """
        使用AI过滤不相关的供应商
        
        Args:
            suppliers: 供应商列表
            product_name: 产品名称
            product_features: 产品特征（可选）
            
        Returns:
            过滤后的供应商列表
        """
        start_time = time.time()
        if not suppliers:
            return suppliers
        
        try:
            api_key = Config.ARK_API_KEY
            if not api_key:
                # 如果没有配置API key，返回原始列表
                log_with_time(f"[供应商过滤] 未配置ARK_API_KEY，跳过AI过滤")
                return suppliers
            
            client = OpenAI(
                api_key=api_key,
                base_url=Config.ARK_BASE_URL,
                timeout=180.0,  # 设置180秒超时
            )
            
            # 构建供应商信息文本
            prompt_start = time.time()
            log_with_time(f"[供应商过滤] 开始构建prompt，供应商数量: {len(suppliers)}")
            supplier_texts = []
            for i, supplier in enumerate(suppliers):
                supplier_info = f"{i+1}. 供应商名称: {supplier.name}"
                # 使用 getattr 安全访问可选字段
                product_name_attr = getattr(supplier, 'product_name', None)
                product_code = getattr(supplier, 'product_code', None)
                sub_category_name = getattr(supplier, 'sub_category_name', None)
                description = getattr(supplier, 'description', None)
                
                if product_name_attr:
                    supplier_info += f", 产品名称: {product_name_attr}"
                if product_code:
                    supplier_info += f", 产品编码: {product_code}"
                if sub_category_name:
                    supplier_info += f", 子分类: {sub_category_name}"
                if description:
                    supplier_info += f", 描述: {description}"
                supplier_texts.append(supplier_info)
            
            suppliers_text = "\n".join(supplier_texts)
            
            # 构建查询问题
            query = f"{product_name}"
            if product_features:
                query += f" {product_features}"
            
            prompt = f"""请判断以下供应商列表中，哪些供应商与产品"{query}"相关。

供应商列表：
{suppliers_text}

请返回一个JSON数组，包含相关供应商的序号（从1开始）。如果所有供应商都不相关，返回空数组[]。

返回格式：
[1, 3, 5]

只返回JSON数组，不要其他文字说明。"""
            prompt_elapsed = time.time() - prompt_start
            log_with_time(f"[供应商过滤] Prompt构建完成 (耗时: {prompt_elapsed:.2f}秒)，prompt长度: {len(prompt)} 字符")

            # 调用AI过滤
            ai_start = time.time()
            log_with_time(f"[供应商过滤] 开始调用AI模型过滤 (超时设置: 180秒)...")
            response = client.chat.completions.create(
                model=Config.ARK_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个专业的采购助手，能够准确判断供应商与产品的相关性。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200,
                timeout=180.0  # 设置180秒超时
            )
            ai_elapsed = time.time() - ai_start
            log_with_time(f"[供应商过滤] AI调用完成 (耗时: {ai_elapsed:.2f}秒)")
            
            result_text = response.choices[0].message.content.strip()
            log_with_time(f"[供应商过滤] AI返回内容: {result_text[:200]}...")
            
            # 解析结果
            import json
            parse_start = time.time()
            try:
                # 尝试提取JSON部分
                if result_text.startswith("```json"):
                    result_text = result_text.replace("```json", "").replace("```", "").strip()
                elif result_text.startswith("```"):
                    result_text = result_text.replace("```", "").strip()
                
                relevant_indices = json.loads(result_text)
                
                if not isinstance(relevant_indices, list):
                    log_with_time(f"[供应商过滤] AI返回格式错误，返回全部供应商")
                    return suppliers
                
                # 转换为0-based索引并过滤
                filtered_suppliers = []
                for idx in relevant_indices:
                    if isinstance(idx, int) and 1 <= idx <= len(suppliers):
                        filtered_suppliers.append(suppliers[idx - 1])
                
                parse_elapsed = time.time() - parse_start
                total_elapsed = time.time() - start_time
                log_with_time(f"[供应商过滤] 解析完成 (耗时: {parse_elapsed:.2f}秒)")
                log_with_time(f"[供应商过滤] 从 {len(suppliers)} 个供应商中过滤出 {len(filtered_suppliers)} 个相关供应商 (总耗时: {total_elapsed:.2f}秒)")
                return filtered_suppliers
                
            except json.JSONDecodeError as e:
                parse_elapsed = time.time() - parse_start
                log_with_time(f"[供应商过滤] JSON解析失败 (耗时: {parse_elapsed:.2f}秒): {e}, 返回内容: {result_text}")
                return suppliers
            
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_with_time(f"[供应商过滤] AI过滤失败 (总耗时: {total_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            # 如果过滤失败，返回原始列表
            return suppliers
    
    def _extract_supplier_name(self, content: str) -> str:
        """
        从内容中提取供应商名称
        这是一个简化的实现，实际可能需要更复杂的NLP处理
        """
        # 简单的关键词匹配，实际应用中可以使用更智能的方法
        # 这里返回空字符串，让调用方处理
        # 实际实现中可以根据文档格式进行解析
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if '供应商' in line or '厂家' in line or '公司' in line:
                # 尝试提取公司名称
                parts = line.split('：')
                if len(parts) > 1:
                    return parts[1].strip()
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[1].strip()
        return ""
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        项目专家问答：通过问题搜索知识库，使用Ark模型总结答案
        
        Args:
            question: 用户问题
            
        Returns:
            包含答案和参考chunk的字典
        """
        try:
            # 1. 从知识库搜索相关内容（获取更多结果用于总结）
            # 构建post_processing参数（根据SDK官方示例）
            post_processing = {
                "rerank_switch": Config.KNOWLEDGE_RERANK_SWITCH,
                "rerank_model": Config.KNOWLEDGE_RERANK_MODEL,
                "rerank_only_chunk": False,
                "chunk_group": True,
                "get_attachment_link": True,  # 获取图片链接
            }
            
            if Config.KNOWLEDGE_RETRIEVE_COUNT:
                post_processing["retrieve_count"] = Config.KNOWLEDGE_RETRIEVE_COUNT
            
            search_params = {
                "query": question,
                "limit": 5,  # 知识库问答只返回top5
                "dense_weight": Config.KNOWLEDGE_DENSE_WEIGHT,
                "post_processing": post_processing,
            }
            
            if self.collection_name:
                search_params["collection_name"] = self.collection_name
                response = self.service.search_knowledge(**search_params)
            else:
                search_params["collection_name"] = "default"
                search_params["resource_id"] = self.collection_id
                response = self.service.search_knowledge(**search_params)
            
            # 2. 解析搜索结果，获取所有chunk（使用与search_specs相同的解析逻辑）
            chunks = []
            print(f"[问答] 搜索结果类型: {type(response)}")
            
            if response:
                # 如果响应是列表
                if isinstance(response, list):
                    print(f"[问答] 响应是列表，长度: {len(response)}")
                    for point in response:
                        # 处理Point对象
                        if hasattr(point, 'content'):
                            doc_name = None
                            if hasattr(point, 'doc_info') and point.doc_info:
                                if hasattr(point.doc_info, 'doc_name'):
                                    doc_name = point.doc_info.doc_name
                                elif hasattr(point.doc_info, 'name'):
                                    doc_name = point.doc_info.name
                                elif isinstance(point.doc_info, dict):
                                    doc_name = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
                            
                            # 提取图片链接 - 尝试多种可能的字段名
                            image_url = None
                            chunk_type = None
                            
                            # 打印所有可用属性以便调试
                            point_attrs = [attr for attr in dir(point) if not attr.startswith('_')]
                            print(f"[问答调试] Point对象属性: {point_attrs}")
                            
                            # 尝试多种可能的字段名
                            if hasattr(point, 'chunk_attachment') and point.chunk_attachment:
                                print(f"[问答调试] 找到 chunk_attachment: {point.chunk_attachment}")
                                if isinstance(point.chunk_attachment, list) and len(point.chunk_attachment) > 0:
                                    attachment = point.chunk_attachment[0]
                                    print(f"[问答调试] attachment: {attachment}, 类型: {type(attachment)}")
                                    if isinstance(attachment, dict):
                                        image_url = attachment.get('link', '')
                                        print(f"[问答调试] 从字典提取 image_url: {image_url}")
                                    elif hasattr(attachment, 'link'):
                                        image_url = attachment.link
                                        print(f"[问答调试] 从对象提取 image_url: {image_url}")
                            
                            # 尝试其他可能的字段名
                            if not image_url:
                                for attr_name in ['attachment_link', 'image_link', 'attachment', 'attachments']:
                                    if hasattr(point, attr_name):
                                        attr_value = getattr(point, attr_name)
                                        print(f"[问答调试] 找到 {attr_name}: {attr_value}")
                                        if isinstance(attr_value, str) and attr_value:
                                            image_url = attr_value
                                            break
                                        elif isinstance(attr_value, list) and len(attr_value) > 0:
                                            if isinstance(attr_value[0], dict):
                                                image_url = attr_value[0].get('link', '')
                                            elif hasattr(attr_value[0], 'link'):
                                                image_url = attr_value[0].link
                                            if image_url:
                                                break
                            
                            if hasattr(point, 'chunk_type'):
                                chunk_type = point.chunk_type
                            
                            # 处理内容编码问题
                            content = point.content or ''
                            if isinstance(content, bytes):
                                try:
                                    content = content.decode('utf-8')
                                except:
                                    try:
                                        content = content.decode('gbk')
                                    except:
                                        content = content.decode('utf-8', errors='ignore')
                            
                            chunk = {
                                "content": content,
                                "slice_id": point.point_id or point.chunk_id or '',
                                "doc_id": point.doc_id or '',
                                "doc_name": doc_name,
                                "image_url": image_url,
                                "chunk_type": chunk_type
                            }
                            print(f"[问答调试] 创建的 chunk: image_url={image_url}, chunk_type={chunk_type}, content长度={len(content)}")
                            if chunk["content"] or chunk["image_url"]:
                                chunks.append(chunk)
                        elif isinstance(point, dict):
                            chunk = self._parse_search_result_item(point)
                            if chunk:
                                chunks.append(chunk)
                # 如果响应是字典
                elif isinstance(response, dict):
                    print(f"[问答] 响应是字典，键: {list(response.keys())}")
                    # 尝试多种可能的键名，包括result_list
                    points = response.get('result_list', response.get('points', response.get('data', response.get('chunks', response.get('results', [])))))
                    if isinstance(points, list):
                        print(f"[问答] points是列表，包含 {len(points)} 个项目")
                        for point in points:
                            # 处理Point对象
                            if hasattr(point, 'content'):
                                doc_name = None
                                if hasattr(point, 'doc_info') and point.doc_info:
                                    if isinstance(point.doc_info, dict):
                                        doc_name = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
                                    elif hasattr(point.doc_info, 'doc_name'):
                                        doc_name = point.doc_info.doc_name
                                
                                # 提取图片链接
                                image_url = None
                                chunk_type = None
                                if hasattr(point, 'chunk_attachment') and point.chunk_attachment:
                                    if isinstance(point.chunk_attachment, list) and len(point.chunk_attachment) > 0:
                                        attachment = point.chunk_attachment[0]
                                        if isinstance(attachment, dict):
                                            image_url = attachment.get('link', '')
                                        elif hasattr(attachment, 'link'):
                                            image_url = attachment.link
                                
                                if hasattr(point, 'chunk_type'):
                                    chunk_type = point.chunk_type
                                
                                # 使用辅助函数提取完整chunk信息
                                chunk_info = extract_chunk_info(point)
                                if not chunk_info["doc_name"]:
                                    chunk_info["doc_name"] = doc_name
                                
                                chunk = {
                                    "content": chunk_info["content"],
                                    "slice_id": chunk_info["slice_id"],
                                    "doc_id": chunk_info["doc_id"],
                                    "doc_name": chunk_info["doc_name"],
                                    "image_url": chunk_info["image_url"],
                                    "chunk_type": chunk_info["chunk_type"],
                                    "md_content": chunk_info["md_content"],
                                    "html_content": chunk_info["html_content"],
                                    "point_id": chunk_info["point_id"]
                                }
                                if chunk["content"] or chunk["image_url"]:
                                    chunks.append(chunk)
                            elif isinstance(point, dict):
                                # 提取文档信息
                                doc_info = point.get('doc_info', {})
                                if isinstance(doc_info, dict):
                                    doc_name = doc_info.get('doc_name', doc_info.get('name', ''))
                                    doc_id = doc_info.get('doc_id', point.get('doc_id', ''))
                                else:
                                    doc_name = point.get('doc_name', point.get('document_name', ''))
                                    doc_id = point.get('doc_id', point.get('document_id', ''))
                                
                                # 提取图片链接
                                image_url = None
                                chunk_type = point.get('chunk_type')
                                chunk_attachment = point.get('chunk_attachment', [])
                                if isinstance(chunk_attachment, list) and len(chunk_attachment) > 0:
                                    attachment = chunk_attachment[0]
                                    if isinstance(attachment, dict):
                                        image_url = attachment.get('link', '')
                                
                                # 处理内容编码问题
                                content = point.get('content', point.get('text', point.get('chunk', '')))
                                if isinstance(content, bytes):
                                    try:
                                        content = content.decode('utf-8')
                                    except:
                                        try:
                                            content = content.decode('gbk')
                                        except:
                                            content = content.decode('utf-8', errors='ignore')
                                
                                # 使用辅助函数提取完整chunk信息
                                chunk_info = extract_chunk_info(point)
                                if not chunk_info["doc_name"]:
                                    chunk_info["doc_name"] = doc_name
                                
                                chunk = {
                                    "content": chunk_info["content"],
                                    "slice_id": chunk_info["slice_id"],
                                    "doc_id": chunk_info["doc_id"],
                                    "doc_name": chunk_info["doc_name"],
                                    "image_url": chunk_info["image_url"],
                                    "chunk_type": chunk_info["chunk_type"],
                                    "md_content": chunk_info["md_content"],
                                    "html_content": chunk_info["html_content"],
                                    "point_id": chunk_info["point_id"]
                                }
                                print(f"[问答调试] 创建的 chunk (字典): doc_name={chunk_info['doc_name']}, image_url={chunk_info['image_url']}, chunk_type={chunk_info['chunk_type']}, content长度={len(chunk_info['content'])}")
                                if chunk["content"] or chunk["image_url"]:
                                    chunks.append(chunk)
            
            print(f"[问答] 解析后得到 {len(chunks)} 个chunk")
            
            if not chunks:
                return {
                    "answer": "抱歉，在知识库中未找到相关信息。",
                    "references": []
                }
            
            # 3. 使用Ark模型总结答案
            api_key = Config.ARK_API_KEY
            if not api_key:
                # 如果没有配置API key，直接返回chunk内容
                # 注意：知识库API已经限制返回5个chunk，无需再次截取
                answer = f"找到 {len(chunks)} 条相关信息，请查看下方参考内容。"
                return {
                    "answer": answer,
                    "references": chunks
                }
            
            client = OpenAI(
                api_key=api_key,
                base_url=Config.ARK_BASE_URL,
                timeout=180.0,  # 设置180秒超时
            )
            
            # 构建prompt，包含所有相关chunk（包含point_id）
            # 注意：知识库API已经限制返回5个chunk，使用全部chunk
            context_parts = []
            for i, chunk in enumerate(chunks):  # 使用全部chunk（最多5个）
                point_id = chunk.get('slice_id', chunk.get('point_id', ''))
                doc_name = chunk.get('doc_name', '未知文档')
                content = chunk.get('content', '')[:800]  # 限制每个chunk长度
                image_url = chunk.get('image_url', '')
                
                # 构建参考内容，包含point_id
                chunk_text = f"point_id: {point_id}\n内容：{content}"
                if image_url:
                    chunk_text += f"\n图片链接：{image_url}"
                context_parts.append(chunk_text)
            
            context_text = "\n".join(context_parts)
            
            # 构建用户问题，明确是关于采购设备规格要求
            user_question = question
            if "规格" not in question and "要求" not in question:
                # 如果问题中没有明确提到规格或要求，补充说明
                user_question = f"{question}相关的规格要求有哪些"
            
            prompt = f"""# 任务
你是一位在线客服，你的首要任务是通过巧妙的话术回复用户的问题，你需要根据「参考资料」来回答接下来的「用户问题」，这些信息在 <context></context> XML tags 之内，你需要根据参考资料给出准确，简洁的回答。

你的回答要满足以下要求：
    1. 回答内容必须在参考资料范围内，尽可能简洁地回答问题，不能做任何参考资料以外的扩展解释。
    2. 回答中需要根据客户问题和参考资料保持与客户的友好沟通。
    3. 如果参考资料不能帮助你回答用户问题，告知客户无法回答该问题，并引导客户提供更加详细的信息。
    4. 为了保密需要，委婉地拒绝回答有关参考资料的文档名称或文档作者等问题。

# 任务执行
现在请你根据提供的参考资料，遵循限制来回答用户的问题，你的回答需要准确和完整。

# 参考资料
<context>
{context_text}
</context>
参考资料中提到的图片按上传顺序排列，请结合图片与文本信息综合回答问题。如参考资料中没有图片，请仅根据参考资料中的文本信息回答问题。

# 引用要求
1. 当可以回答时，在句子末尾适当引用相关参考资料，每个参考资料引用格式必须使用<reference>标签对，例如: <reference data-ref="{{point_id}}"></reference>
2. 当告知客户无法回答时，不允许引用任何参考资料
3. 'data-ref' 字段表示对应参考资料的 point_id
4. 'point_id' 取值必须来源于参考资料对应的'point_id'后的id号
5. 适当合并引用，当引用项相同可以合并引用，只在引用内容结束添加一个引用标签。

# 配图要求
1. 首先对参考资料的每个图片内容含义深入理解，然后从所有图片中筛选出与回答上下文直接关联的图片，在回答中的合适位置插入作为配图，图像内容必须支持直接的可视化说明问题的答案。若参考资料中无适配图片，或图片仅是间接性关联，则省略配图。
2. 使用 <illustration> 标签对表示插图，例如: <illustration data-ref="{{point_id}}"></illustration>，其中 'point_id' 字段表示对应图片的 point_id，每个配图标签对必须另起一行，相同的图片（以'point_id'区分）只允许使用一次。
3. 'point_id' 取值必须来源于参考资料，形如"_sys_auto_gen_doc_id-1005563729285435073--1"，请注意务必不要虚构，'point_id'值必须与参考资料完全一致

# 用户问题
{user_question}"""

            # 调用Ark模型生成答案
            response = client.chat.completions.create(
                model=Config.ARK_MODEL,
                messages=[
                    {"role": "system", "content": "你是一位专业的在线客服，能够基于知识库内容准确回答用户问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                timeout=180.0  # 设置180秒超时
            )
            
            answer = response.choices[0].message.content.strip()
            
            # 返回答案和参考chunk
            # 注意：知识库API已经限制返回5个chunk，无需再次截取
            return {
                "answer": answer,
                "references": chunks
            }
            
        except Exception as e:
            print(f"[问答] 问答功能失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"抱歉，处理您的问题时出现错误：{str(e)}",
                "references": []
            }
    
    def _parse_search_result_item(self, item: Any) -> Optional[Dict[str, Any]]:
        """解析搜索结果项，提取chunk信息"""
        try:
            if isinstance(item, dict):
                # 尝试多种可能的字段名
                content = (item.get('content', '') or 
                          item.get('text', '') or 
                          item.get('slice_content', '') or
                          item.get('point_content', '') or
                          item.get('chunk_content', ''))
                
                slice_id = (item.get('slice_id', '') or 
                           item.get('id', '') or
                           item.get('point_id', ''))
                
                doc_id = (item.get('doc_id', '') or 
                         item.get('document_id', '') or
                         item.get('docId', ''))
                
                doc_name = (item.get('doc_name', '') or 
                           item.get('document_name', '') or
                           item.get('docName', ''))
                
                # 提取图片链接 - 尝试多种可能的字段名
                image_url = None
                chunk_type = item.get('chunk_type')
                
                print(f"[解析] 完整item内容: {item}")
                print(f"[解析] item的所有键: {list(item.keys())}")
                
                # 尝试 chunk_attachment
                chunk_attachment = item.get('chunk_attachment', [])
                print(f"[解析] chunk_attachment: {chunk_attachment}, 类型: {type(chunk_attachment)}")
                if isinstance(chunk_attachment, list) and len(chunk_attachment) > 0:
                    attachment = chunk_attachment[0]
                    print(f"[解析] attachment: {attachment}, 类型: {type(attachment)}")
                    if isinstance(attachment, dict):
                        image_url = attachment.get('link', '')
                        print(f"[解析] 从chunk_attachment提取的 image_url: {image_url}")
                
                # 尝试其他可能的字段名
                if not image_url:
                    for key in ['attachment_link', 'image_link', 'attachment', 'attachments', 'chunk_attachment_link']:
                        if key in item:
                            value = item[key]
                            print(f"[解析] 找到字段 {key}: {value}, 类型: {type(value)}")
                            if isinstance(value, str) and value:
                                image_url = value
                                break
                            elif isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], dict):
                                    image_url = value[0].get('link', '')
                                elif hasattr(value[0], 'link'):
                                    image_url = value[0].link
                                if image_url:
                                    break
                
                # 处理内容编码问题
                if isinstance(content, bytes):
                    try:
                        content = content.decode('utf-8')
                    except:
                        try:
                            content = content.decode('gbk')
                        except:
                            content = content.decode('utf-8', errors='ignore')
                
                # 如果content是空字符串，尝试从其他字段获取
                if not content:
                    # 尝试获取整个item的字符串表示
                    content = str(item)
                
                if content and content.strip() or image_url:
                    print(f"[解析] 成功解析chunk: doc_name={doc_name}, content长度={len(content)}, image_url={image_url}, chunk_type={chunk_type}")
                    return {
                        "content": content.strip() if content else "",
                        "slice_id": str(slice_id) if slice_id else "",
                        "doc_id": str(doc_id) if doc_id else "",
                        "doc_name": str(doc_name) if doc_name else "",
                        "image_url": image_url,
                        "chunk_type": chunk_type
                    }
                else:
                    print(f"[解析] chunk内容为空，item keys: {list(item.keys()) if isinstance(item, dict) else 'not dict'}")
            elif isinstance(item, str):
                if item.strip():
                    return {
                        "content": item.strip(),
                        "slice_id": "",
                        "doc_id": "",
                        "doc_name": ""
                    }
        except Exception as e:
            print(f"[解析] 解析搜索结果项失败: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def search_certificate_personnel(
        self, 
        project_time: str,
        certificate_requirements: Dict[str, int],
        free_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询证书人员信息
        
        Args:
            project_time: 标段时间
            certificate_requirements: 证书范围，每种证书要求的人员数，例如：{'证书A': 2, '证书B': 3}
            free_status: 空闲状态（可选）
            
        Returns:
            包含问题、人员列表和参考chunk的字典
        """
        start_time = time.time()
        log_with_time(f"[证书人员查询] 开始查询证书人员")
        log_with_time(f"[证书人员查询] 标段时间: {project_time}")
        log_with_time(f"[证书人员查询] 证书要求: {certificate_requirements}")
        log_with_time(f"[证书人员查询] 空闲状态: {free_status}")
        
        # 指定的证书知识库文档ID
        certificate_doc_id = "_sys_auto_gen_doc_id-17526703582802695253"
        
        try:
            # 1. 将输入转换成查询问题
            # 构建更宽泛的搜索查询，确保能找到相关证书
            cert_names = list(certificate_requirements.keys())
            # 提取证书关键词（去掉"证书"、"培训"等通用词，保留核心关键词）
            cert_keywords = []
            for cert_name in cert_names:
                # 提取关键词，例如"一级建造师注册证书" -> "一级建造师"
                keywords = cert_name.replace("证书", "").replace("注册", "").replace("培训", "").strip()
                cert_keywords.append(keywords)
            
            # 构建搜索查询：使用证书关键词和标段时间
            search_query_parts = cert_keywords + [project_time]
            if free_status:
                search_query_parts.append(free_status)
            search_query = " ".join(search_query_parts)
            
            # 构建用于AI分析的完整查询描述
            question_parts = []
            question_parts.append(f"标段时间：{project_time}")
            
            cert_list = []
            for cert_name, count in certificate_requirements.items():
                cert_list.append(f"{cert_name}需要{count}人")
            question_parts.append(f"证书要求：{', '.join(cert_list)}")
            
            if free_status:
                question_parts.append(f"空闲状态：{free_status}")
            
            query = " ".join(question_parts)
            log_with_time(f"[证书人员查询] 搜索查询: {search_query}")
            log_with_time(f"[证书人员查询] 完整查询描述: {query}")
            
            # 2. 在指定的文档中搜索所有相关信息
            post_processing = {
                "rerank_switch": Config.KNOWLEDGE_RERANK_SWITCH,
                "rerank_model": Config.KNOWLEDGE_RERANK_MODEL,
                "rerank_only_chunk": False,
                "chunk_group": True,
                "get_attachment_link": True,
            }
            
            if Config.KNOWLEDGE_RETRIEVE_COUNT:
                post_processing["retrieve_count"] = Config.KNOWLEDGE_RETRIEVE_COUNT
            
            search_params = {
                "query": search_query,  # 使用更宽泛的搜索查询
                "limit": 50,  # 获取更多结果以找到所有匹配的人员
                "dense_weight": Config.KNOWLEDGE_DENSE_WEIGHT,
                "post_processing": post_processing,
            }
            
            search_start = time.time()
            log_with_time(f"[证书人员查询] [步骤1] 开始搜索知识库...")
            if self.collection_name:
                search_params["collection_name"] = self.collection_name
                response = self.service.search_knowledge(**search_params)
            else:
                search_params["collection_name"] = "default"
                search_params["resource_id"] = self.collection_id
                response = self.service.search_knowledge(**search_params)
            search_elapsed = time.time() - search_start
            log_with_time(f"[证书人员查询] [步骤1] 搜索完成 (耗时: {search_elapsed:.2f}秒)")
            
            # 3. 解析搜索结果，收集所有来自指定文档的chunk
            chunks = []
            references = []
            
            if response:
                if isinstance(response, list):
                    for point in response:
                        chunk = None
                        if hasattr(point, 'content'):
                            doc_name = None
                            if hasattr(point, 'doc_info') and point.doc_info:
                                if hasattr(point.doc_info, 'doc_name'):
                                    doc_name = point.doc_info.doc_name
                                elif hasattr(point.doc_info, 'name'):
                                    doc_name = point.doc_info.name
                                elif isinstance(point.doc_info, dict):
                                    doc_name = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
                            
                            # 尝试多种方式获取文档ID
                            point_doc_id = ''
                            if hasattr(point, 'doc_id'):
                                point_doc_id = point.doc_id or ''
                            elif hasattr(point, 'document_id'):
                                point_doc_id = point.document_id or ''
                            
                            # 如果还没有，尝试从doc_info中获取
                            if not point_doc_id and hasattr(point, 'doc_info') and point.doc_info:
                                if hasattr(point.doc_info, 'doc_id'):
                                    point_doc_id = point.doc_info.doc_id or ''
                                elif isinstance(point.doc_info, dict):
                                    point_doc_id = point.doc_info.get('doc_id', '') or point.doc_info.get('document_id', '')
                            
                            # 只处理来自指定文档的chunk
                            if point_doc_id != certificate_doc_id:
                                continue
                            
                            content = point.content or ''
                            if isinstance(content, bytes):
                                try:
                                    content = content.decode('utf-8')
                                except:
                                    try:
                                        content = content.decode('gbk')
                                    except:
                                        content = content.decode('utf-8', errors='ignore')
                            
                            chunk = {
                                "content": content,
                                "slice_id": point.point_id or point.chunk_id or '',
                                "doc_id": point_doc_id,
                                "doc_name": doc_name,
                                "image_url": None,
                                "chunk_type": getattr(point, 'chunk_type', None)
                            }
                        elif isinstance(point, dict):
                            # 尝试多种方式获取文档ID
                            point_doc_id = point.get('doc_id', '') or point.get('document_id', '')
                            
                            # 如果还没有，尝试从doc_info中获取
                            if not point_doc_id and 'doc_info' in point:
                                doc_info = point['doc_info']
                                if isinstance(doc_info, dict):
                                    point_doc_id = doc_info.get('doc_id', '') or doc_info.get('document_id', '')
                            
                            # 只处理来自指定文档的chunk
                            if point_doc_id != certificate_doc_id:
                                continue
                            
                            chunk = self._parse_search_result_item(point)
                        
                        if chunk and chunk.get("content"):
                            chunks.append(chunk)
                            # 添加到references
                            from models.schemas import SpecSource
                            references.append(SpecSource(
                                content=chunk["content"],
                                slice_id=chunk.get("slice_id", ""),
                                doc_id=chunk.get("doc_id", ""),
                                doc_name=chunk.get("doc_name"),
                                image_url=chunk.get("image_url"),
                                chunk_type=chunk.get("chunk_type")
                            ))
                
                elif isinstance(response, dict):
                    points = response.get('result_list', response.get('points', response.get('data', response.get('chunks', response.get('results', [])))))
                    if isinstance(points, list):
                        for point in points:
                            chunk = None
                            if hasattr(point, 'content'):
                                # 尝试多种方式获取文档ID
                                point_doc_id = ''
                                if hasattr(point, 'doc_id'):
                                    point_doc_id = point.doc_id or ''
                                elif hasattr(point, 'document_id'):
                                    point_doc_id = point.document_id or ''
                                
                                # 如果还没有，尝试从doc_info中获取
                                if not point_doc_id and hasattr(point, 'doc_info') and point.doc_info:
                                    if hasattr(point.doc_info, 'doc_id'):
                                        point_doc_id = point.doc_info.doc_id or ''
                                    elif isinstance(point.doc_info, dict):
                                        point_doc_id = point.doc_info.get('doc_id', '') or point.doc_info.get('document_id', '')
                                
                                if point_doc_id != certificate_doc_id:
                                    continue
                                
                                content = point.content or ''
                                if isinstance(content, bytes):
                                    try:
                                        content = content.decode('utf-8')
                                    except:
                                        try:
                                            content = content.decode('gbk')
                                        except:
                                            content = content.decode('utf-8', errors='ignore')
                                
                                doc_name = None
                                if hasattr(point, 'doc_info') and point.doc_info:
                                    if isinstance(point.doc_info, dict):
                                        doc_name = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
                                    elif hasattr(point.doc_info, 'doc_name'):
                                        doc_name = point.doc_info.doc_name
                                
                                chunk = {
                                    "content": content,
                                    "slice_id": point.point_id or point.chunk_id or '',
                                    "doc_id": point_doc_id,
                                    "doc_name": doc_name,
                                    "image_url": None,
                                    "chunk_type": getattr(point, 'chunk_type', None)
                                }
                            elif isinstance(point, dict):
                                # 尝试多种方式获取文档ID
                                point_doc_id = point.get('doc_id', '') or point.get('document_id', '')
                                
                                # 如果还没有，尝试从doc_info中获取
                                if not point_doc_id and 'doc_info' in point:
                                    doc_info = point['doc_info']
                                    if isinstance(doc_info, dict):
                                        point_doc_id = doc_info.get('doc_id', '') or doc_info.get('document_id', '')
                                
                                if point_doc_id != certificate_doc_id:
                                    continue
                                
                                chunk = self._parse_search_result_item(point)
                            
                            if chunk and chunk.get("content"):
                                chunks.append(chunk)
                                from models.schemas import SpecSource
                                references.append(SpecSource(
                                    content=chunk["content"],
                                    slice_id=chunk.get("slice_id", ""),
                                    doc_id=chunk.get("doc_id", ""),
                                    doc_name=chunk.get("doc_name"),
                                    image_url=chunk.get("image_url"),
                                    chunk_type=chunk.get("chunk_type")
                                ))
            
            log_with_time(f"[证书人员查询] [步骤1] 找到 {len(chunks)} 个相关chunk（来自指定文档）")
            
            # 如果没有找到chunk，尝试不限制文档ID的搜索
            if not chunks:
                log_with_time(f"[证书人员查询] [步骤1] 未找到指定文档的chunk，尝试搜索所有文档...")
                # 重新搜索，不限制文档ID
                if self.collection_name:
                    search_params["collection_name"] = self.collection_name
                    response_all = self.service.search_knowledge(**search_params)
                else:
                    search_params["collection_name"] = "default"
                    search_params["resource_id"] = self.collection_id
                    response_all = self.service.search_knowledge(**search_params)
                
                # 解析所有结果，但只保留来自指定文档的
                found_doc_ids = set()
                if response_all:
                    if isinstance(response_all, list):
                        log_with_time(f"[证书人员查询] [调试] 搜索返回了 {len(response_all)} 个结果")
                        for idx, point in enumerate(response_all[:10]):  # 只检查前10个
                            point_doc_id = getattr(point, 'doc_id', '') if hasattr(point, 'doc_id') else (point.get('doc_id', '') if isinstance(point, dict) else '')
                            found_doc_ids.add(point_doc_id)
                            if idx < 5:  # 只打印前5个
                                log_with_time(f"[证书人员查询] [调试] 结果 {idx+1} 文档ID: {point_doc_id}")
                            if point_doc_id == certificate_doc_id:
                                # 解析这个chunk
                                chunk = None
                                if hasattr(point, 'content'):
                                    content = point.content or ''
                                    if isinstance(content, bytes):
                                        try:
                                            content = content.decode('utf-8')
                                        except:
                                            try:
                                                content = content.decode('gbk')
                                            except:
                                                content = content.decode('utf-8', errors='ignore')
                                    chunk = {
                                        "content": content,
                                        "slice_id": point.point_id or point.chunk_id or '',
                                        "doc_id": point_doc_id,
                                        "doc_name": None,
                                        "image_url": None,
                                        "chunk_type": getattr(point, 'chunk_type', None)
                                    }
                                elif isinstance(point, dict):
                                    chunk = self._parse_search_result_item(point)
                                
                                if chunk and chunk.get("content"):
                                    chunks.append(chunk)
                                    from models.schemas import SpecSource
                                    references.append(SpecSource(
                                        content=chunk["content"],
                                        slice_id=chunk.get("slice_id", ""),
                                        doc_id=chunk.get("doc_id", ""),
                                        doc_name=chunk.get("doc_name"),
                                        image_url=chunk.get("image_url"),
                                        chunk_type=chunk.get("chunk_type")
                                    ))
                    
                    elif isinstance(response_all, dict):
                            points_all = response_all.get('result_list', response_all.get('points', response_all.get('data', response_all.get('chunks', response_all.get('results', [])))))
                            if isinstance(points_all, list):
                                log_with_time(f"[证书人员查询] [调试] 搜索返回了 {len(points_all)} 个结果（字典格式）")
                                for idx, point in enumerate(points_all[:10]):
                                    # 尝试多种方式获取文档ID
                                    point_doc_id = ''
                                    if hasattr(point, 'doc_id'):
                                        point_doc_id = point.doc_id or ''
                                    elif hasattr(point, 'document_id'):
                                        point_doc_id = point.document_id or ''
                                    elif isinstance(point, dict):
                                        point_doc_id = point.get('doc_id', '') or point.get('document_id', '') or point.get('docId', '')
                                    
                                    # 如果还是没有，尝试从doc_info中获取
                                    if not point_doc_id:
                                        if hasattr(point, 'doc_info'):
                                            doc_info = point.doc_info
                                            if hasattr(doc_info, 'doc_id'):
                                                point_doc_id = doc_info.doc_id or ''
                                            elif isinstance(doc_info, dict):
                                                point_doc_id = doc_info.get('doc_id', '') or doc_info.get('document_id', '')
                                        elif isinstance(point, dict) and 'doc_info' in point:
                                            doc_info = point['doc_info']
                                            if isinstance(doc_info, dict):
                                                point_doc_id = doc_info.get('doc_id', '') or doc_info.get('document_id', '')
                                    
                                    found_doc_ids.add(point_doc_id)
                                    if idx < 5:
                                        log_with_time(f"[证书人员查询] [调试] 结果 {idx+1} 文档ID: {point_doc_id}")
                                        # 打印point的所有属性/键，帮助调试
                                        if hasattr(point, '__dict__'):
                                            log_with_time(f"[证书人员查询] [调试] 结果 {idx+1} 属性: {list(point.__dict__.keys())[:10]}")
                                        elif isinstance(point, dict):
                                            log_with_time(f"[证书人员查询] [调试] 结果 {idx+1} 键: {list(point.keys())[:10]}")
                                    
                                    if point_doc_id == certificate_doc_id:
                                        # 解析这个chunk
                                        chunk = None
                                        if hasattr(point, 'content'):
                                            content = point.content or ''
                                            if isinstance(content, bytes):
                                                try:
                                                    content = content.decode('utf-8')
                                                except:
                                                    try:
                                                        content = content.decode('gbk')
                                                    except:
                                                        content = content.decode('utf-8', errors='ignore')
                                            chunk = {
                                                "content": content,
                                                "slice_id": point.point_id or point.chunk_id or '',
                                                "doc_id": point_doc_id,
                                                "doc_name": None,
                                                "image_url": None,
                                                "chunk_type": getattr(point, 'chunk_type', None)
                                            }
                                        elif isinstance(point, dict):
                                            chunk = self._parse_search_result_item(point)
                                        
                                        if chunk and chunk.get("content"):
                                            chunks.append(chunk)
                                            from models.schemas import SpecSource
                                            references.append(SpecSource(
                                                content=chunk["content"],
                                                slice_id=chunk.get("slice_id", ""),
                                                doc_id=chunk.get("doc_id", ""),
                                                doc_name=chunk.get("doc_name"),
                                                image_url=chunk.get("image_url"),
                                                chunk_type=chunk.get("chunk_type")
                                            ))
                
                if found_doc_ids:
                    log_with_time(f"[证书人员查询] [调试] 搜索到的文档ID列表: {list(found_doc_ids)[:10]}")
                log_with_time(f"[证书人员查询] [步骤1] 重新搜索后找到 {len(chunks)} 个相关chunk")
            
            if not chunks:
                log_with_time(f"[证书人员查询] 警告：未找到任何相关chunk，返回空结果")
                log_with_time(f"[证书人员查询] 目标文档ID: {certificate_doc_id}")
                log_with_time(f"[证书人员查询] 搜索查询: {search_query}")
                return {
                    "question": query,
                    "personnel_list": [],
                    "references": references
                }
            
            # 4. 使用AI模型筛选和格式化人员信息
            api_key = Config.ARK_API_KEY
            if not api_key:
                log_with_time(f"[证书人员查询] 未配置ARK_API_KEY，返回原始chunk")
                # 如果没有配置API key，返回原始chunk内容
                from models.schemas import PersonnelInfo
                personnel_list = []
                for chunk in chunks[:20]:
                    personnel_list.append(PersonnelInfo(
                        content=chunk["content"],
                        slice_id=chunk.get("slice_id"),
                        doc_id=chunk.get("doc_id")
                    ))
                return {
                    "question": query,
                    "personnel_list": personnel_list,
                    "references": references[:20]
                }
            
            # 构建prompt
            prompt_start = time.time()
            log_with_time(f"[证书人员查询] [步骤2] 开始构建AI prompt...")
            
            client = OpenAI(
                api_key=api_key,
                base_url=Config.ARK_BASE_URL,
                timeout=180.0,  # 设置180秒超时
            )
            
            # 构建上下文内容
            context_parts = []
            for i, chunk in enumerate(chunks[:30]):  # 最多使用30个chunk
                slice_id = chunk.get("slice_id", "")
                content = chunk.get("content", "")[:1500]  # 增加chunk长度限制以包含更多信息
                chunk_text = f"point_id: {slice_id}\n内容：{content}"
                context_parts.append(chunk_text)
            
            context_text = "\n".join(context_parts)
            log_with_time(f"[证书人员查询] [步骤2] 构建了 {len(context_parts)} 个chunk的上下文，总长度: {len(context_text)} 字符")
            
            # 构建证书要求描述
            cert_requirements_text = []
            for cert_name, count in certificate_requirements.items():
                cert_requirements_text.append(f"- {cert_name}：需要 {count} 人")
            cert_requirements_str = "\n".join(cert_requirements_text)
            
            # 构建用户查询需求
            user_requirement = f"""标段时间：{project_time}
证书要求：
{cert_requirements_str}"""
            if free_status:
                user_requirement += f"\n空闲状态：{free_status}"
            user_requirement += "\n\n请找出有效期可以覆盖标段时间的人员信息。"
            
            prompt = f"""# 任务
你是一位专业的人力资源专家，你的任务是根据「参考资料」找出符合要求的人员信息，这些信息在 <context></context> XML tags 之内。

# 查询需求
{user_requirement}

# 数据格式说明
参考资料中可能包含三种不同的表格格式，你需要识别并正确解析：

**格式1：成都公司的sheet页**
字段：序号、姓名、部门、类别、证书名称、证书编号、发证日期、到期日期
- 姓名 → name
- 部门 → department
- 类别 → category
- 证书名称 → certificate_name
- 证书编号 → certificate_number
- 发证日期 → issue_date
- 到期日期 → expiry_date

**格式2：公司各类培训证书的sheet页**
字段：序号、姓名、部门、证书名称、培训机构、发证时间、证书有效期、备注
- 姓名 → name
- 部门 → department
- 证书名称 → certificate_name
- 发证时间 → issue_date
- 证书有效期 → expiry_date（注意：可能是"X年"格式，需要转换为具体日期）
- 备注 → free_status（如果备注中包含空闲状态信息）

**格式3：新疆片区员工证书sheet页**
字段：序号、姓名、部门、作业区、专业、证书名称、证书编号、发证日期、有效日期、备注
- 姓名 → name
- 部门 → department
- 作业区 → category（作业区作为类别）
- 专业 → category（专业也可以作为类别，优先使用作业区）
- 证书名称 → certificate_name
- 证书编号 → certificate_number
- 发证日期 → issue_date
- 有效日期 → expiry_date
- 备注 → free_status（如果备注中包含空闲状态信息）

# 任务要求
1. 仔细分析参考资料中的所有人员信息，识别表格格式
2. 筛选出符合以下条件的人员：
   - 证书有效期可以覆盖标段时间（{project_time}）
     * 如果到期日期/有效日期在标段时间之后，则符合条件
     * 如果证书有效期是"X年"格式，需要根据发证日期计算到期日期
   - 证书类型符合要求（{', '.join(certificate_requirements.keys())}）
     * 证书名称需要匹配或包含要求的证书类型
     * 匹配要灵活，例如："一级建造师注册证书"可以匹配"一级建造师"、"建造师"等
     * "关键岗位HSE培训 施工项目负责人"可以匹配包含"HSE"、"施工项目负责人"、"关键岗位"等的证书
   - 如果指定了空闲状态，人员空闲状态需匹配
     * 空闲状态可能在备注字段中，需要仔细查找
3. 从每个符合条件的人员信息中提取以下字段：
   - name（姓名）：必填
   - department（部门）：必填
   - category（类别）：可选，可能是"类别"、"作业区"或"专业"
   - certificate_name（证书名称）：必填
   - certificate_number（证书编号）：可选，格式2可能没有
   - issue_date（发证日期）：必填，格式统一为YYYY-MM-DD
   - expiry_date（到期日期）：必填，格式统一为YYYY-MM-DD
     * 如果是"X年"格式，需要根据发证日期计算
     * 例如：发证日期2020-01-01，有效期3年，则到期日期为2023-01-01
   - free_status（空闲状态）：可选，从备注或其他字段中提取
4. 返回JSON格式的人员列表，格式如下：
```json
{{
  "personnel_list": [
    {{
      "name": "姓名",
      "department": "部门",
      "category": "类别",
      "certificate_name": "证书名称",
      "certificate_number": "证书编号",
      "issue_date": "2024-01-01",
      "expiry_date": "2027-01-01",
      "free_status": "空闲状态",
      "slice_id": "对应的point_id"
    }}
  ]
}}
```

# 注意事项
1. 只返回JSON格式，不要添加任何其他文字说明
2. 如果某个字段在参考资料中找不到，使用空字符串 ""
3. slice_id字段必须使用参考资料中对应的point_id
4. 只返回符合条件的人员，不符合条件的不要包含
5. 确保日期格式统一为YYYY-MM-DD（如：2024-01-01）
6. 日期计算要准确，注意年份的加减
7. 证书名称匹配要灵活，支持部分匹配（如：要求"安全证书"，"安全员证书"也符合）
8. 如果同一人员有多条记录，每条记录都要单独返回

# 参考资料
<context>
{context_text}
</context>

请根据参考资料找出符合要求的人员，并以JSON格式返回。"""
            
            prompt_elapsed = time.time() - prompt_start
            log_with_time(f"[证书人员查询] [步骤2] Prompt构建完成 (耗时: {prompt_elapsed:.2f}秒)，prompt长度: {len(prompt)} 字符")
            
            # 调用AI模型
            ai_start = time.time()
            log_with_time(f"[证书人员查询] [步骤2] 开始调用AI模型分析人员信息 (超时设置: 120秒)...")
            try:
                response = client.chat.completions.create(
                    model=Config.ARK_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一位专业的人力资源专家，能够准确提取和格式化人员信息。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # 降低温度以提高准确性
                    max_tokens=4000,  # 增加token限制以支持更多人员
                    timeout=180.0  # 设置180秒超时
                )
                ai_elapsed = time.time() - ai_start
                log_with_time(f"[证书人员查询] [步骤2] AI调用完成 (耗时: {ai_elapsed:.2f}秒)")
                
                ai_response = response.choices[0].message.content.strip()
                log_with_time(f"[证书人员查询] [步骤2] AI响应长度: {len(ai_response)} 字符")
                
                # 5. 解析AI返回的JSON
                import json
                import re
                
                # 尝试提取JSON（可能包含markdown代码块）
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 尝试直接查找JSON对象
                    json_match = re.search(r'\{.*"personnel_list".*\}', ai_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        json_str = ai_response
                
                # 解析JSON
                parse_start = time.time()
                log_with_time(f"[证书人员查询] [步骤3] 开始解析AI返回的JSON...")
                try:
                    result_data = json.loads(json_str)
                    personnel_list_data = result_data.get("personnel_list", [])
                    
                    # 转换为PersonnelInfo对象
                    from models.schemas import PersonnelInfo
                    personnel_list = []
                    for person_data in personnel_list_data:
                        # 找到对应的chunk以获取完整内容
                        slice_id = person_data.get("slice_id", "")
                        chunk_content = ""
                        for chunk in chunks:
                            if chunk.get("slice_id") == slice_id:
                                chunk_content = chunk.get("content", "")
                                break
                        
                        personnel_info = PersonnelInfo(
                            name=person_data.get("name", ""),
                            department=person_data.get("department", ""),
                            category=person_data.get("category", ""),
                            certificate_name=person_data.get("certificate_name", ""),
                            certificate_number=person_data.get("certificate_number", ""),
                            issue_date=person_data.get("issue_date", ""),
                            expiry_date=person_data.get("expiry_date", ""),
                            free_status=person_data.get("free_status", ""),
                            content=chunk_content or person_data.get("name", ""),
                            slice_id=slice_id,
                            doc_id=certificate_doc_id
                        )
                        personnel_list.append(personnel_info)
                    
                    parse_elapsed = time.time() - parse_start
                    log_with_time(f"[证书人员查询] [步骤3] JSON解析完成 (耗时: {parse_elapsed:.2f}秒)，找到 {len(personnel_list)} 个人员")
                    
                except json.JSONDecodeError as json_error:
                    parse_elapsed = time.time() - parse_start
                    log_with_time(f"[证书人员查询] [步骤3] JSON解析失败 (耗时: {parse_elapsed:.2f}秒): {json_error}")
                    log_with_time(f"[证书人员查询] AI返回内容: {ai_response[:500]}")
                    # 如果解析失败，返回空列表
                    personnel_list = []
                
            except Exception as ai_error:
                ai_elapsed = time.time() - ai_start
                log_with_time(f"[证书人员查询] [步骤2] AI调用失败 (耗时: {ai_elapsed:.2f}秒): {ai_error}")
                import traceback
                traceback.print_exc()
                # 如果AI调用失败，返回空列表
                personnel_list = []
            
            total_elapsed = time.time() - start_time
            log_with_time(f"[证书人员查询] 查询完成 (总耗时: {total_elapsed:.2f}秒)，找到 {len(personnel_list)} 个匹配人员")
            
            return {
                "question": query,
                "personnel_list": personnel_list,
                "references": references[:20]  # 最多返回20个参考
            }
        
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_with_time(f"[证书人员查询] 查询失败 (耗时: {total_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            return {
                "question": query if 'query' in locals() else "",
                "personnel_list": [],
                "references": []
            }
    
    def search_certificate_personnel_by_query(self, query: str) -> Dict[str, Any]:
        """
        根据自然语言查询需求查询证书人员信息
        直接使用用户查询搜索知识库，然后AI筛选和格式化结果
        
        Args:
            query: 自然语言查询需求，例如："标段时间：2026年1月到2026年3月，需要2个一级建造师注册证书的人员"
            
        Returns:
            包含问题、人员列表和参考chunk的字典
        """
        start_time = time.time()
        log_with_time(f"[证书人员查询] 开始查询证书人员")
        log_with_time(f"[证书人员查询] 用户查询: {query}")
        
        # 指定的证书知识库文档ID
        certificate_doc_id = "_sys_auto_gen_doc_id-17526703582802695253"
        
        try:
            # 1. 直接使用用户查询搜索知识库
            post_processing = {
                "rerank_switch": Config.KNOWLEDGE_RERANK_SWITCH,
                "rerank_model": Config.KNOWLEDGE_RERANK_MODEL,
                "rerank_only_chunk": False,
                "chunk_group": True,
                "get_attachment_link": True,
            }
            
            if Config.KNOWLEDGE_RETRIEVE_COUNT:
                post_processing["retrieve_count"] = Config.KNOWLEDGE_RETRIEVE_COUNT
            
            search_params = {
                "query": query,  # 直接使用用户查询
                "limit": 50,
                "dense_weight": Config.KNOWLEDGE_DENSE_WEIGHT,
                "post_processing": post_processing,
            }
            
            search_start = time.time()
            log_with_time(f"[证书人员查询] [步骤1] 开始搜索知识库...")
            if self.collection_name:
                search_params["collection_name"] = self.collection_name
                response = self.service.search_knowledge(**search_params)
            else:
                search_params["collection_name"] = "default"
                search_params["resource_id"] = self.collection_id
                response = self.service.search_knowledge(**search_params)
            search_elapsed = time.time() - search_start
            log_with_time(f"[证书人员查询] [步骤1] 搜索完成 (耗时: {search_elapsed:.2f}秒)")
            
            # 2. 解析搜索结果，收集所有来自指定文档的chunk
            chunks = []
            references = []
            
            if response:
                if isinstance(response, list):
                    for point in response:
                        chunk = None
                        if hasattr(point, 'content'):
                            doc_name = None
                            if hasattr(point, 'doc_info') and point.doc_info:
                                if hasattr(point.doc_info, 'doc_name'):
                                    doc_name = point.doc_info.doc_name
                                elif hasattr(point.doc_info, 'name'):
                                    doc_name = point.doc_info.name
                                elif isinstance(point.doc_info, dict):
                                    doc_name = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
                            
                            point_doc_id = ''
                            if hasattr(point, 'doc_id'):
                                point_doc_id = point.doc_id or ''
                            elif hasattr(point, 'document_id'):
                                point_doc_id = point.document_id or ''
                            
                            if not point_doc_id and hasattr(point, 'doc_info') and point.doc_info:
                                if hasattr(point.doc_info, 'doc_id'):
                                    point_doc_id = point.doc_info.doc_id or ''
                                elif isinstance(point.doc_info, dict):
                                    point_doc_id = point.doc_info.get('doc_id', '') or point.doc_info.get('document_id', '')
                            
                            if point_doc_id != certificate_doc_id:
                                continue
                            
                            content = point.content or ''
                            if isinstance(content, bytes):
                                try:
                                    content = content.decode('utf-8')
                                except:
                                    try:
                                        content = content.decode('gbk')
                                    except:
                                        content = content.decode('utf-8', errors='ignore')
                            
                            chunk = {
                                "content": content,
                                "slice_id": point.point_id or point.chunk_id or '',
                                "doc_id": point_doc_id,
                                "doc_name": doc_name,
                                "image_url": None,
                                "chunk_type": getattr(point, 'chunk_type', None)
                            }
                        elif isinstance(point, dict):
                            point_doc_id = point.get('doc_id', '') or point.get('document_id', '')
                            
                            if not point_doc_id and 'doc_info' in point:
                                doc_info = point['doc_info']
                                if isinstance(doc_info, dict):
                                    point_doc_id = doc_info.get('doc_id', '') or doc_info.get('document_id', '')
                            
                            if point_doc_id != certificate_doc_id:
                                continue
                            
                            chunk = self._parse_search_result_item(point)
                        
                        if chunk and chunk.get("content"):
                            chunks.append(chunk)
                            from models.schemas import SpecSource
                            references.append(SpecSource(
                                content=chunk["content"],
                                slice_id=chunk.get("slice_id", ""),
                                doc_id=chunk.get("doc_id", ""),
                                doc_name=chunk.get("doc_name"),
                                image_url=chunk.get("image_url"),
                                chunk_type=chunk.get("chunk_type")
                            ))
                
                elif isinstance(response, dict):
                    points = response.get('result_list', response.get('points', response.get('data', response.get('chunks', response.get('results', [])))))
                    if isinstance(points, list):
                        for point in points:
                            chunk = None
                            if hasattr(point, 'content'):
                                point_doc_id = ''
                                if hasattr(point, 'doc_id'):
                                    point_doc_id = point.doc_id or ''
                                elif hasattr(point, 'document_id'):
                                    point_doc_id = point.document_id or ''
                                
                                if not point_doc_id and hasattr(point, 'doc_info') and point.doc_info:
                                    if hasattr(point.doc_info, 'doc_id'):
                                        point_doc_id = point.doc_info.doc_id or ''
                                    elif isinstance(point.doc_info, dict):
                                        point_doc_id = point.doc_info.get('doc_id', '') or point.doc_info.get('document_id', '')
                                
                                if point_doc_id != certificate_doc_id:
                                    continue
                                
                                content = point.content or ''
                                if isinstance(content, bytes):
                                    try:
                                        content = content.decode('utf-8')
                                    except:
                                        try:
                                            content = content.decode('gbk')
                                        except:
                                            content = content.decode('utf-8', errors='ignore')
                                
                                doc_name = None
                                if hasattr(point, 'doc_info') and point.doc_info:
                                    if isinstance(point.doc_info, dict):
                                        doc_name = point.doc_info.get('doc_name', point.doc_info.get('name', ''))
                                    elif hasattr(point.doc_info, 'doc_name'):
                                        doc_name = point.doc_info.doc_name
                                
                                chunk = {
                                    "content": content,
                                    "slice_id": point.point_id or point.chunk_id or '',
                                    "doc_id": point_doc_id,
                                    "doc_name": doc_name,
                                    "image_url": None,
                                    "chunk_type": getattr(point, 'chunk_type', None)
                                }
                            elif isinstance(point, dict):
                                point_doc_id = point.get('doc_id', '') or point.get('document_id', '')
                                
                                if not point_doc_id and 'doc_info' in point:
                                    doc_info = point['doc_info']
                                    if isinstance(doc_info, dict):
                                        point_doc_id = doc_info.get('doc_id', '') or doc_info.get('document_id', '')
                                
                                if point_doc_id != certificate_doc_id:
                                    continue
                                
                                chunk = self._parse_search_result_item(point)
                            
                            if chunk and chunk.get("content"):
                                chunks.append(chunk)
                                from models.schemas import SpecSource
                                references.append(SpecSource(
                                    content=chunk["content"],
                                    slice_id=chunk.get("slice_id", ""),
                                    doc_id=chunk.get("doc_id", ""),
                                    doc_name=chunk.get("doc_name"),
                                    image_url=chunk.get("image_url"),
                                    chunk_type=chunk.get("chunk_type")
                                ))
            
            log_with_time(f"[证书人员查询] [步骤1] 找到 {len(chunks)} 个相关chunk（来自指定文档）")
            
            if not chunks:
                log_with_time(f"[证书人员查询] 未找到相关chunk，返回空结果")
                return {
                    "question": query,
                    "personnel_list": [],
                    "references": references
                }
            
            # 3. 使用AI筛选和格式化人员信息
            api_key = Config.ARK_API_KEY
            if not api_key:
                log_with_time(f"[证书人员查询] 未配置ARK_API_KEY，返回原始chunk")
                from models.schemas import PersonnelInfo
                personnel_list = []
                for chunk in chunks[:20]:
                    personnel_list.append(PersonnelInfo(
                        content=chunk["content"],
                        slice_id=chunk.get("slice_id"),
                        doc_id=chunk.get("doc_id")
                    ))
                return {
                    "question": query,
                    "personnel_list": personnel_list,
                    "references": references[:20]
                }
            
            # 构建prompt，让AI根据用户查询筛选和格式化人员信息
            prompt_start = time.time()
            log_with_time(f"[证书人员查询] [步骤2] 开始构建AI prompt...")
            
            client = OpenAI(
                api_key=api_key,
                base_url=Config.ARK_BASE_URL,
                timeout=180.0,
            )
            
            # 构建上下文内容
            context_parts = []
            for i, chunk in enumerate(chunks[:30]):
                slice_id = chunk.get("slice_id", "")
                content = chunk.get("content", "")[:1500]
                chunk_text = f"point_id: {slice_id}\n内容：{content}"
                context_parts.append(chunk_text)
            
            context_text = "\n".join(context_parts)
            
            # 使用原有的prompt模板，但用用户查询替换查询需求部分
            prompt = f"""# 任务
你是一位专业的人力资源专家，你的任务是根据「参考资料」找出符合用户要求的人员信息，这些信息在 <context></context> XML tags 之内。

# 用户查询需求
{query}

# 数据格式说明
参考资料中可能包含三种不同的表格格式，你需要识别并正确解析：

**格式1：成都公司的sheet页**
字段：序号、姓名、部门、类别、证书名称、证书编号、发证日期、到期日期
- 姓名 → name
- 部门 → department
- 类别 → category
- 证书名称 → certificate_name
- 证书编号 → certificate_number
- 发证日期 → issue_date
- 到期日期 → expiry_date

**格式2：公司各类培训证书的sheet页**
字段：序号、姓名、部门、证书名称、培训机构、发证时间、证书有效期、备注
- 姓名 → name
- 部门 → department
- 证书名称 → certificate_name
- 发证时间 → issue_date
- 证书有效期 → expiry_date（注意：可能是"X年"格式，需要转换为具体日期）
- 备注 → free_status（如果备注中包含空闲状态信息）

**格式3：新疆片区员工证书sheet页**
字段：序号、姓名、部门、作业区、专业、证书名称、证书编号、发证日期、有效日期、备注
- 姓名 → name
- 部门 → department
- 作业区 → category（作业区作为类别）
- 专业 → category（专业也可以作为类别，优先使用作业区）
- 证书名称 → certificate_name
- 证书编号 → certificate_number
- 发证日期 → issue_date
- 有效日期 → expiry_date
- 备注 → free_status（如果备注中包含空闲状态信息）

# 任务要求
1. 仔细分析参考资料中的所有人员信息，识别表格格式
2. 根据用户查询需求筛选出符合条件的人员：
   - 如果用户提到了时间范围，筛选证书有效期可以覆盖该时间范围的人员
   - 如果用户提到了证书类型，筛选证书名称匹配的人员
   - 如果用户提到了人数要求，按人数要求返回相应数量的人员
   - 如果用户提到了空闲状态，筛选空闲状态匹配的人员
3. 从每个符合条件的人员信息中提取以下字段：
   - name（姓名）：必填
   - department（部门）：必填
   - category（类别）：可选，可能是"类别"、"作业区"或"专业"
   - certificate_name（证书名称）：必填
   - certificate_number（证书编号）：可选，格式2可能没有
   - issue_date（发证日期）：必填，格式统一为YYYY-MM-DD
   - expiry_date（到期日期）：必填，格式统一为YYYY-MM-DD
     * 如果是"X年"格式，需要根据发证日期计算
     * 例如：发证日期2020-01-01，有效期3年，则到期日期为2023-01-01
   - free_status（空闲状态）：可选，从备注或其他字段中提取
4. 返回JSON格式的人员列表，格式如下：
```json
{{
  "personnel_list": [
    {{
      "name": "姓名",
      "department": "部门",
      "category": "类别",
      "certificate_name": "证书名称",
      "certificate_number": "证书编号",
      "issue_date": "2024-01-01",
      "expiry_date": "2027-01-01",
      "free_status": "空闲状态",
      "slice_id": "对应的point_id"
    }}
  ]
}}
```

# 注意事项
1. 只返回JSON格式，不要添加任何其他文字说明
2. 如果某个字段在参考资料中找不到，使用空字符串 ""
3. slice_id字段必须使用参考资料中对应的point_id
4. 只返回符合用户查询条件的人员，不符合条件的不要包含
5. 确保日期格式统一为YYYY-MM-DD（如：2024-01-01）
6. 日期计算要准确，注意年份的加减
7. 证书名称匹配要灵活，支持部分匹配
8. 如果同一人员有多条记录，每条记录都要单独返回

# 参考资料
<context>
{context_text}
</context>

请根据用户查询需求和参考资料找出符合要求的人员，并以JSON格式返回。"""
            
            prompt_elapsed = time.time() - prompt_start
            log_with_time(f"[证书人员查询] [步骤2] Prompt构建完成 (耗时: {prompt_elapsed:.2f}秒)，prompt长度: {len(prompt)} 字符")
            
            # 调用AI模型
            ai_start = time.time()
            log_with_time(f"[证书人员查询] [步骤2] 开始调用AI模型分析人员信息 (超时设置: 120秒)...")
            try:
                response = client.chat.completions.create(
                    model=Config.ARK_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一位专业的人力资源专家，能够准确提取和格式化人员信息。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4000,
                    timeout=180.0
                )
                ai_elapsed = time.time() - ai_start
                log_with_time(f"[证书人员查询] [步骤2] AI调用完成 (耗时: {ai_elapsed:.2f}秒)")
                
                ai_response = response.choices[0].message.content.strip()
                log_with_time(f"[证书人员查询] [步骤2] AI响应长度: {len(ai_response)} 字符")
                log_with_time(f"[证书人员查询] [步骤2] AI响应前500字符: {ai_response[:500]}")
                
                # 解析AI返回的JSON
                import json
                import re
                
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    log_with_time(f"[证书人员查询] [步骤3] 从markdown代码块中提取JSON")
                else:
                    json_match = re.search(r'\{.*"personnel_list".*\}', ai_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        log_with_time(f"[证书人员查询] [步骤3] 从文本中提取JSON（包含personnel_list）")
                    else:
                        json_str = ai_response
                        log_with_time(f"[证书人员查询] [步骤3] 使用完整AI响应作为JSON")
                
                log_with_time(f"[证书人员查询] [步骤3] 提取的JSON字符串长度: {len(json_str)} 字符")
                log_with_time(f"[证书人员查询] [步骤3] 提取的JSON前500字符: {json_str[:500]}")
                
                parse_start = time.time()
                log_with_time(f"[证书人员查询] [步骤3] 开始解析AI返回的JSON...")
                try:
                    result_data = json.loads(json_str)
                    log_with_time(f"[证书人员查询] [步骤3] JSON解析成功，result_data类型: {type(result_data)}")
                    log_with_time(f"[证书人员查询] [步骤3] result_data的keys: {list(result_data.keys()) if isinstance(result_data, dict) else 'N/A'}")
                    personnel_list_data = result_data.get("personnel_list", [])
                    log_with_time(f"[证书人员查询] [步骤3] personnel_list_data类型: {type(personnel_list_data)}, 长度: {len(personnel_list_data) if isinstance(personnel_list_data, list) else 'N/A'}")
                    
                    from models.schemas import PersonnelInfo
                    personnel_list = []
                    for person_data in personnel_list_data:
                        slice_id = person_data.get("slice_id", "")
                        # slice_id可能是完整格式（如_sys_auto_gen_doc_id-17526703582802695253-13）或短格式（如17526703582802695253-13）
                        # 需要匹配两种格式
                        chunk_content = ""
                        for chunk in chunks:
                            chunk_slice_id = chunk.get("slice_id", "")
                            # 精确匹配或后缀匹配（slice_id可能是完整格式的一部分）
                            if chunk_slice_id == slice_id or chunk_slice_id.endswith(slice_id) or slice_id.endswith(chunk_slice_id):
                                chunk_content = chunk.get("content", "")
                                break
                        
                        personnel_info = PersonnelInfo(
                            name=person_data.get("name", ""),
                            department=person_data.get("department", ""),
                            category=person_data.get("category", ""),
                            certificate_name=person_data.get("certificate_name", ""),
                            certificate_number=person_data.get("certificate_number", ""),
                            issue_date=person_data.get("issue_date", ""),
                            expiry_date=person_data.get("expiry_date", ""),
                            free_status=person_data.get("free_status", ""),
                            content=chunk_content or person_data.get("name", ""),
                            slice_id=slice_id,
                            doc_id=certificate_doc_id
                        )
                        personnel_list.append(personnel_info)
                    
                    parse_elapsed = time.time() - parse_start
                    log_with_time(f"[证书人员查询] [步骤3] JSON解析完成 (耗时: {parse_elapsed:.2f}秒)，找到 {len(personnel_list)} 个人员")
                    
                except json.JSONDecodeError as json_error:
                    parse_elapsed = time.time() - parse_start
                    log_with_time(f"[证书人员查询] [步骤3] JSON解析失败 (耗时: {parse_elapsed:.2f}秒): {json_error}")
                    log_with_time(f"[证书人员查询] AI返回内容: {ai_response[:500]}")
                    personnel_list = []
                
            except Exception as ai_error:
                ai_elapsed = time.time() - ai_start
                log_with_time(f"[证书人员查询] [步骤2] AI调用失败 (耗时: {ai_elapsed:.2f}秒): {ai_error}")
                import traceback
                traceback.print_exc()
                personnel_list = []
            
            total_elapsed = time.time() - start_time
            log_with_time(f"[证书人员查询] 查询完成 (总耗时: {total_elapsed:.2f}秒)，找到 {len(personnel_list)} 个匹配人员")
            
            return {
                "question": query,
                "personnel_list": personnel_list,
                "references": references[:20]
            }
        
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_with_time(f"[证书人员查询] 查询失败 (总耗时: {total_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            return {
                "question": query,
                "personnel_list": [],
                "references": []
            }

