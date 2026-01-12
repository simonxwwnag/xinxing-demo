from fastapi import APIRouter, HTTPException
from services.knowledge_service import KnowledgeService, refresh_image_link
from models.schemas import (
    KnowledgeSearchRequest, KnowledgeSearchResponse, 
    SpecSearchResponse, SupplierSearchResponse,
    QARequest, QAResponse,
    CertificatePersonnelRequest, CertificatePersonnelResponse,
    SpecSource, SupplierInfo
)
from pydantic import BaseModel, Field
from typing import Optional
import time
from datetime import datetime

router = APIRouter()
knowledge_service = KnowledgeService()

def log_with_time(message: str):
    """带时间戳的日志输出"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] {message}")

@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    知识库查询：搜索产品规格和供应商信息
    规格参数会调用AI进行总结，总结内容中包含引用标签，可以点击查看知识库源文件
    规格参数和供应商信息顺序查询，分别处理和返回
    """
    start_time = time.time()
    log_with_time(f"[API] ========== 开始查询知识库 ==========")
    log_with_time(f"[API] 产品名称: {request.product_name}, 特征: {request.product_features}")
    
    try:
        # 搜索并总结规格参数（调用AI总结）
        spec_start_time = time.time()
        log_with_time(f"[API] [顺序-规格] 开始搜索并总结规格参数...")
        try:
            spec_result = knowledge_service.summarize_specs(
                request.product_name,
                request.product_features
            )
            spec_elapsed = time.time() - spec_start_time
            log_with_time(f"[API] [顺序-规格] 规格总结完成 (耗时: {spec_elapsed:.2f}秒)，总结长度: {len(spec_result.get('summary', '') or '')} 字符，引用数量: {len(spec_result.get('references', []))}")
        except Exception as e:
            spec_elapsed = time.time() - spec_start_time
            log_with_time(f"[API] [顺序-规格] 规格总结失败 (耗时: {spec_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            # 如果总结失败，降级为只返回原始chunk
            try:
                specs = knowledge_service.search_specs(
                    request.product_name,
                    request.product_features
                )
                spec_result = {
                    "summary": f"总结失败，找到 {len(specs)} 条规格信息，请查看下方参考内容。",
                    "references": specs
                }
                log_with_time(f"[API] [顺序-规格] 降级处理：返回原始chunk，数量: {len(specs)}")
            except Exception as fallback_error:
                log_with_time(f"[API] [顺序-规格] 降级处理也失败: {fallback_error}")
                spec_result = {
                    "summary": None,
                    "references": []
                }
                log_with_time(f"[API] [顺序-规格] 搜索失败，返回空结果")
        
        # 顺序执行供应商搜索
        supplier_start_time = time.time()
        log_with_time(f"[API] [顺序-供应商] 开始搜索供应商...")
        try:
            suppliers = knowledge_service.search_suppliers_from_docs(
                request.product_name,
                request.product_features
            )
            supplier_elapsed = time.time() - supplier_start_time
            log_with_time(f"[API] [顺序-供应商] 供应商搜索完成 (耗时: {supplier_elapsed:.2f}秒)，找到 {len(suppliers)} 个供应商")
        except Exception as e:
            supplier_elapsed = time.time() - supplier_start_time
            log_with_time(f"[API] [顺序-供应商] 供应商搜索失败 (耗时: {supplier_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            suppliers = []
        
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 查询完成 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 规格数量: {len(spec_result.get('references', []))}")
        log_with_time(f"[API] 供应商数量: {len(suppliers)}")
        
        # 转换specs格式
        specs_raw = spec_result.get("references", [])
        log_with_time(f"[API] 开始转换specs，原始数量: {len(specs_raw)}")
        specs = []
        for i, spec in enumerate(specs_raw):
            try:
                if isinstance(spec, SpecSource):
                    # 已经是SpecSource对象，直接添加
                    specs.append(spec)
                    log_with_time(f"[API] spec {i+1} 已经是SpecSource对象，slice_id: {spec.slice_id}")
                elif isinstance(spec, dict):
                    # 字典格式，转换为SpecSource对象
                    spec_source = SpecSource(
                        content=spec.get("content", ""),
                        slice_id=spec.get("slice_id", ""),
                        doc_id=spec.get("doc_id", ""),
                        doc_name=spec.get("doc_name"),
                        image_url=spec.get("image_url"),
                        chunk_type=spec.get("chunk_type"),
                        md_content=spec.get("md_content"),
                        html_content=spec.get("html_content"),
                        point_id=spec.get("point_id")
                    )
                    specs.append(spec_source)
                    log_with_time(f"[API] spec {i+1} 转换成功，slice_id: {spec_source.slice_id}")
                else:
                    log_with_time(f"[API] 警告: spec {i+1} 类型未知: {type(spec)}，跳过")
            except Exception as spec_error:
                log_with_time(f"[API] 转换spec {i+1} 失败: {spec_error}")
                import traceback
                traceback.print_exc()
        
        log_with_time(f"[API] specs转换完成，最终数量: {len(specs)}")
        
        # 转换suppliers格式
        suppliers_raw = suppliers if isinstance(suppliers, list) else []
        log_with_time(f"[API] 开始转换suppliers，原始数量: {len(suppliers_raw)}")
        suppliers_list = []
        for i, supplier in enumerate(suppliers_raw):
            try:
                if isinstance(supplier, SupplierInfo):
                    # 已经是SupplierInfo对象，直接添加
                    content_len = len(supplier.content) if supplier.content else 0
                    log_with_time(f"[API] supplier {i+1} 已经是SupplierInfo对象，name: {supplier.name}, content长度: {content_len}")
                    suppliers_list.append(supplier)
                elif isinstance(supplier, dict):
                    # 字典格式，转换为SupplierInfo对象
                    content_value = supplier.get("content", "")
                    content_len = len(content_value) if content_value else 0
                    log_with_time(f"[API] supplier {i+1} 字典格式，name: {supplier.get('name', '')}, content长度: {content_len}")
                    supplier_info = SupplierInfo(
                        name=supplier.get("name", ""),
                        source=supplier.get("source", "knowledge_base"),
                        doc_id=supplier.get("doc_id"),
                        doc_name=supplier.get("doc_name"),
                        url=supplier.get("url"),
                        description=supplier.get("description"),
                        slice_id=supplier.get("slice_id"),
                        content=content_value,
                        supplier_type=supplier.get("supplier_type"),
                        sub_category_name=supplier.get("sub_category_name"),
                        valid_from=supplier.get("valid_from"),
                        valid_to=supplier.get("valid_to"),
                        contact_person=supplier.get("contact_person"),
                        relevance=supplier.get("relevance")  # 添加relevance字段
                    )
                    suppliers_list.append(supplier_info)
                    log_with_time(f"[API] supplier {i+1} 转换成功，name: {supplier_info.name}, content长度: {len(supplier_info.content) if supplier_info.content else 0}")
                else:
                    log_with_time(f"[API] 警告: supplier {i+1} 类型未知: {type(supplier)}，跳过")
            except Exception as supplier_error:
                log_with_time(f"[API] 转换supplier {i+1} 失败: {supplier_error}")
                import traceback
                traceback.print_exc()
        
        log_with_time(f"[API] suppliers转换完成，最终数量: {len(suppliers_list)}")
        
        # 构建响应（包含spec_summary）
        spec_summary = spec_result.get("summary")
        log_with_time(f"[API] 准备返回响应: specs数量={len(specs)}, suppliers数量={len(suppliers_list)}, spec_summary长度={len(spec_summary or '')}")
        
        response = KnowledgeSearchResponse(
            specs=specs,
            suppliers=suppliers_list,
            spec_summary=spec_summary  # 返回AI总结的规格参数
        )
        
        log_with_time(f"[API] 响应对象创建成功")
        return response
    
    except Exception as e:
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 知识库查询异常 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 异常信息: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"知识库查询失败: {str(e)}")

@router.post("/search-specs", response_model=SpecSearchResponse)
async def search_specs_only(request: KnowledgeSearchRequest):
    """
    只搜索产品规格信息（独立API）
    规格参数会调用AI进行总结，总结内容中包含引用标签
    """
    start_time = time.time()
    log_with_time(f"[API] ========== 开始搜索规格 ==========")
    log_with_time(f"[API] 产品名称: {request.product_name}, 特征: {request.product_features}")
    
    try:
        # 搜索并总结规格参数
        spec_start_time = time.time()
        log_with_time(f"[API] [规格] 开始搜索并总结规格参数...")
        try:
            spec_result = knowledge_service.summarize_specs(
                request.product_name,
                request.product_features
            )
            spec_elapsed = time.time() - spec_start_time
            log_with_time(f"[API] [规格] 规格总结完成 (耗时: {spec_elapsed:.2f}秒)，总结长度: {len(spec_result.get('summary', '') or '')} 字符，引用数量: {len(spec_result.get('references', []))}")
        except Exception as e:
            spec_elapsed = time.time() - spec_start_time
            log_with_time(f"[API] [规格] 规格总结失败 (耗时: {spec_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            # 如果总结失败，降级为只返回原始chunk
            try:
                specs = knowledge_service.search_specs(
                    request.product_name,
                    request.product_features
                )
                spec_result = {
                    "summary": f"总结失败，找到 {len(specs)} 条规格信息，请查看下方参考内容。",
                    "references": specs
                }
                log_with_time(f"[API] [规格] 降级处理：返回原始chunk，数量: {len(specs)}")
            except Exception as fallback_error:
                log_with_time(f"[API] [规格] 降级处理也失败: {fallback_error}")
                spec_result = {
                    "summary": None,
                    "references": []
                }
        
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 规格搜索完成 (总耗时: {total_elapsed:.2f}秒) ==========")
        
        # 转换specs格式
        specs_raw = spec_result.get("references", [])
        log_with_time(f"[API] 开始转换specs，原始数量: {len(specs_raw)}")
        specs = []
        for i, spec in enumerate(specs_raw):
            try:
                if isinstance(spec, SpecSource):
                    specs.append(spec)
                    log_with_time(f"[API] spec {i+1} 已经是SpecSource对象，slice_id: {spec.slice_id}")
                elif isinstance(spec, dict):
                    spec_source = SpecSource(
                        content=spec.get("content", ""),
                        slice_id=spec.get("slice_id", ""),
                        doc_id=spec.get("doc_id", ""),
                        doc_name=spec.get("doc_name"),
                        image_url=spec.get("image_url"),
                        chunk_type=spec.get("chunk_type"),
                        md_content=spec.get("md_content"),
                        html_content=spec.get("html_content"),
                        point_id=spec.get("point_id")
                    )
                    specs.append(spec_source)
                    log_with_time(f"[API] spec {i+1} 转换成功，slice_id: {spec_source.slice_id}")
                else:
                    log_with_time(f"[API] 警告: spec {i+1} 类型未知: {type(spec)}，跳过")
            except Exception as spec_error:
                log_with_time(f"[API] 转换spec {i+1} 失败: {spec_error}")
                import traceback
                traceback.print_exc()
        
        log_with_time(f"[API] specs转换完成，最终数量: {len(specs)}")
        
        # 构建响应
        spec_summary = spec_result.get("summary")
        response = SpecSearchResponse(
            specs=specs,
            spec_summary=spec_summary
        )
        
        log_with_time(f"[API] 响应对象创建成功")
        return response
    
    except Exception as e:
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 规格搜索异常 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 异常信息: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"规格搜索失败: {str(e)}")

@router.post("/search-suppliers", response_model=SupplierSearchResponse)
async def search_suppliers_only(request: KnowledgeSearchRequest):
    """
    只搜索供应商信息（独立API）
    从供应商文档中搜索，并使用AI过滤不相关的供应商
    """
    start_time = time.time()
    log_with_time(f"[API] ========== 开始搜索供应商 ==========")
    log_with_time(f"[API] 产品名称: {request.product_name}, 特征: {request.product_features}")
    
    try:
        # 搜索供应商
        supplier_start_time = time.time()
        log_with_time(f"[API] [供应商] 开始搜索供应商...")
        try:
            suppliers = knowledge_service.search_suppliers_from_docs(
                request.product_name,
                request.product_features
            )
            supplier_elapsed = time.time() - supplier_start_time
            log_with_time(f"[API] [供应商] 供应商搜索完成 (耗时: {supplier_elapsed:.2f}秒)，找到 {len(suppliers)} 个供应商")
        except Exception as e:
            supplier_elapsed = time.time() - supplier_start_time
            log_with_time(f"[API] [供应商] 供应商搜索失败 (耗时: {supplier_elapsed:.2f}秒): {e}")
            import traceback
            traceback.print_exc()
            suppliers = []
        
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 供应商搜索完成 (总耗时: {total_elapsed:.2f}秒) ==========")
        
        # 转换suppliers格式
        suppliers_raw = suppliers if isinstance(suppliers, list) else []
        log_with_time(f"[API] 开始转换suppliers，原始数量: {len(suppliers_raw)}")
        suppliers_list = []
        for i, supplier in enumerate(suppliers_raw):
            try:
                if isinstance(supplier, SupplierInfo):
                    suppliers_list.append(supplier)
                    log_with_time(f"[API] supplier {i+1} 已经是SupplierInfo对象，name: {supplier.name}")
                elif isinstance(supplier, dict):
                    supplier_info = SupplierInfo(
                        name=supplier.get("name", ""),
                        source=supplier.get("source", "knowledge_base"),
                        doc_id=supplier.get("doc_id"),
                        doc_name=supplier.get("doc_name"),
                        url=supplier.get("url"),
                        description=supplier.get("description"),
                        slice_id=supplier.get("slice_id"),
                        content=supplier.get("content"),
                        supplier_type=supplier.get("supplier_type"),
                        sub_category_name=supplier.get("sub_category_name"),
                        valid_from=supplier.get("valid_from"),
                        valid_to=supplier.get("valid_to"),
                        contact_person=supplier.get("contact_person"),
                        relevance=supplier.get("relevance")
                    )
                    suppliers_list.append(supplier_info)
                    log_with_time(f"[API] supplier {i+1} 转换成功，name: {supplier_info.name}")
                else:
                    log_with_time(f"[API] 警告: supplier {i+1} 类型未知: {type(supplier)}，跳过")
            except Exception as supplier_error:
                log_with_time(f"[API] 转换supplier {i+1} 失败: {supplier_error}")
                import traceback
                traceback.print_exc()
        
        log_with_time(f"[API] suppliers转换完成，最终数量: {len(suppliers_list)}")
        
        # 构建响应
        response = SupplierSearchResponse(
            suppliers=suppliers_list
        )
        
        log_with_time(f"[API] 响应对象创建成功")
        return response
    
    except Exception as e:
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 供应商搜索异常 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 异常信息: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"供应商搜索失败: {str(e)}")

