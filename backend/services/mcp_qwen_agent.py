"""
使用 qwen_agent 调用 MCP WebSearch 工具

参考 qwen_agent 的 Assistant 类来调用 MCP 服务器
"""
import os
from typing import List, Optional
from qwen_agent.agents import Assistant
from models.schemas import SupplierInfo
from utils.config import Config

class QwenAgentMCPService:
    """使用 qwen_agent 调用 MCP WebSearch 的服务"""
    
    def __init__(self):
        """初始化 qwen_agent Assistant"""
        # LLM 配置
        self.llm_cfg = {
            "model": "qwen-plus-latest",
            "model_server": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": Config.DASHSCOPE_API_KEY,
        }
        
        # MCP 服务器配置 - 参考用户提供的格式
        # qwen_agent 的 function_list 应该是一个包含 mcpServers 配置的字典列表
        self.mcp_tools = [
            {
                "mcpServers": {
                    "bailian-web-search": {
                        "type": "sse",
                        "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
                        "headers": {
                            "Authorization": f"Bearer {Config.DASHSCOPE_API_KEY}"
                        }
                    }
                }
            }
        ]
        
        # 创建助手实例
        # 注意：由于 anyio 版本冲突，可能需要特殊处理
        self.bot = None
        try:
            self.bot = Assistant(
                llm=self.llm_cfg,
                name="WebSearch助手",
                description="网络搜索助手，可以搜索供应商信息",
                system_message="你是一个专业的网络搜索助手，可以帮助用户搜索供应商信息。",
                function_list=self.mcp_tools,
            )
            print("[QwenAgent MCP] 助手初始化成功")
        except Exception as e:
            print(f"[QwenAgent MCP] 初始化失败: {e}")
            print("[QwenAgent MCP] 可能是 anyio 版本冲突导致的")
            print("[QwenAgent MCP] 建议: 1) 升级 anyio: pip install 'anyio>=4.5'")
            print("[QwenAgent MCP] 建议: 2) 或使用 Cursor AI 助手调用 MCP 工具")
            self.bot = None
    
    def search_web(self, query: str, count: int = 5) -> List[SupplierInfo]:
        """
        使用 qwen_agent 调用 MCP WebSearch 工具进行搜索
        
        Args:
            query: 搜索查询词
            count: 返回结果数量
            
        Returns:
            供应商信息列表
        """
        suppliers = []
        
        if self.bot is None:
            print("[QwenAgent MCP] 助手未初始化，无法调用")
            return suppliers
        
        try:
            # 构建搜索请求 - 明确指定使用 MCP 工具
            search_query = f"请使用 bailian_web_search 工具搜索 '{query}'，返回 {count} 个结果"
            
            print(f"[QwenAgent MCP] 正在搜索: {query}, 结果数: {count}")
            
            messages = [
                {"role": "user", "content": search_query}
            ]
            
            # 运行助手并获取响应
            response_data = None
            tool_call_info = None
            all_responses = []
            
            print(f"[QwenAgent MCP] 开始调用助手...")
            for response_chunk in self.bot.run(messages):
                new_response = response_chunk[-1]
                all_responses.append(new_response)
                
                if "function_call" in new_response:
                    tool_call_info = new_response["function_call"]
                    print(f"[QwenAgent MCP] 检测到工具调用: {tool_call_info.get('name', 'unknown')}")
                
                elif "function_call" not in new_response and tool_call_info:
                    # 工具调用完成，获取结果
                    response_data = new_response
                    print(f"[QwenAgent MCP] 工具调用完成，获取结果")
                    # 不立即break，继续收集所有响应
                
                elif new_response.get("role") == "assistant" and "content" in new_response:
                    # 普通响应内容
                    content = new_response.get("content", "")
                    if content:
                        print(f"[QwenAgent MCP] 助手响应: {content[:100]}...")
            
            # 从所有响应中提取数据
            print(f"[QwenAgent MCP] 共收到 {len(all_responses)} 个响应块")
            
            # 打印所有响应以便调试
            print(f"[QwenAgent MCP] 调试：打印响应结构...")
            for i, resp in enumerate(all_responses[:5]):  # 只打印前5个
                print(f"[QwenAgent MCP] 响应 {i+1} 类型: {type(resp)}")
                print(f"[QwenAgent MCP] 响应 {i+1} 键: {list(resp.keys()) if isinstance(resp, dict) else 'N/A'}")
                if isinstance(resp, dict):
                    # 打印部分内容
                    for key in ['function_call', 'content', 'role']:
                        if key in resp:
                            value = resp[key]
                            if isinstance(value, dict):
                                print(f"[QwenAgent MCP]   {key}: {list(value.keys())}")
                            elif isinstance(value, str):
                                print(f"[QwenAgent MCP]   {key}: {value[:100]}...")
                            else:
                                print(f"[QwenAgent MCP]   {key}: {type(value)}")
            
            # 尝试从所有响应中解析
            for resp in all_responses:
                parsed = self._parse_response(resp, query)
                if parsed:
                    print(f"[QwenAgent MCP] 从响应中解析到 {len(parsed)} 个供应商")
                    suppliers.extend(parsed)
            
            # 去重并过滤无效结果
            seen_names = set()
            unique_suppliers = []
            invalid_names = {"WebSearch助手", "助手", "你是一个专业的网络搜索助手", "网络搜索助手"}
            
            for s in suppliers:
                # 过滤无效名称
                if s.name in invalid_names or len(s.name.strip()) < 3:
                    continue
                # 去重
                if s.name not in seen_names:
                    seen_names.add(s.name)
                    unique_suppliers.append(s)
            
            suppliers = unique_suppliers[:count]  # 限制数量
            
            print(f"[QwenAgent MCP] 最终解析结果: {len(suppliers)} 个供应商")
            
        except ImportError:
            print("[QwenAgent MCP] 错误: qwen_agent 库未安装")
            print("[QwenAgent MCP] 请运行: pip install qwen-agent")
        except Exception as e:
            print(f"[QwenAgent MCP] 调用失败: {e}")
            import traceback
            traceback.print_exc()
        
        return suppliers
    
    def _parse_response(self, response_data: dict, query: str) -> List[SupplierInfo]:
        """
        解析 qwen_agent 返回的响应数据
        
        Args:
            response_data: qwen_agent 返回的响应数据
            query: 原始查询词
            
        Returns:
            供应商信息列表
        """
        suppliers = []
        
        try:
            # qwen_agent 返回的数据格式可能不同
            # 需要根据实际返回格式解析
            
            # 如果响应中包含 function_call 的结果
            if "function_call" in response_data:
                function_call = response_data.get("function_call", {})
                print(f"[QwenAgent MCP] 找到 function_call: {list(function_call.keys())}")
                
                # 检查不同的结果字段
                result = function_call.get("result") or function_call.get("content") or function_call.get("data")
                if result:
                    print(f"[QwenAgent MCP] 找到结果数据: {type(result)}")
                    # 使用已有的解析逻辑
                    from services.mcp_proxy import MCPProxyService
                    if isinstance(result, dict):
                        suppliers = MCPProxyService.parse_search_results([result])
                    elif isinstance(result, list):
                        suppliers = MCPProxyService.parse_search_results(result)
                    elif isinstance(result, str):
                        # 尝试解析JSON字符串
                        import json
                        try:
                            result_json = json.loads(result)
                            suppliers = MCPProxyService.parse_search_results([result_json] if isinstance(result_json, dict) else result_json)
                        except json.JSONDecodeError:
                            pass
            
            # 如果响应中包含 content，尝试解析
            if not suppliers and "content" in response_data:
                content = response_data.get("content", "")
                print(f"[QwenAgent MCP] 找到 content: {type(content)}")
                # 尝试从 content 中提取 JSON
                import json
                try:
                    # 如果 content 是 JSON 字符串
                    if isinstance(content, str):
                        # 跳过明显的系统消息或助手名称
                        if content in ["WebSearch助手", "助手", "你是一个专业的网络搜索助手"]:
                            return suppliers
                        
                        if content.strip().startswith("{"):
                            content_json = json.loads(content)
                            from services.mcp_proxy import MCPProxyService
                            suppliers = MCPProxyService.parse_search_results([content_json] if isinstance(content_json, dict) else content_json)
                        # 尝试从文本中提取JSON（可能包含在文本中）
                        elif "{" in content and "}" in content:
                            # 尝试提取JSON部分
                            start = content.find("{")
                            end = content.rfind("}") + 1
                            if start >= 0 and end > start:
                                json_str = content[start:end]
                                try:
                                    content_json = json.loads(json_str)
                                    from services.mcp_proxy import MCPProxyService
                                    suppliers = MCPProxyService.parse_search_results([content_json] if isinstance(content_json, dict) else content_json)
                                except json.JSONDecodeError:
                                    pass
                    elif isinstance(content, dict):
                        from services.mcp_proxy import MCPProxyService
                        suppliers = MCPProxyService.parse_search_results([content])
                except json.JSONDecodeError as e:
                    print(f"[QwenAgent MCP] JSON解析失败: {e}")
            
            # 如果响应本身就是 MCP 格式
            if not suppliers and isinstance(response_data, dict):
                if "isError" in response_data or "content" in response_data:
                    from services.mcp_proxy import MCPProxyService
                    suppliers = MCPProxyService.parse_search_results([response_data])
                # 或者直接包含搜索结果字段
                elif any(key in response_data for key in ['pages', 'items', 'results']):
                    from services.mcp_proxy import MCPProxyService
                    suppliers = MCPProxyService.parse_search_results([response_data])
            
        except Exception as e:
            print(f"[QwenAgent MCP] 解析响应失败: {e}")
            import traceback
            traceback.print_exc()
        
        return suppliers

