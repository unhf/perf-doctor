"""
DevTools客户端模块

与Chrome DevTools建立WebSocket连接并通信
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional, Callable, Set

from .commands import DevToolsCommands
from .events import DevToolsEvents, DevToolsEvent, EventNames
from ...core.exceptions import DevToolsException, TimeoutException


class DevToolsClient:
    """Chrome DevTools WebSocket客户端"""
    
    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.websocket = None
        self.command_id = 0
        self.pending_commands: Dict[int, asyncio.Future] = {}
        self.events = DevToolsEvents()
        self.logger = logging.getLogger(__name__)
        self.enabled_domains: Set[str] = set()
        self._page_loaded = None  # 新增: 用于等待页面加载
    
    async def connect(self) -> bool:
        """建立WebSocket连接"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.logger.info(f"连接到DevTools: {self.websocket_url}")
            
            # 启动事件监听协程
            asyncio.create_task(self.listen_for_events())
            
            # 启用Page域
            await self.enable_domain("Page")
            
            return True
        except Exception as e:
            self.logger.error(f"连接DevTools失败: {e}")
            raise DevToolsException(f"连接DevTools失败: {e}")
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.websocket:
            await self.websocket.close()
            self.logger.info("断开DevTools连接")
    
    def _get_next_command_id(self) -> int:
        """获取下一个命令ID"""
        self.command_id += 1
        return self.command_id
    
    async def send_command(self, method: str, params: Dict[str, Any] = None, 
                          timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """发送命令到DevTools"""
        if not self.websocket:
            raise DevToolsException("WebSocket未连接")
        
        command_id = self._get_next_command_id()
        command = {
            "id": command_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            future = asyncio.get_event_loop().create_future()
            self.pending_commands[command_id] = future
            
            await self.websocket.send(json.dumps(command))
            self.logger.debug(f"发送命令: {method} (ID: {command_id})")
            
            try:
                response = await asyncio.wait_for(future, timeout=timeout)
                return response
            except asyncio.TimeoutError:
                raise TimeoutException(f"命令超时: {method} (ID: {command_id})")
            finally:
                self.pending_commands.pop(command_id, None)
                
        except Exception as e:
            self.pending_commands.pop(command_id, None)
            raise DevToolsException(f"发送命令失败: {method}, 错误: {e}")
    
    def add_event_handler(self, event_name: str, handler: Callable[[Dict[str, Any]], None]):
        """添加事件处理器"""
        self.events.add_handler(event_name, handler)
    
    async def listen_for_events(self):
        """监听DevTools事件"""
        if not self.websocket:
            self.logger.error("WebSocket未连接，无法监听事件")
            return
        
        self.logger.info("开始监听DevTools事件")
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.logger.debug(f"收到消息: {data}")
                    
                    # 处理命令响应
                    if "id" in data:
                        command_id = data["id"]
                        if command_id in self.pending_commands:
                            future = self.pending_commands[command_id]
                            if not future.done():
                                if "error" in data:
                                    self.logger.error(f"命令执行失败 (ID: {command_id}): {data['error']}")
                                    future.set_exception(Exception(data["error"]))
                                else:
                                    self.logger.debug(f"命令执行成功 (ID: {command_id})")
                                    future.set_result(data.get("result", {}))
                    
                    # 处理事件
                    elif "method" in data:
                        event = DevToolsEvent(
                            method=data["method"],
                            params=data.get("params", {})
                        )
                        self.logger.debug(f"处理事件: {data['method']}")
                        self.events.handle_event(event)
                
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析消息失败: {e}, 消息: {message}")
                except Exception as e:
                    self.logger.error(f"处理消息失败: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket连接已关闭")
        except Exception as e:
            self.logger.error(f"监听事件失败: {e}")
    
    async def enable_domain(self, domain: str) -> bool:
        """启用DevTools域"""
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
    
    async def navigate_to(self, url: str, timeout: float = 30.0) -> bool:
        """导航到指定URL，并等待页面加载完成"""
        try:
            # 创建页面加载完成的Future
            self._page_loaded = asyncio.get_event_loop().create_future()
            
            # 定义页面加载事件处理器
            def on_load_event(event):
                self.logger.info("收到Page.loadEventFired事件")
                if not self._page_loaded.done():
                    self._page_loaded.set_result(True)
            
            # 添加事件处理器
            self.add_event_handler("Page.loadEventFired", on_load_event)
            self.logger.info("已注册Page.loadEventFired事件处理器")
            
            # 发送导航命令
            self.logger.info(f"开始导航到: {url}")
            response = await self.send_command("Page.navigate", {"url": url}, timeout=timeout)
            
            if not response or "frameId" not in response:
                self.logger.error(f"导航命令失败: {url}")
                return False
            
            self.logger.info(f"导航命令成功，等待页面加载: {url}")
            
            # 等待页面加载事件
            try:
                await asyncio.wait_for(self._page_loaded, timeout=timeout)
                self.logger.info(f"页面加载完成: {url}")
                return True
            except asyncio.TimeoutError:
                self.logger.error(f"页面加载超时: {url}")
                return False
                
        except Exception as e:
            self.logger.error(f"导航过程异常: {e}")
            return False
    
    async def execute_javascript(self, expression: str) -> Any:
        """执行JavaScript代码"""
        response = await self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True
        }, timeout=30.0)
        
        if response and "result" in response:
            result = response["result"]
            if "value" in result:
                return result["value"]
            elif "description" in result:
                return result["description"]
        
        self.logger.error(f"JavaScript执行失败: {expression}")
        return None
    
    async def get_metrics(self) -> Optional[Dict[str, Any]]:
        """获取性能指标"""
        try:
            response = await self.send_command("Performance.getMetrics")
            if response and "metrics" in response:
                return response["metrics"]
            return None
        except Exception as e:
            self.logger.error(f"获取性能指标失败: {e}")
            return None 