@router.post("/qa", response_model=QAResponse)
async def answer_question(request: QARequest):
    """
    项目专家问答：通过问题搜索知识库，使用qwen模型总结答案
    """
    start_time = time.time()
    log_with_time(f"[API] ========== 开始问答 ==========")
    log_with_time(f"[API] 问题: {request.question}")
    
    try:
        result = knowledge_service.answer_question(request.question)
        
        log_with_time(f"[API] 服务返回结果类型: {type(result)}")
        log_with_time(f"[API] 服务返回结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        log_with_time(f"[API] answer长度: {len(result.get('answer', '')) if isinstance(result, dict) else 'N/A'}")
        log_with_time(f"[API] references数量: {len(result.get('references', [])) if isinstance(result, dict) else 'N/A'}")
        
        # 转换references格式
        references = []
        refs_raw = result.get("references", [])
        log_with_time(f"[API] 开始转换references，原始数量: {len(refs_raw)}")
        
        for i, ref in enumerate(refs_raw):
            try:
                log_with_time(f"[API] 转换reference {i+1}/{len(refs_raw)}，类型: {type(ref)}")
                if isinstance(ref, dict):
                    from models.schemas import SpecSource
                    spec_source = SpecSource(
                        content=ref.get("content", ""),
                        slice_id=ref.get("slice_id", ""),
                        doc_id=ref.get("doc_id", ""),
                        doc_name=ref.get("doc_name"),
                        image_url=ref.get("image_url"),
                        chunk_type=ref.get("chunk_type")
                    )
                    references.append(spec_source)
                    log_with_time(f"[API] reference {i+1} 转换成功，slice_id: {spec_source.slice_id}")
                else:
                    log_with_time(f"[API] 警告: reference {i+1} 不是字典类型，跳过")
            except Exception as ref_error:
                log_with_time(f"[API] 转换reference {i+1} 失败: {ref_error}")
                import traceback
                traceback.print_exc()
        
        log_with_time(f"[API] references转换完成，最终数量: {len(references)}")
        
        response = QAResponse(
            answer=result.get("answer", ""),
            references=references
        )
        
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 问答完成 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 最终返回answer长度: {len(response.answer)}")
        log_with_time(f"[API] 最终返回references数量: {len(response.references)}")
        
        return response
    
    except Exception as e:
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 问答异常 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 异常信息: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")

@router.post("/certificate-personnel", response_model=CertificatePersonnelResponse)
async def search_certificate_personnel(request: CertificatePersonnelRequest):
    """
    证书人员查询：根据自然语言描述查询匹配的人员信息
    AI会自动解析标段时间、证书要求、空闲状态等信息
    """
    start_time = time.time()
    log_with_time(f"[API] ========== 开始证书人员查询 ==========")
    log_with_time(f"[API] 查询需求: {request.query}")
    
    try:
        result = knowledge_service.search_certificate_personnel_by_query(request.query)
        
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 证书人员查询完成 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 返回结果: question={result.get('question', '')}, personnel_count={len(result.get('personnel_list', []))}, references_count={len(result.get('references', []))}")
        
        personnel_list = result.get("personnel_list", [])
        references_raw = result.get("references", [])
        
        # 确保personnel_list是列表
        if not isinstance(personnel_list, list):
            log_with_time(f"[API] 警告: personnel_list不是列表类型: {type(personnel_list)}")
            personnel_list = []
        
        # 转换personnel_list格式，确保每个项都是PersonnelInfo对象
        from models.schemas import PersonnelInfo
        processed_personnel_list = []
        for person in personnel_list:
            if isinstance(person, PersonnelInfo):
                # 已经是PersonnelInfo对象，直接添加
                processed_personnel_list.append(person)
            elif isinstance(person, dict):
                # 字典格式，转换为PersonnelInfo对象
                processed_personnel_list.append(PersonnelInfo(
                    name=person.get("name"),
                    department=person.get("department"),
                    category=person.get("category"),
                    certificate_name=person.get("certificate_name"),
                    certificate_number=person.get("certificate_number"),
                    issue_date=person.get("issue_date"),
                    expiry_date=person.get("expiry_date"),
                    free_status=person.get("free_status"),
                    content=person.get("content", ""),
                    slice_id=person.get("slice_id"),
                    doc_id=person.get("doc_id")
                ))
            else:
                log_with_time(f"[API] 警告: personnel_list中的项类型未知: {type(person)}")
        
        # 转换references格式（如果是SpecSource对象，FastAPI会自动序列化）
        references = []
        if isinstance(references_raw, list):
            for ref in references_raw:
                if isinstance(ref, SpecSource):
                    # SpecSource对象，FastAPI会自动序列化为JSON
                    references.append(ref)
                elif isinstance(ref, dict):
                    # 字典格式，转换为SpecSource对象
                    references.append(SpecSource(
                        content=ref.get("content", ""),
                        slice_id=ref.get("slice_id", ""),
                        doc_id=ref.get("doc_id", ""),
                        doc_name=ref.get("doc_name"),
                        image_url=ref.get("image_url"),
                        chunk_type=ref.get("chunk_type")
                    ))
                else:
                    log_with_time(f"[API] 警告: references中的项类型未知: {type(ref)}")
        else:
            log_with_time(f"[API] 警告: references不是列表类型: {type(references_raw)}")
        
        log_with_time(f"[API] 最终返回: personnel_list长度={len(processed_personnel_list)}, references长度={len(references)}")
        if len(processed_personnel_list) > 0:
            first_person = processed_personnel_list[0]
            log_with_time(f"[API] 第一个人员信息: name={first_person.name if hasattr(first_person, 'name') else first_person.get('name', 'N/A') if isinstance(first_person, dict) else 'N/A'}")
            log_with_time(f"[API] 第一个人员信息完整内容: {first_person}")
        
        return CertificatePersonnelResponse(
            question=result.get("question", request.query),
            personnel_list=processed_personnel_list,
            references=references
        )
    
    except Exception as e:
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 证书人员查询异常 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 异常信息: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"证书人员查询失败: {str(e)}")

