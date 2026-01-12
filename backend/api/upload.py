from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional
import tempfile
import os
from services.excel_parser import ExcelParser
from services.data_service import DataService
from services.knowledge_service import KnowledgeService
from services.search_service import SearchService
from models.schemas import Product

router = APIRouter()
excel_parser = ExcelParser()
data_service = DataService()
knowledge_service = KnowledgeService()
search_service = SearchService()

@router.post("/upload", response_model=List[Product])
async def upload_excel(
    file: UploadFile = File(...),
    project_id: str = Form(...)
):
    """
    上传Excel文件并解析
    """
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件 (.xlsx, .xls)")
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # 解析Excel
        products_data = excel_parser.parse_excel(tmp_file_path)
        
        # 处理每个产品：先创建产品基本信息，不查询知识库
        # 知识库查询将在前端异步进行
        result_products = []
        for product_data in products_data:
            # 创建产品（只包含基本信息，不包含规格和供应商）
            from models.schemas import ProductCreate
            product_create = ProductCreate(
                project_id=project_id,
                project_code=product_data.project_code,
                project_name=product_data.project_name,
                project_features=product_data.project_features,
                unit=product_data.unit,
                quantity=product_data.quantity
            )
            # 创建产品时不传入specs和suppliers，让它们为空数组
            product = data_service.create_product(
                product_create,
                specs=[],
                suppliers=[]
            )
            
            result_products.append(product)
        
        return result_products
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文件时出错: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

