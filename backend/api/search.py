from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import WebSearchRequest, WebSearchResponse, SupplierInfo
from services.data_service import DataService
from services.mcp_proxy import MCPProxyService
from typing import List
import asyncio

router = APIRouter()
data_service = DataService()
mcp_proxy = MCPProxyService()

@router.post("/suppliers", response_model=WebSearchResponse)
async def search_suppliers(request: WebSearchRequest):
    """
    网络搜索供应商
    
    通过MCP SSE Endpoint调用WebSearch工具。
    
    注意：由于MCP工具需要在MCP环境中调用（如Cursor AI），
    如果直接HTTP调用返回空结果，需要通过以下方式：
    1. 在Cursor AI中调用MCP工具（推荐用于演示）
    2. 使用MCP SDK（如果可用）
    3. 通过MCP服务器代理调用
    
    MCP配置（已在Cursor中配置）：
    {
      "mcpServers": {
        "type": "sse",
        "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
        "headers": {
          "Authorization": "Bearer ${DASHSCOPE_API_KEY}"
        }
      }
    }
    """
    try:
        # 构建搜索查询
        query = f"{request.product_name} 供应商 厂家"
        
        # 尝试通过MCP代理服务调用SSE Endpoint
        # 注意：如果返回空结果，说明需要通过MCP环境调用
        suppliers = mcp_proxy.search_web(query, request.limit)
        
        # 如果返回空结果，记录提示信息
        if not suppliers:
            print(f"[API] MCP搜索返回空结果")
            print(f"[API] 提示: 需要通过MCP环境调用（Cursor AI或MCP SDK）")
            print(f"[API] 在Cursor AI中输入: 搜索 '{query}'")
        
        return WebSearchResponse(suppliers=suppliers)
    
    except Exception as e:
        # 如果调用失败，返回空结果并记录错误
        print(f"[API] MCP搜索调用失败: {e}")
        import traceback
        traceback.print_exc()
        return WebSearchResponse(suppliers=[])

@router.post("/suppliers/{product_id}", response_model=WebSearchResponse)
async def search_suppliers_for_product(product_id: str, request: WebSearchRequest):
    """
    为特定产品搜索供应商并更新产品信息
    
    通过MCP SSE Endpoint搜索供应商，然后自动更新产品信息
    """
    try:
        # 构建搜索查询
        query = f"{request.product_name} 供应商 厂家"
        
        # 通过MCP代理服务调用SSE Endpoint搜索供应商
        suppliers = mcp_proxy.search_web(query, request.limit)
        
        # 更新产品信息
        product = data_service.get_product(product_id)
        if product:
            # 合并现有供应商和新搜索的供应商
            existing_suppliers = [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in product.suppliers]
            new_suppliers = [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in suppliers]
            
            # 去重：基于供应商名称
            seen_names = {s.get('name') for s in existing_suppliers}
            unique_new_suppliers = [
                s for s in new_suppliers 
                if s.get('name') not in seen_names
            ]
            
            all_suppliers = existing_suppliers + unique_new_suppliers
            
            # 更新产品
            data_service.update_product_specs_and_suppliers(
                product_id,
                [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in product.other_specs],
                all_suppliers
            )
        
        return WebSearchResponse(suppliers=suppliers)
    except Exception as e:
        print(f"[API] 搜索并更新供应商失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"搜索供应商失败: {str(e)}")
