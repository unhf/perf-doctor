#!/usr/bin/env python3
"""
Chrome DevTools通信模块
负责WebSocket连接和命令发送
"""

import asyncio
import json
import websockets


class DevToolsClient:
    """Chrome DevTools客户端"""
    
    def __init__(self):
        """初始化DevTools客户端"""
        self.websocket = None
        self.command_id = 1
    
    async def connect(self, websocket_url):
        """
        连接到Chrome DevTools WebSocket
        
        Args:
            websocket_url (str): WebSocket连接URL
            
        Returns:
            bool: True如果连接成功，False否则
        """
        try:
            self.websocket = await websockets.connect(websocket_url)
            print("WebSocket连接成功")
            return True
        except Exception as e:
            print(f"WebSocket连接失败: {e}")
            return False
    
    async def send_command(self, method, params=None, timeout=3):
        """
        发送DevTools命令
        
        Args:
            method (str): DevTools方法名
            params (dict): 命令参数，可选
            timeout (int): 超时时间（秒）
            
        Returns:
            dict: 命令响应，失败返回None
        """
        if not self.websocket:
            print("WebSocket未连接")
            return None
        
        # 构建命令
        command = {
            "id": self.command_id,
            "method": method,
            "params": params or {}
        }
        command_id = self.command_id
        self.command_id += 1
        
        try:
            # 发送命令
            await self.websocket.send(json.dumps(command))
            
            # 等待对应ID的响应（过滤事件消息）
            return await self._wait_for_response(command_id, timeout)
            
        except Exception as e:
            print(f"命令{method}执行失败: {e}")
            return None
    
    async def _wait_for_response(self, command_id, timeout, max_attempts=10):
        """
        等待特定命令的响应
        
        Args:
            command_id (int): 命令ID
            timeout (int): 单次接收超时时间
            max_attempts (int): 最大尝试次数
            
        Returns:
            dict: 命令响应，超时返回None
        """
        for _ in range(max_attempts):
            try:
                # 接收消息
                message = await asyncio.wait_for(
                    self.websocket.recv(), 
                    timeout=timeout
                )
                result = json.loads(message)
                
                # 检查是否是期待的命令响应
                if 'id' in result and result['id'] == command_id:
                    return result
                
                # 如果是事件通知，继续等待
                elif 'method' in result:
                    continue
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"接收响应时出错: {e}")
                break
        
        print(f"等待命令{command_id}响应超时")
        return None
    
    async def enable_domains(self, domains=None):
        """
        启用必要的DevTools域
        
        Args:
            domains (list): 要启用的域列表，默认为['Runtime', 'Page']
            
        Returns:
            bool: True如果全部启用成功，False否则
        """
        if domains is None:
            domains = ['Runtime', 'Page']
        
        success = True
        for domain in domains:
            response = await self.send_command(f'{domain}.enable')
            if response is None:
                print(f"启用{domain}域失败")
                success = False
            else:
                print(f"已启用{domain}域")
        
        return success
    
    async def evaluate_javascript(self, expression, return_by_value=True):
        """
        执行JavaScript代码
        
        Args:
            expression (str): JavaScript表达式
            return_by_value (bool): 是否按值返回结果
            
        Returns:
            dict: 执行结果，失败返回None
        """
        response = await self.send_command('Runtime.evaluate', {
            'expression': expression,
            'returnByValue': return_by_value
        })
        
        if response and 'result' in response:
            return response['result']
        return None
    
    async def navigate_to_page(self, url):
        """
        导航到指定页面
        
        Args:
            url (str): 目标URL
            
        Returns:
            bool: True如果导航成功，False否则
        """
        response = await self.send_command('Page.navigate', {'url': url})
        if response:
            print(f"导航到: {url}")
            return True
        else:
            print(f"导航失败: {url}")
            return False
    
    async def get_current_url(self):
        """
        获取当前页面URL
        
        Returns:
            str: 当前URL，失败返回空字符串
        """
        result = await self.evaluate_javascript('location.href')
        if result and 'result' in result and 'value' in result['result']:
            return result['result']['value']
        return ""
    
    async def wait_for_page_load(self, timeout=8):
        """
        等待页面加载完成
        
        Args:
            timeout (int): 等待时间（秒）
        """
        print("等待页面加载...")
        await asyncio.sleep(timeout)
    
    async def close(self):
        """关闭WebSocket连接"""
        if self.websocket:
            try:
                await self.websocket.close()
                print("WebSocket连接已关闭")
            except:
                pass
            self.websocket = None
