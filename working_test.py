#!/usr/bin/env python3
"""
工作版Chrome Performance Doctor
"""

import asyncio
import json
import subprocess
import time
import websockets
import requests
import psutil

class WorkingPerformanceDoctor:
    def __init__(self):
        self.chrome_process = None
        self.websocket = None
        self.debug_port = 9222
        self.command_id = 1

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
                '--user-data-dir=/tmp/chrome-debug',
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

    async def send_command(self, method, params=None):
        """发送DevTools命令"""
        if not self.websocket:
            return None
        
        command = {
            "id": self.command_id,
            "method": method,
            "params": params or {}
        }
        command_id = self.command_id
        self.command_id += 1
        
        try:
            await self.websocket.send(json.dumps(command))
            
            # 等待对应ID的响应
            for _ in range(10):
                response = await asyncio.wait_for(self.websocket.recv(), timeout=3)
                result = json.loads(response)
                
                # 如果是我们期待的命令响应
                if 'id' in result and result['id'] == command_id:
                    return result
                # 如果是事件通知，继续等待
                elif 'method' in result:
                    continue
                    
            print(f"等待 {method} 响应超时")
            return None
            
        except Exception as e:
            print(f"命令 {method} 失败: {e}")
            return None

    async def analyze_page(self, url):
        """分析页面性能"""
        try:
            # 获取targets
            response = requests.get(f'http://localhost:{self.debug_port}/json')
            targets = response.json()
            
            if not targets:
                print("未找到调试目标")
                return None
            
            # 连接第一个目标
            target = targets[0]
            ws_url = target['webSocketDebuggerUrl']
            
            self.websocket = await websockets.connect(ws_url)
            print("WebSocket连接成功")
            
            # 启用域
            await self.send_command('Runtime.enable')
            await self.send_command('Page.enable')
            print("已启用必要域")
            
            # 导航到页面
            print(f"导航到: {url}")
            await self.send_command('Page.navigate', {'url': url})
            
            # 等待页面加载
            print("等待页面加载...")
            await asyncio.sleep(8)
            
            # 获取页面信息
            print("获取页面信息...")
            page_info = await self.send_command('Runtime.evaluate', {
                'expression': 'JSON.stringify({href: location.href, title: document.title})',
                'returnByValue': True
            })
            
            if page_info and 'result' in page_info:
                info = json.loads(page_info['result']['result']['value'])
                print(f"页面标题: {info.get('title', 'Unknown')}")
                print(f"页面URL: {info.get('href', 'Unknown')}")
            
            # 获取性能数据
            print("获取性能数据...")
            perf_response = await self.send_command('Runtime.evaluate', {
                'expression': '''
                JSON.stringify({
                    loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                    domReady: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
                    ttfb: performance.timing.responseStart - performance.timing.navigationStart,
                    dns: performance.timing.domainLookupEnd - performance.timing.domainLookupStart,
                    tcp: performance.timing.connectEnd - performance.timing.connectStart,
                    paint: performance.getEntriesByType('paint').map(p => ({name: p.name, time: p.startTime})),
                    memory: performance.memory || {},
                    href: location.href,
                    title: document.title
                })
                ''',
                'returnByValue': True
            })
            
            if perf_response and 'result' in perf_response:
                return json.loads(perf_response['result']['result']['value'])
            
            return None
            
        except Exception as e:
            print(f"分析失败: {e}")
            return None

    def generate_report(self, data):
        """生成性能报告"""
        if not data:
            return "无法生成报告 - 没有性能数据"
        
        report = f"""
=== Chrome页面性能报告 ===
页面: {data.get('title', 'Unknown')}
URL: {data.get('href', 'Unknown')}
测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

=== 核心性能指标 ===
页面加载时间: {data.get('loadTime', 0):.0f}ms
DOM就绪时间: {data.get('domReady', 0):.0f}ms
首字节时间(TTFB): {data.get('ttfb', 0):.0f}ms
DNS查询时间: {data.get('dns', 0):.0f}ms
TCP连接时间: {data.get('tcp', 0):.0f}ms
"""
        
        # 添加Paint Timing
        paint_data = data.get('paint', [])
        for paint in paint_data:
            report += f"{paint['name']}: {paint['time']:.0f}ms\n"
        
        # 添加内存信息
        memory = data.get('memory', {})
        if memory and memory.get('usedJSHeapSize'):
            report += f"JS堆内存使用: {memory['usedJSHeapSize'] / 1024 / 1024:.1f}MB\n"
        
        # 性能评估
        load_time = data.get('loadTime', 0)
        report += "\n=== 性能评估 ===\n"
        if load_time < 1000:
            report += "✅ 页面加载速度: 优秀 (< 1秒)\n"
        elif load_time < 3000:
            report += "⚠️  页面加载速度: 良好 (1-3秒)\n"
        else:
            report += "❌ 页面加载速度: 需要优化 (> 3秒)\n"
        
        ttfb = data.get('ttfb', 0)
        if ttfb < 200:
            report += "✅ 首字节时间: 优秀 (< 200ms)\n"
        elif ttfb < 500:
            report += "⚠️  首字节时间: 良好 (200-500ms)\n"
        else:
            report += "❌ 首字节时间: 需要优化 (> 500ms)\n"
        
        return report

    def cleanup(self):
        """清理资源"""
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

async def test_page_performance(url):
    """测试页面性能"""
    doctor = WorkingPerformanceDoctor()
    
    try:
        print(f"=== 开始分析页面性能 ===")
        print(f"目标URL: {url}")
        print("=" * 40)
        
        # 启动Chrome
        if not doctor.start_chrome():
            print("Chrome启动失败")
            return
        
        # 分析页面
        perf_data = await doctor.analyze_page(url)
        
        if perf_data:
            # 生成报告
            report = doctor.generate_report(perf_data)
            print(report)
            
            # 保存报告
            filename = f"performance_report_{int(time.time())}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n✅ 报告已保存到: {filename}")
        else:
            print("❌ 性能分析失败")
            
    except Exception as e:
        print(f"测试过程出错: {e}")
    finally:
        doctor.cleanup()

if __name__ == "__main__":
    # 可以修改这里的URL来测试不同的网站
    test_urls = [
        "https://www.baidu.com",
        # "https://www.google.com",
        # "https://www.github.com"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        asyncio.run(test_page_performance(url))
        if len(test_urls) > 1:
            print("等待5秒后测试下一个...")
            time.sleep(5)
