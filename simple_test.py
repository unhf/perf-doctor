#!/usr/bin/env python3
"""
简化版Chrome Performance Doctor - 用于快速测试和调试
"""

import asyncio
import json
import subproce            # 导航命令
            print(f"导航到: {url}")
            nav_response = await self.send_command('Page.navigate', {'url': url})
            
            # 等待页面加载完成
            print("等待页面加载...")
            await asyncio.sleep(8)  # 固定等待时间
            
            # 验证是否导航成功
            current_url_response = await self.send_command('Runtime.evaluate', {
                'expression': 'location.href',
                'returnByValue': True
            })
            
            if current_url_response and 'result' in current_url_response and 'result' in current_url_response['result']:
                current_url = current_url_response['result']['result']['value']
                print(f"当前页面URL: {current_url}")
                
                # 如果没有正确导航，再次尝试
                if url not in current_url:
                    print("页面导航可能失败，重新尝试...")
                    await self.send_command('Page.navigate', {'url': url})
                    await asyncio.sleep(5)
            
            # 获取性能数据
            print("获取性能数据...")
            perf_data = await self.get_performance_data()
            
            return perf_datae
import websockets
import requests
import psutil
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SimplePerformanceDoctor:
    def __init__(self):
        self.chrome_process = None
        self.websocket = None
        self.debug_port = 9222
        self.command_id = 1  # 简单的命令ID计数器

    def start_chrome(self):
        """启动Chrome浏览器"""
        try:
            # 检查是否已有Chrome调试实例
            try:
                response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=2)
                if response.status_code == 200:
                    print(f"Chrome调试端口 {self.debug_port} 已在运行")
                    return True
            except:
                pass

            # 关闭现有Chrome进程
            print("正在关闭现有Chrome进程...")
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        proc.terminate()
                        proc.wait(timeout=3)
                except:
                    pass
            
            time.sleep(2)

            # 启动新的Chrome实例
            chrome_cmd = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                f'--remote-debugging-port={self.debug_port}',
                '--user-data-dir=/tmp/chrome-perf-test',  # 添加用户数据目录
                '--disable-gpu',
                '--no-sandbox',
                '--disable-extensions',
                '--disable-background-timer-throttling',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--disable-default-browser-check'
            ]
            
            print(f"启动Chrome (界面模式)...")
            self.chrome_process = subprocess.Popen(
                chrome_cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            # 等待Chrome启动
            for i in range(15):
                try:
                    response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=2)
                    if response.status_code == 200:
                        print(f"Chrome启动成功 (尝试 {i+1}/15)")
                        return True
                except:
                    pass
                
                print(f"等待Chrome启动... ({i+1}/15)")
                time.sleep(1)
            
            print("Chrome启动失败")
            return False
            
        except Exception as e:
            print(f"启动Chrome时出错: {e}")
            return False

    async def connect_and_test(self, url):
        """连接Chrome并测试页面"""
        try:
            # 获取调试目标
            response = requests.get(f'http://localhost:{self.debug_port}/json')
            targets = response.json()
            
            if not targets:
                print("未找到调试目标")
                return None
            
            # 连接到第一个目标
            target = targets[0]
            websocket_url = target['webSocketDebuggerUrl']
            print(f"连接到: {websocket_url}")
            
            self.websocket = await websockets.connect(websocket_url)
            print("WebSocket连接成功")
            
            # 启用必要的域
            await self.send_command('Runtime.enable')
            await self.send_command('Page.enable')
            print("已启用必要域")
            
            # 导航到页面 - 使用简单方式
            print(f"导航到: {url}")
            nav_response = await self.send_command('Page.navigate', {'url': url})
            
            # 等待页面加载完成
            print("等待页面加载...")
            await asyncio.sleep(8)  # 固定等待时间
            
            # 验证是否导航成功
            current_url_response = await self.send_command('Runtime.evaluate', {
                'expression': 'location.href',
                'returnByValue': True
            })
            
            if current_url_response and 'result' in current_url_response and 'result' in current_url_response['result']:
                current_url = current_url_response['result']['result']['value']
                print(f"当前页面URL: {current_url}")
                
                # 如果没有正确导航，再次尝试
                if url not in current_url:
                    print("页面导航可能失败，重新尝试...")
                    await self.send_command('Page.navigate', {'url': url})
                    await asyncio.sleep(5)
            
            # 获取性能数据
            print("获取性能数据...")
            perf_data = await self.get_performance_data()
            
            return perf_data
            
        except Exception as e:
            print(f"连接测试失败: {e}")
            return None

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
            for _ in range(20):  # 最多尝试20次
                response = await asyncio.wait_for(self.websocket.recv(), timeout=2)
                result = json.loads(response)
                
                # 如果是我们期待的命令响应
                if 'id' in result and result['id'] == command_id:
                    print(f"[DEBUG] {method} 成功响应")
                    return result
                # 如果是事件通知，继续等待
                elif 'method' in result:
                    print(f"[DEBUG] 收到事件: {result['method']}")
                    continue
                    
            print(f"等待 {method} 响应超时")
            return None
            
        except asyncio.TimeoutError:
            print(f"命令超时: {method}")
            return None
        except Exception as e:
            print(f"发送命令失败: {method}, 错误: {e}")
            return None

    async def get_performance_data(self):
        """获取性能数据"""
        try:
            # 执行JavaScript获取性能数据 - 分步骤获取
            print("正在获取页面基本信息...")
            basic_script = '''
            JSON.stringify({
                href: location.href,
                title: document.title,
                readyState: document.readyState,
                timestamp: Date.now()
            })
            '''
            
            basic_response = await self.send_command('Runtime.evaluate', {
                'expression': basic_script,
                'returnByValue': True
            })
            
            if not basic_response or 'result' not in basic_response:
                print("无法获取基本页面信息")
                return None
            
            basic_data = json.loads(basic_response['result']['result']['value'])
            print(f"页面标题: {basic_data.get('title', 'Unknown')}")
            print(f"页面状态: {basic_data.get('readyState', 'Unknown')}")
            
            # 获取性能计时数据
            print("正在获取性能计时数据...")
            timing_script = '''
            (function() {
                try {
                    var timing = performance.timing;
                    var nav = timing.navigationStart;
                    return JSON.stringify({
                        navigationStart: timing.navigationStart,
                        loadEventEnd: timing.loadEventEnd,
                        domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                        responseStart: timing.responseStart,
                        domainLookupStart: timing.domainLookupStart,
                        domainLookupEnd: timing.domainLookupEnd,
                        connectStart: timing.connectStart,
                        connectEnd: timing.connectEnd,
                        loadTime: timing.loadEventEnd > 0 ? timing.loadEventEnd - nav : 0,
                        domReady: timing.domContentLoadedEventEnd > 0 ? timing.domContentLoadedEventEnd - nav : 0,
                        ttfb: timing.responseStart > 0 ? timing.responseStart - nav : 0,
                        dns: timing.domainLookupEnd > 0 && timing.domainLookupStart > 0 ? timing.domainLookupEnd - timing.domainLookupStart : 0,
                        tcp: timing.connectEnd > 0 && timing.connectStart > 0 ? timing.connectEnd - timing.connectStart : 0
                    });
                } catch(e) {
                    return JSON.stringify({error: e.message});
                }
            })()
            '''
            
            timing_response = await self.send_command('Runtime.evaluate', {
                'expression': timing_script,
                'returnByValue': True
            })
            
            timing_data = {}
            if timing_response and 'result' in timing_response and 'result' in timing_response['result'] and 'value' in timing_response['result']['result']:
                timing_data = json.loads(timing_response['result']['result']['value'])
                if 'error' in timing_data:
                    print(f"获取计时数据出错: {timing_data['error']}")
                else:
                    print("计时数据获取成功")
            
            # 获取内存和Paint数据
            print("正在获取内存和Paint数据...")
            extra_script = '''
            (function() {
                try {
                    var result = {
                        memory: performance.memory || {},
                        paint: []
                    };
                    
                    // 获取Paint Timing
                    if (performance.getEntriesByType) {
                        var paints = performance.getEntriesByType('paint');
                        result.paint = paints.map(function(p) {
                            return {name: p.name, time: p.startTime};
                        });
                    }
                    
                    return JSON.stringify(result);
                } catch(e) {
                    return JSON.stringify({error: e.message});
                }
            })()
            '''
            
            extra_response = await self.send_command('Runtime.evaluate', {
                'expression': extra_script,
                'returnByValue': True
            })
            
            extra_data = {}
            if extra_response and 'result' in extra_response and 'result' in extra_response['result'] and 'value' in extra_response['result']['result']:
                extra_data = json.loads(extra_response['result']['result']['value'])
                if 'error' in extra_data:
                    print(f"获取额外数据出错: {extra_data['error']}")
                else:
                    print("额外数据获取成功")
            
            # 合并所有数据
            result = {**basic_data, **timing_data, **extra_data}
            
            print(f"性能数据收集完成，包含 {len(result)} 个字段")
            return result
                
        except Exception as e:
            print(f"获取性能数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_report(self, data):
        """生成简单的性能报告"""
        if not data:
            return "无法生成报告 - 没有性能数据"
        
        report = f"""
=== 页面性能报告 ===
页面: {data.get('title', 'Unknown')}
URL: {data.get('href', 'Unknown')}
测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

=== 关键指标 ===
页面加载时间: {data.get('loadTime', 0):.0f}ms
DOM就绪时间: {data.get('domReady', 0):.0f}ms
首字节时间: {data.get('ttfb', 0):.0f}ms
DNS查询时间: {data.get('dns', 0):.0f}ms
TCP连接时间: {data.get('tcp', 0):.0f}ms
"""
        
        # 添加Paint Timing
        paint_data = data.get('paint', [])
        for paint in paint_data:
            report += f"{paint['name']}: {paint['time']:.0f}ms\n"
        
        # 添加内存信息
        memory = data.get('memory', {})
        if memory:
            report += f"JS堆内存: {memory.get('usedJSHeapSize', 0) / 1024 / 1024:.1f}MB\n"
        
        # 简单评估
        load_time = data.get('loadTime', 0)
        report += "\n=== 性能评估 ===\n"
        if load_time < 1000:
            report += "✅ 加载速度: 优秀\n"
        elif load_time < 3000:
            report += "⚠️  加载速度: 良好\n"
        else:
            report += "❌ 加载速度: 需要优化\n"
        
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
                print("Chrome进程已终止")
            except:
                try:
                    self.chrome_process.kill()
                except:
                    pass
        
        # 清理临时目录
        import shutil
        temp_dir = '/tmp/chrome-perf-test'
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

async def test_single_page(url):
    """测试单个页面"""
    doctor = SimplePerformanceDoctor()
    
    try:
        print(f"开始测试: {url}")
        
        # 启动Chrome
        if not doctor.start_chrome():
            print("Chrome启动失败")
            return
        
        # 连接并测试
        perf_data = await doctor.connect_and_test(url)
        
        if perf_data:
            report = doctor.generate_report(perf_data)
            print(report)
            
            # 保存报告
            filename = f"simple_report_{int(time.time())}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n报告已保存到: {filename}")
        else:
            print("测试失败")
            
    except Exception as e:
        print(f"测试过程出错: {e}")
    finally:
        doctor.cleanup()

if __name__ == "__main__":
    # 测试URL
    test_url = "https://www.baidu.com"
    
    print("=== 简化版Chrome性能测试 ===")
    print(f"测试URL: {test_url}")
    print("=" * 40)
    
    asyncio.run(test_single_page(test_url))
