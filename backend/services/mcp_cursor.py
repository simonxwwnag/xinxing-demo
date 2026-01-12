"""
通过Cursor MCP服务器调用WebSearch工具

由于MCP服务器在Cursor中运行，后端代码无法直接调用。
这个模块提供了通过Cursor MCP接口调用的说明和框架。
"""
import json
from typing import List, Dict, Any
from models.schemas import SupplierInfo

class CursorMCPService:
    """
    Cursor MCP服务调用说明
    
    由于MCP服务器在Cursor中配置，需要通过以下方式之一调用：
    1. 通过AI助手（Cursor AI）调用MCP工具
    2. 如果Cursor提供MCP API，通过API调用
    3. 手动调用后输入结果
    """
    
    @staticmethod
    def search_web_via_cursor(query: str, count: int = 5) -> List[SupplierInfo]:
        """
        通过Cursor MCP调用WebSearch
        
        注意：这个方法需要Cursor环境支持。
        如果无法直接调用，返回空列表，提示用户通过AI助手调用。
        
        Args:
            query: 搜索查询词
            count: 返回结果数量
            
        Returns:
            供应商信息列表
        """
        # 由于MCP在Cursor中运行，后端代码无法直接调用
        # 这里返回空列表，实际调用需要通过AI助手完成
        print(f"[Cursor MCP] 提示: MCP工具需要通过Cursor AI助手调用")
        print(f"[Cursor MCP] 请在Cursor中请求AI助手调用: bailian_web_search")
        print(f"[Cursor MCP] 参数: query='{query}', count={count}")
        
        return []
    
    @staticmethod
    def parse_cursor_mcp_response(response_data: Dict[str, Any]) -> List[SupplierInfo]:
        """
        解析从Cursor MCP返回的响应数据
        
        当通过AI助手调用MCP工具后，将返回的数据传入此方法进行解析。
        
        Args:
            response_data: Cursor MCP返回的响应数据
            
        Returns:
            供应商信息列表
        """
        from services.mcp_proxy import MCPProxyService
        return MCPProxyService.parse_search_results([response_data])

