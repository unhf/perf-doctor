#!/usr/bin/env python3
"""
Chrome DevTools 连接测试 - 最简化版本
"""

import asyncio
import json
import subprocess
import time
import websockets
import requests
import psutil

class ChromeDebugTest:
    def __init__(self):
        self.chrome_process = None
        self.websocket = None
        self.debug_port = 9222

    def start_chrome(self):
        """启动Chrome"""
        try:
            # 关闭现有Chrome
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        proc.terminate()
                        proc.wait(timeout=3)
                except:
                    pass
            
            time.sleep(1)

            # 启动Chrome
            chrome_cmd = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                f'--remote-debugging-port={self.debug_port}',
                '--user-data-dir=/tmp/chrome-debug',  # 指定用户数据目录
                '--no-first-run',
                '--disable-extensions',
                '--disable-default-browser-check'
            ]
            
            print("启动Chrome...")
            self.chrome_process = subprocess.Popen(chrome_cmd)
            
            # 等待启动
            for i in range(10):
                try:
                    response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=2)
                    if response.status_code == 200:
                        print(f"Chrome启动成功")
                        return True
                except:
                    pass
                
                print(f"等待Chrome... ({i+1}/10)")
                time.sleep(1)
            
            return False
            
        except Exception as e:
            print(f"启动失败: {e}")
            return False

    async def basic_test(self):
        """基础连接测试"""
        try:
            # 获取targets
            response = requests.get(f'http://localhost:{self.debug_port}/json')
            targets = response.json()
            print(f"找到 {len(targets)} 个目标")
            
            if not targets:
                return False
            
            # 连接第一个目标
            target = targets[0]
            ws_url = target['webSocketDebuggerUrl']
            print(f"WebSocket URL: {ws_url}")
            
            self.websocket = await websockets.connect(ws_url)
            print("WebSocket连接成功!")
            
            # 测试简单命令
            print("测试Runtime.evaluate命令...")
            command = {
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "2 + 2",
                    "returnByValue": True
                }
            }
            
            await self.websocket.send(json.dumps(command))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
            result = json.loads(response)
            
            print(f"命令响应: {result}")
            
            if 'result' in result and 'result' in result['result'] and 'value' in result['result']['result']:
                print(f"计算结果: {result['result']['result']['value']}")
                return True
            
            return False
            
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def page_test(self, url):
        """页面测试"""
        try:
            print(f"导航到页面: {url}")
            
            # 启用Page域
            page_cmd = {"id": 2, "method": "Page.enable"}
            await self.websocket.send(json.dumps(page_cmd))
            await self.websocket.recv()
            print("Page域已启用")
            
            # 导航命令
            nav_cmd = {
                "id": 3,
                "method": "Page.navigate",
                "params": {"url": url}
            }
            
            await self.websocket.send(json.dumps(nav_cmd))
            nav_response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            print(f"导航响应: {json.loads(nav_response)}")
            
            # 等待一段时间让页面加载
            print("等待页面加载...")
            await asyncio.sleep(5)
            
            # 获取页面URL
            url_cmd = {
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "location.href",
                    "returnByValue": True
                }
            }
            
            await self.websocket.send(json.dumps(url_cmd))
            url_response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
            url_result = json.loads(url_response)
            
            if 'result' in url_result and 'result' in url_result['result'] and 'value' in url_result['result']['result']:
                current_url = url_result['result']['result']['value']
                print(f"当前页面URL: {current_url}")
                return True
            else:
                print(f"URL获取失败，响应: {url_result}")
            
            return False
            
        except Exception as e:
            print(f"页面测试失败: {e}")
            return False

    def cleanup(self):
        """清理"""
        if self.websocket:
            try:
                asyncio.create_task(self.websocket.close())
            except:
                pass
        
        if self.chrome_process:
            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=3)
                print("Chrome已关闭")
            except:
                pass

async def run_test():
    tester = ChromeDebugTest()
    
    try:
        print("=== Chrome DevTools连接测试 ===\n")
        
        # 启动Chrome
        if not tester.start_chrome():
            print("Chrome启动失败")
            return
        
        # 基础连接测试
        print("\n--- 基础连接测试 ---")
        if not await tester.basic_test():
            print("基础连接测试失败")
            return
        
        print("✅ 基础连接测试通过")
        
        # 页面导航测试
        print("\n--- 页面导航测试 ---")
        if await tester.page_test("https://www.baidu.com"):
            print("✅ 页面导航测试通过")
        else:
            print("❌ 页面导航测试失败")
        
    except Exception as e:
        print(f"测试过程出错: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    asyncio.run(run_test())
