from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: str = Field(..., description="项目ID")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProductBase(BaseModel):
    project_id: str = Field(..., description="所属项目ID")
    project_code: str = Field(..., description="项目编码")
    project_name: str = Field(..., description="项目名称")
    project_features: Optional[str] = Field(None, description="项目特征（原始规格）")
    unit: str = Field(..., description="计量单位")
    quantity: float = Field(..., description="工程量")

class SpecSource(BaseModel):
    """规格来源切片信息"""
    content: str = Field(..., description="规格内容")
    slice_id: str = Field(..., description="切片ID")
    doc_id: str = Field(..., description="文档ID")
    doc_name: Optional[str] = Field(None, description="文档名称")
    image_url: Optional[str] = Field(None, description="图片链接（当chunk_type为image时）")
    chunk_type: Optional[str] = Field(None, description="切片类型（image/text等）")
    # 新增字段：支持多种内容格式
    md_content: Optional[str] = Field(None, description="Markdown格式内容")
    html_content: Optional[str] = Field(None, description="HTML格式内容")
    point_id: Optional[str] = Field(None, description="点ID（用于追踪）")

class SupplierInfo(BaseModel):
    """供应商信息"""
    name: str = Field(..., description="供应商名称")
    source: str = Field(..., description="来源：knowledge_base或web_search")
    doc_id: Optional[str] = Field(None, description="文档ID（知识库来源）")
    doc_name: Optional[str] = Field(None, description="文档名称（知识库来源）")
    url: Optional[str] = Field(None, description="链接（网络搜索来源）")
    description: Optional[str] = Field(None, description="描述信息")
    slice_id: Optional[str] = Field(None, description="切片ID（知识库来源，用于查看原文）")
    content: Optional[str] = Field(None, description="原始内容（知识库来源，用于查看原文）")
    # 结构化数据字段（用于知识库供应商的表格显示）
    product_code: Optional[str] = Field(None, description="产品编码")
    product_name: Optional[str] = Field(None, description="产品名称")
    supplier_type: Optional[str] = Field(None, description="供应商类型（制造商/供货商）")
    sub_category_name: Optional[str] = Field(None, description="子分类名称")
    sub_category_code: Optional[str] = Field(None, description="子分类编码")
    valid_from: Optional[str] = Field(None, description="有效期开始日期")
    valid_to: Optional[str] = Field(None, description="有效期结束日期")
    contact_person: Optional[str] = Field(None, description="联系人")
    relevance: Optional[str] = Field(None, description="相关性标记（强相关/可能相关）")

class ProductCreateFromExcel(BaseModel):
    """从Excel解析的产品数据（不包含project_id）"""
    project_code: str = Field(..., description="项目编码")
    project_name: str = Field(..., description="项目名称")
    project_features: Optional[str] = Field(None, description="项目特征（原始规格）")
    unit: str = Field(..., description="计量单位")
    quantity: float = Field(..., description="工程量")

class ProductCreate(ProductCreateFromExcel):
    """创建产品请求（包含project_id）"""
    project_id: str = Field(..., description="所属项目ID")

class ProductUpdate(BaseModel):
    price: Optional[float] = Field(None, description="价格")
    price_unit: Optional[str] = Field(None, description="价格单位")
    notes: Optional[str] = Field(None, description="备注")
    inquiry_completed: Optional[bool] = Field(None, description="询价完成状态")

class Product(ProductBase):
    id: str = Field(..., description="产品ID")
    other_specs: List[SpecSource] = Field(default_factory=list, description="其他文件相关规格汇总")
    suppliers: List[SupplierInfo] = Field(default_factory=list, description="供应商列表")
    spec_summary: Optional[str] = Field(None, description="规格参数总结内容")
    price: Optional[float] = Field(None, description="价格")
    price_unit: Optional[str] = Field(None, description="价格单位")
    notes: Optional[str] = Field(None, description="备注")
    inquiry_completed: bool = Field(default=False, description="询价完成状态")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class KnowledgeSearchRequest(BaseModel):
    product_name: str = Field(..., description="产品名称")
    product_features: Optional[str] = Field(None, description="产品特征")

class KnowledgeSearchResponse(BaseModel):
    specs: List[SpecSource] = Field(default_factory=list, description="规格引用列表")
    suppliers: List[SupplierInfo] = Field(default_factory=list, description="供应商信息")
    spec_summary: Optional[str] = Field(None, description="规格参数总结内容")

class SpecSearchResponse(BaseModel):
    """规格搜索响应"""
    specs: List[SpecSource] = Field(default_factory=list, description="规格引用列表")
    spec_summary: Optional[str] = Field(None, description="规格参数总结内容")

class SupplierSearchResponse(BaseModel):
    """供应商搜索响应"""
    suppliers: List[SupplierInfo] = Field(default_factory=list, description="供应商信息")

class WebSearchRequest(BaseModel):
    product_name: str = Field(..., description="产品名称")
    limit: int = Field(default=5, description="返回结果数量限制")

class WebSearchResponse(BaseModel):
    suppliers: List[SupplierInfo] = Field(default_factory=list, description="供应商搜索结果")

class QARequest(BaseModel):
    question: str = Field(..., description="用户问题")

class QAResponse(BaseModel):
    answer: str = Field(..., description="AI总结的答案")
    references: List[SpecSource] = Field(default_factory=list, description="参考的知识库chunk")

class CertificatePersonnelRequest(BaseModel):
    """证书人员查询请求"""
    query: str = Field(..., description="自然语言查询需求，例如：标段时间：2026年1月到2026年3月，需要2个一级建造师注册证书的人员，需要3个HSE培训证书的人员，空闲状态：空闲")

class PersonnelInfo(BaseModel):
    """人员信息"""
    name: Optional[str] = Field(None, description="姓名")
    department: Optional[str] = Field(None, description="部门")
    category: Optional[str] = Field(None, description="类别")
    certificate_name: Optional[str] = Field(None, description="证书名称")
    certificate_number: Optional[str] = Field(None, description="证书编号")
    issue_date: Optional[str] = Field(None, description="发证日期")
    expiry_date: Optional[str] = Field(None, description="到期日期")
    free_status: Optional[str] = Field(None, description="空闲状态")
    content: str = Field(..., description="原始内容")
    slice_id: Optional[str] = Field(None, description="切片ID")
    doc_id: Optional[str] = Field(None, description="文档ID")

class CertificatePersonnelResponse(BaseModel):
    """证书人员查询响应"""
    question: str = Field(..., description="转换后的问题")
    personnel_list: List[PersonnelInfo] = Field(default_factory=list, description="匹配的人员列表")
    references: List[SpecSource] = Field(default_factory=list, description="参考的知识库chunk")

