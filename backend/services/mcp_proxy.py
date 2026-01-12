"""
MCP工具代理服务
通过HTTP SSE Endpoint调用MCP WebSearch工具

注意：SSE Endpoint需要通过MCP协议调用，而不是直接HTTP POST。
如果已经在Cursor中配置了MCP服务器，可以通过以下方式调用：
1. 通过AI助手环境调用MCP工具（推荐用于演示）
2. 使用MCP SDK（如果可用）
3. 通过MCP服务器代理调用

MCP配置示例（已在Cursor中配置）：
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
import requests
import json
from typing import List, Dict, Any
from models.schemas import SupplierInfo
from utils.config import Config

class MCPProxyService:
    """MCP工具代理服务"""
    
    @staticmethod
    def search_web(query: str, count: int = 5, use_qwen_agent: bool = True) -> List[SupplierInfo]:
        """
        通过MCP SSE Endpoint进行网络搜索
        
        注意：SSE Endpoint可能需要通过MCP协议调用，直接HTTP调用可能返回空响应。
        如果无法调用，可以考虑使用其他搜索API替代。
        
        Args:
            query: 搜索查询词
            count: 返回结果数量
            use_qwen_agent: 是否使用 qwen_agent 调用（如果可用）
            
        Returns:
            供应商信息列表
        """
        suppliers = []
        
        # 优先尝试使用 qwen_agent 调用
        if use_qwen_agent:
            try:
                from services.mcp_qwen_agent import QwenAgentMCPService
                qwen_service = QwenAgentMCPService()
                suppliers = qwen_service.search_web(query, count)
                if suppliers:
                    print(f"[MCP代理] 通过 qwen_agent 成功获取 {len(suppliers)} 个供应商")
                    return suppliers
            except ImportError:
                print("[MCP代理] qwen_agent 未安装，尝试直接HTTP调用")
            except Exception as e:
                print(f"[MCP代理] qwen_agent 调用失败: {e}，尝试直接HTTP调用")
        
        # 如果 qwen_agent 不可用，尝试直接HTTP调用
        try:
            api_key = Config.DASHSCOPE_API_KEY
            if not api_key:
                print("[MCP代理] 错误: DASHSCOPE_API_KEY未配置")
                return suppliers
            
            # MCP SSE Endpoint
            url = "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse"
            
            # 请求头 - 使用Bearer Token方式鉴权
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"  # SSE需要这个Accept头
            }
            
            # 请求体 - 根据MCP工具的参数格式
            payload = {
                "query": query,
                "count": count
            }
            
            print(f"[MCP代理] 正在搜索: {query}, 结果数: {count}")
            
            # 尝试非流式请求查看响应
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    stream=False,
                    timeout=30
                )
                
                if response.status_code == 200 and response.text:
                    # 如果非流式请求有响应，尝试解析
                    try:
                        response_json = response.json()
                        suppliers = MCPProxyService.parse_search_results([response_json])
                        if suppliers:
                            print(f"[MCP代理] 从非流式响应中解析到 {len(suppliers)} 个供应商")
                            return suppliers
                    except json.JSONDecodeError:
                        # 如果不是JSON，可能是SSE格式
                        pass
                
                # 如果非流式请求返回空，尝试流式请求
                if not response.text or response.status_code != 200:
                    print(f"[MCP代理] 非流式请求返回空或失败，尝试流式请求...")
                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        stream=True,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        suppliers = MCPProxyService._parse_sse_response(response)
                        if suppliers:
                            print(f"[MCP代理] 从流式响应中解析到 {len(suppliers)} 个供应商")
                            return suppliers
                
            except requests.exceptions.RequestException as e:
                print(f"[MCP代理] 请求异常: {e}")
            
            # 如果都失败了，返回空列表
            if not suppliers:
                print("[MCP代理] 警告: 无法从MCP SSE Endpoint获取响应")
                print("[MCP代理] 提示: SSE Endpoint可能需要通过MCP协议调用，而不是直接HTTP调用")
                print("[MCP代理] 建议: 1) 使用MCP SDK 2) 通过MCP服务器代理 3) 使用其他搜索API")
            
        except Exception as e:
            print(f"[MCP代理] 调用失败: {e}")
            import traceback
            traceback.print_exc()
        
        return suppliers
    
    @staticmethod
    def _parse_sse_response(response) -> List[SupplierInfo]:
        """解析SSE流式响应"""
        results = []
        buffer = ""
        
        for line in response.iter_lines():
            if line:
                try:
                    line_str = line.decode('utf-8')
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:].strip()
                        if data_str:
                            buffer += data_str
                            try:
                                data = json.loads(buffer)
                                results.append(data)
                                buffer = ""
                            except json.JSONDecodeError:
                                if buffer.endswith('}') or buffer.endswith(']'):
                                    try:
                                        data = json.loads(buffer)
                                        results.append(data)
                                        buffer = ""
                                    except:
                                        pass
                    elif line_str.strip() == '' and buffer:
                        try:
                            data = json.loads(buffer)
                            results.append(data)
                            buffer = ""
                        except:
                            buffer = ""
                except UnicodeDecodeError:
                    continue
        
        if buffer:
            try:
                data = json.loads(buffer)
                results.append(data)
            except:
                pass
        
        if results:
            return MCPProxyService.parse_search_results(results)
        return []
    
    @staticmethod
    def parse_search_results(results: List[Dict[str, Any]]) -> List[SupplierInfo]:
        """
        解析搜索结果并转换为SupplierInfo列表
        
        MCP WebSearch实际响应格式：
        {
          "isError": false,
          "content": [
            {
              "text": "{\"status\":0,\"pages\":[{\"snippet\":\"...\", ...}]}",
              "type": "text"
            }
          ]
        }
        
        Args:
            results: MCP工具返回的搜索结果
            
        Returns:
            供应商信息列表
        """
        suppliers = []
        all_pages = []
        
        for result in results:
            if isinstance(result, dict):
                # 检查是否是MCP标准响应格式
                if 'isError' in result and 'content' in result:
                    if result.get('isError'):
                        continue
                    
                    content = result.get('content', [])
                    if isinstance(content, list):
                        for content_item in content:
                            if isinstance(content_item, dict) and 'text' in content_item:
                                text_content = content_item.get('text', '')
                                try:
                                    # 解析text字段中的JSON字符串
                                    inner_json = json.loads(text_content)
                                    if isinstance(inner_json, dict) and 'pages' in inner_json:
                                        pages = inner_json.get('pages', [])
                                        if isinstance(pages, list):
                                            all_pages.extend(pages)
                                except json.JSONDecodeError:
                                    pass
                
                # 兼容其他格式
                elif 'pages' in result:
                    pages = result['pages']
                    if isinstance(pages, list):
                        all_pages.extend(pages)
                elif 'items' in result:
                    items = result['items']
                    if isinstance(items, list):
                        all_pages.extend(items)
                elif any(key in result for key in ['snippet', 'title', 'name']):
                    all_pages.append(result)
        
        # 解析每个页面
        for item in all_pages:
            try:
                snippet = item.get('snippet', '')
                title = (
                    item.get('title') or 
                    item.get('name') or 
                    item.get('heading') or 
                    ''
                )
                url = item.get('url') or item.get('link') or item.get('href')
                description = snippet or item.get('description', '')
                
                # 从snippet中提取标题
                if not title and snippet:
                    lines = snippet.split('\n')
                    if lines:
                        title = lines[0].strip()
                    if not title:
                        title = snippet[:50].strip()
                    if len(title) > 100:
                        title = title[:100] + '...'
                
                if not title:
                    continue
                
                supplier = SupplierInfo(
                    name=title,
                    source="web_search",
                    url=url,
                    description=description
                )
                suppliers.append(supplier)
            except Exception as e:
                print(f"[MCP代理] 解析项失败: {e}")
                continue
        
        return suppliers
