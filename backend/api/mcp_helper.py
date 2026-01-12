"""
MCP工具辅助API
用于手动输入MCP工具返回的结果
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from services.mcp_proxy import MCPProxyService
from models.schemas import SupplierInfo, WebSearchResponse

router = APIRouter()

class MCPResponseInput(BaseModel):
    """MCP工具返回的原始响应数据"""
    response_data: Dict[str, Any]

@router.post("/mcp/parse-response", response_model=WebSearchResponse)
async def parse_mcp_response(input_data: MCPResponseInput):
    """
    解析从Cursor MCP工具返回的响应数据
    
    使用场景：
    1. 在Cursor中通过AI助手调用 bailian_web_search 工具
    2. 获取MCP工具返回的响应数据
    3. 将响应数据通过此API传入，自动解析为供应商列表
    
    示例请求：
    ```json
    {
      "response_data": {
        "isError": false,
        "content": [
          {
            "text": "{\"status\":0,\"pages\":[{\"snippet\":\"...\", \"url\":\"...\"}]}",
            "type": "text"
          }
        ]
      }
    }
    ```
    """
    try:
        # 使用已有的解析逻辑
        suppliers = MCPProxyService.parse_search_results([input_data.response_data])
        
        return WebSearchResponse(suppliers=suppliers)
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"解析MCP响应失败: {str(e)}"
        )