class RefreshImageLinkRequest(BaseModel):
    """刷新图片链接请求"""
    slice_id: str = Field(..., description="切片ID")

class RefreshImageLinkResponse(BaseModel):
    """刷新图片链接响应"""
    image_url: Optional[str] = Field(None, description="新的图片链接")
    success: bool = Field(..., description="是否成功")

@router.post("/refresh-image-link", response_model=RefreshImageLinkResponse)
async def refresh_image_link_api(request: RefreshImageLinkRequest):
    """
    刷新过期的图片链接
    当图片链接过期时，前端可以调用此接口重新获取图片链接
    """
    start_time = time.time()
    log_with_time(f"[API] ========== 刷新图片链接 ==========")
    log_with_time(f"[API] slice_id: {request.slice_id}")
    
    try:
        # 调用服务刷新图片链接
        new_image_url = refresh_image_link(knowledge_service, request.slice_id)
        
        if new_image_url:
            log_with_time(f"[API] 图片链接刷新成功: {new_image_url[:50]}...")
            return RefreshImageLinkResponse(
                image_url=new_image_url,
                success=True
            )
        else:
            log_with_time(f"[API] 图片链接刷新失败：未找到对应的chunk或没有图片")
            return RefreshImageLinkResponse(
                image_url=None,
                success=False
            )
    
    except Exception as e:
        total_elapsed = time.time() - start_time
        log_with_time(f"[API] ========== 刷新图片链接异常 (总耗时: {total_elapsed:.2f}秒) ==========")
        log_with_time(f"[API] 异常信息: {e}")
        import traceback
        traceback.print_exc()
        return RefreshImageLinkResponse(
            image_url=None,
            success=False
        )

