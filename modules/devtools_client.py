"""
DevTools WebSocket 客户端模块

负责与 Chrome DevTools 建立 WebSocket 连接，发送命令并接收响应
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional, Callable, Set
from urllib.parse import urlparse

class DevToolsClient:
    """Chrome DevTools WebSocket 客户端"""
    
    def __init__(self, websocket_url: str):
        """
        初始化 DevTools 客户端
        
        Args:
            websocket_url: DevTools WebSocket URL
        """
        self.websocket_url = websocket_url
        self.websocket = None
        self.command_id = 0
        self.pending_commands = {}  # 等待响应的命令
        self.event_handlers = {}    # 事件处理器
        self.logger = logging.getLogger(__name__)
        self.enabled_domains = set()  # 已启用的域
    
    async def connect(self) -> bool:
        """
        建立 WebSocket 连接
        
        Returns:
            True 如果连接成功
        """
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.logger.info(f"连接到 DevTools: {self.websocket_url}")
            return True
        except Exception as e:
            self.logger.error(f"连接 DevTools 失败: {e}")
            return False
    
    async def disconnect(self):
        """断开 WebSocket 连接"""
        if self.websocket:
            await self.websocket.close()
            self.logger.info("断开 DevTools 连接")
    
    def _get_next_command_id(self) -> int:
        """获取下一个命令ID"""
        self.command_id += 1
        return self.command_id
    
    async def send_command(self, method: str, params: Dict[str, Any] = None, 
                          timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        发送命令到 DevTools
        
        Args:
            method: 命令方法名
            params: 命令参数
            timeout: 超时时间（秒）
            
        Returns:
            命令响应，失败时返回 None
        """
        if not self.websocket:
            self.logger.error("WebSocket 未连接")
            return None
        
        command_id = self._get_next_command_id()
        command = {
            "id": command_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            # 创建 Future 用于等待响应
            future = asyncio.get_event_loop().create_future()
            self.pending_commands[command_id] = future
            
            # 发送命令
            await self.websocket.send(json.dumps(command))
            self.logger.debug(f"发送命令: {method} (ID: {command_id})")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(future, timeout=timeout)
                return response
            except asyncio.TimeoutError:
                self.logger.error(f"命令超时: {method} (ID: {command_id})")
                return None
            finally:
                # 清理等待队列
                self.pending_commands.pop(command_id, None)
                
        except Exception as e:
            self.logger.error(f"发送命令失败: {method}, 错误: {e}")
            self.pending_commands.pop(command_id, None)
            return None
    
    def add_event_handler(self, event_name: str, handler: Callable[[Dict], None]):
        """
        添加事件处理器
        
        Args:
            event_name: 事件名称
            handler: 事件处理函数
        """
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
        self.logger.debug(f"添加事件处理器: {event_name}")
    
    async def listen_for_events(self):
        """监听 DevTools 事件（在后台运行）"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    # 处理命令响应
                    if "id" in data:
                        command_id = data["id"]
                        if command_id in self.pending_commands:
                            future = self.pending_commands[command_id]
                            if not future.done():
                                if "error" in data:
                                    future.set_exception(Exception(data["error"]))
                                else:
                                    future.set_result(data.get("result", {}))
                    
                    # 处理事件
                    elif "method" in data:
                        method = data["method"]
                        params = data.get("params", {})
                        
                        if method in self.event_handlers:
                            for handler in self.event_handlers[method]:
                                try:
                                    handler(params)
                                except Exception as e:
                                    self.logger.error(f"事件处理器错误 {method}: {e}")
                        
                        self.logger.debug(f"收到事件: {method}")
                
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析消息失败: {e}")
                except Exception as e:
                    self.logger.error(f"处理消息失败: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket 连接已关闭")
        except Exception as e:
            self.logger.error(f"监听事件失败: {e}")
    
    async def enable_domain(self, domain: str) -> bool:
        """
        启用 DevTools 域
        
        Args:
            domain: 域名（如 'Performance', 'Page' 等）
            
        Returns:
            True 如果成功启用
        """
        if domain in self.enabled_domains:
            return True
        
        response = await self.send_command(f"{domain}.enable")
        if response is not None:
            self.enabled_domains.add(domain)
            self.logger.info(f"启用域: {domain}")
            return True
        else:
            self.logger.error(f"启用域失败: {domain}")
            return False
    
    async def navigate_to(self, url: str) -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            
        Returns:
            True 如果导航成功
        """
        response = await self.send_command("Page.navigate", {"url": url})
        if response and "frameId" in response:
            self.logger.info(f"导航到: {url}")
            return True
        else:
            self.logger.error(f"导航失败: {url}")
            return False
    
    async def execute_javascript(self, expression: str) -> Any:
        """
        执行 JavaScript 代码
        
        Args:
            expression: JavaScript 表达式
            
        Returns:
            执行结果
        """
        response = await self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True
        }, timeout=30.0)  # 增加超时时间到30秒
        
        if response and "result" in response:
            result = response["result"]
            if "value" in result:
                return result["value"]
            elif "description" in result:
                return result["description"]
        
        self.logger.error(f"JavaScript 执行失败: {expression}")
        return None
