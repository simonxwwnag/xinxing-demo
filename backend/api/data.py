from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from services.data_service import DataService
from models.schemas import Product, ProductUpdate, SpecSource, SupplierInfo

router = APIRouter()
data_service = DataService()

class UpdateSpecsAndSuppliersRequest(BaseModel):
    specs: Optional[List[SpecSource]] = None
    suppliers: Optional[List[SupplierInfo]] = None
    spec_summary: Optional[str] = None

@router.get("/products", response_model=List[Product])
async def get_all_products(project_id: Optional[str] = None):
    """获取所有产品数据，可指定project_id筛选"""
    try:
        return data_service.get_all_products(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取产品列表失败: {str(e)}")

@router.put("/products/{product_id}/specs-suppliers", response_model=Product)
async def update_product_specs_and_suppliers(
    product_id: str, 
    request: UpdateSpecsAndSuppliersRequest,
    project_id: Optional[str] = None
):
    """更新产品的规格和供应商信息"""
    try:
        specs = [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in (request.specs or [])]
        suppliers = [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in (request.suppliers or [])]
        
        # 调试：检查suppliers中的content字段
        for i, supplier in enumerate(suppliers[:3], 1):  # 只检查前3个
            content = supplier.get('content', '')
            content_len = len(content) if content else 0
            print(f"[API] 保存供应商 {i}: {supplier.get('name', 'N/A')}, content长度: {content_len}")
            if not content:
                print(f"[API] ⚠️  供应商 {i} 的content为空！所有字段: {list(supplier.keys())}")
            else:
                print(f"[API] ✅ 供应商 {i} 的content前50字符: {content[:50]}...")
        
        product = data_service.update_product_specs_and_suppliers(
            product_id, specs, suppliers, request.spec_summary, project_id
        )
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新规格和供应商失败: {str(e)}")

@router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, update_data: ProductUpdate, project_id: Optional[str] = None):
    """更新产品信息"""
    try:
        product = data_service.update_product(product_id, update_data, project_id)
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新产品失败: {str(e)}")

@router.post("/products/{product_id}/complete", response_model=Product)
async def complete_inquiry(product_id: str, project_id: Optional[str] = None):
    """标记询价完成"""
    try:
        product = data_service.mark_inquiry_completed(product_id, project_id)
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记询价完成失败: {str(e)}")

@router.delete("/products/{product_id}")
async def delete_product(product_id: str, project_id: Optional[str] = None):
    """删除产品"""
    try:
        success = data_service.delete_product(product_id, project_id)
        if not success:
            raise HTTPException(status_code=404, detail="产品不存在")
        return {"message": "产品已删除", "product_id": product_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除产品失败: {str(e)}")

