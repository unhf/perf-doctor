import asyncio
import json
import subprocess
import time
import websockets
import requests
import psutil
import sys
import os
import shutil
from urllib.parse import urlparse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *


class ChromePerformanceDoctor:
    def __init__(self):
        self.chrome_process = None
        self.websocket = None
        self.debug_port = CHROME_DEBUG_PORT
        self.performance_data = {}

    def start_chrome_with_debugging(self):
        """启动Chrome浏览器并开启调试端口"""
        try:
            # 先尝试连接现有的调试端口
            try:
                response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=2)
                if response.status_code == 200:
                    print(f"Chrome调试端口 {self.debug_port} 已在运行")
                    return True
            except:
                pass

            # 关闭所有现有的Chrome进程以避免冲突
            print("正在关闭现有的Chrome进程...")
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        proc.terminate()
                        proc.wait(timeout=3)
                except:
                    pass
            
            # 稍等片刻确保进程完全关闭
            time.sleep(2)

            # 启动Chrome浏览器
            chrome_cmd = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                f'--remote-debugging-port={self.debug_port}',
                '--new-instance',  # 强制创建新实例
                '--user-data-dir=/tmp/chrome-debug-session'  # 使用临时用户数据目录
            ] + CHROME_ARGS
            
            print(f"正在启动Chrome，调试端口: {self.debug_port}")
            self.chrome_process = subprocess.Popen(chrome_cmd, 
                                                 stdout=subprocess.DEVNULL, 
                                                 stderr=subprocess.DEVNULL)
            
            # 等待Chrome启动完成，并验证调试端口是否可用
            max_retries = 10
            for i in range(max_retries):
                try:
                    response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=2)
                    if response.status_code == 200:
                        print(f"Chrome调试端口启动成功: {self.debug_port}")
                        return True
                except:
                    pass
                
                print(f"等待Chrome启动... ({i+1}/{max_retries})")
                time.sleep(1)
            
            print("Chrome启动超时，调试端口未响应")
            return False
            
        except Exception as e:
            print(f"启动Chrome失败: {e}")
            return False

    async def get_debug_targets(self):
        """获取可用的调试目标"""
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json')
            targets = response.json()
            return targets
        except Exception as e:
            print(f"获取调试目标失败: {e}")
            return []

    async def connect_to_target(self, websocket_url):
        """连接到指定的WebSocket目标"""
        try:
            self.websocket = await websockets.connect(websocket_url)
            print(f"已连接到Chrome DevTools: {websocket_url}")
            return True
        except Exception as e:
            print(f"连接WebSocket失败: {e}")
            return False

    async def send_command(self, method, params=None):
        """发送命令到Chrome DevTools"""
        if not self.websocket:
            return None
            
        command = {
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {}
        }
        
        await self.websocket.send(json.dumps(command))
        response = await self.websocket.recv()
        return json.loads(response)

    async def enable_domains(self):
        """启用必要的Chrome DevTools域"""
        domains = ['Runtime', 'Performance', 'Network', 'Page']
        
        for domain in domains:
            response = await self.send_command(f'{domain}.enable')
            print(f"已启用 {domain} 域")

    async def start_performance_monitoring(self):
        """开始性能监控"""
        # 开始性能跟踪
        await self.send_command('Performance.enable')
        await self.send_command('Performance.startPreciseCoverage', {
            'callCount': True,
            'detailed': True
        })
        
        # 开始网络监控
        await self.send_command('Network.enable')
        
        print("性能监控已开始")

    async def navigate_to_page(self, url):
        """导航到指定页面"""
        response = await self.send_command('Page.navigate', {'url': url})
        print(f"正在导航到: {url}")
        
        # 等待页面加载事件
        start_time = time.time()
        timeout = 15  # 15秒超时
        
        while time.time() - start_time < timeout:
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                event = json.loads(message)
                
                # 检查页面加载完成事件
                if event.get('method') == 'Page.loadEventFired':
                    print("页面加载完成")
                    break
                elif event.get('method') == 'Page.domContentEventFired':
                    print("DOM内容加载完成")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"等待页面加载事件时出错: {e}")
                break
        
        # 额外等待确保所有资源加载完成
        await asyncio.sleep(3)
        return response

    async def collect_performance_metrics(self):
        """收集性能指标"""
        print("正在收集性能指标...")
        
        # 获取性能指标
        metrics_response = await self.send_command('Performance.getMetrics')
        
        # 获取运行时性能 - 使用更详细的脚本
        runtime_script = '''
        (function() {
            try {
                const timing = performance.timing;
                const navigation = performance.navigation;
                const memory = performance.memory || {};
                
                // 获取Paint Timing
                const paintEntries = performance.getEntriesByType('paint') || [];
                const paintTiming = {};
                paintEntries.forEach(entry => {
                    paintTiming[entry.name] = entry.startTime;
                });
                
                // 获取Navigation Timing
                const navTiming = performance.getEntriesByType('navigation')[0] || {};
                
                // 获取Resource Timing (前10个资源)
                const resourceTiming = performance.getEntriesByType('resource').slice(0, 10);
                
                // 计算核心Web Vitals
                const result = {
                    timing: {
                        navigationStart: timing.navigationStart,
                        loadEventEnd: timing.loadEventEnd,
                        domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                        responseStart: timing.responseStart,
                        domainLookupStart: timing.domainLookupStart,
                        domainLookupEnd: timing.domainLookupEnd,
                        connectStart: timing.connectStart,
                        connectEnd: timing.connectEnd,
                        requestStart: timing.requestStart,
                        responseEnd: timing.responseEnd,
                        domLoading: timing.domLoading,
                        domInteractive: timing.domInteractive,
                        domComplete: timing.domComplete
                    },
                    navigation: navigation,
                    memory: memory,
                    paintTiming: paintTiming,
                    navigationTiming: navTiming,
                    resourceTiming: resourceTiming,
                    currentTime: Date.now(),
                    href: window.location.href
                };
                
                return JSON.stringify(result);
            } catch (error) {
                return JSON.stringify({error: error.message});
            }
        })()
        '''
        
        runtime_response = await self.send_command('Runtime.evaluate', {
            'expression': runtime_script,
            'returnByValue': True
        })
        
        print("性能指标收集完成")
        
        return {
            'devtools_metrics': metrics_response,
            'performance_api': runtime_response
        }

    def parse_performance_data(self, data):
        """解析和整理性能数据"""
        performance_report = {
            'timestamp': time.time(),
            'summary': {},
            'detailed_metrics': {}
        }
        
        # 解析DevTools指标
        if 'devtools_metrics' in data and 'result' in data['devtools_metrics']:
            metrics = data['devtools_metrics']['result'].get('metrics', [])
            for metric in metrics:
                performance_report['detailed_metrics'][metric['name']] = metric['value']
        
        # 解析Performance API数据
        if 'performance_api' in data and 'result' in data['performance_api']:
            try:
                # 处理不同的响应格式
                result = data['performance_api']['result']
                if 'value' in result:
                    if isinstance(result['value'], str):
                        perf_data = json.loads(result['value'])
                    else:
                        perf_data = result['value']
                else:
                    perf_data = result
                
                # 检查是否有错误
                if 'error' in perf_data:
                    print(f"性能数据收集错误: {perf_data['error']}")
                    return performance_report
                
                # 计算关键性能指标
                timing = perf_data.get('timing', {})
                if timing and timing.get('navigationStart'):
                    nav_start = timing['navigationStart']
                    
                    performance_report['summary'] = {
                        'page_load_time': (timing.get('loadEventEnd', 0) - nav_start) if timing.get('loadEventEnd') else 0,
                        'dom_ready_time': (timing.get('domContentLoadedEventEnd', 0) - nav_start) if timing.get('domContentLoadedEventEnd') else 0,
                        'first_byte_time': (timing.get('responseStart', 0) - nav_start) if timing.get('responseStart') else 0,
                        'dns_lookup_time': (timing.get('domainLookupEnd', 0) - timing.get('domainLookupStart', 0)) if timing.get('domainLookupEnd') and timing.get('domainLookupStart') else 0,
                        'tcp_connect_time': (timing.get('connectEnd', 0) - timing.get('connectStart', 0)) if timing.get('connectEnd') and timing.get('connectStart') else 0,
                        'request_response_time': (timing.get('responseEnd', 0) - timing.get('requestStart', 0)) if timing.get('responseEnd') and timing.get('requestStart') else 0,
                        'dom_processing_time': (timing.get('domComplete', 0) - timing.get('domLoading', 0)) if timing.get('domComplete') and timing.get('domLoading') else 0
                    }
                
                # 添加Paint Timing指标
                paint_timing = perf_data.get('paintTiming', {})
                for paint_name, paint_time in paint_timing.items():
                    performance_report['summary'][f"{paint_name.replace('-', '_')}_time"] = paint_time
                
                # 添加内存信息
                memory = perf_data.get('memory', {})
                if memory:
                    performance_report['summary']['memory_used'] = memory.get('usedJSHeapSize', 0)
                    performance_report['summary']['memory_total'] = memory.get('totalJSHeapSize', 0)
                    performance_report['summary']['memory_limit'] = memory.get('jsHeapSizeLimit', 0)
                
                # 添加页面信息
                performance_report['page_info'] = {
                    'url': perf_data.get('href', 'Unknown'),
                    'collection_time': perf_data.get('currentTime', 0)
                }
                
            except Exception as e:
                print(f"解析性能数据失败: {e}")
                print(f"原始数据: {data.get('performance_api', {})}")
        
        return performance_report

    def generate_performance_report(self, performance_data):
        """生成性能评估报告"""
        report = f"""
=== Chrome页面性能评估报告 ===
生成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(performance_data['timestamp']))}
测试页面: {performance_data.get('page_info', {}).get('url', 'Unknown')}

=== 核心性能指标 ===
"""
        
        summary = performance_data.get('summary', {})
        if summary:
            # 时间相关指标
            if summary.get('page_load_time'):
                report += f"页面加载时间: {summary['page_load_time']:.0f}ms\n"
            if summary.get('dom_ready_time'):
                report += f"DOM就绪时间: {summary['dom_ready_time']:.0f}ms\n"
            if summary.get('first_byte_time'):
                report += f"首字节时间(TTFB): {summary['first_byte_time']:.0f}ms\n"
            if summary.get('dns_lookup_time'):
                report += f"DNS查询时间: {summary['dns_lookup_time']:.0f}ms\n"
            if summary.get('tcp_connect_time'):
                report += f"TCP连接时间: {summary['tcp_connect_time']:.0f}ms\n"
            if summary.get('request_response_time'):
                report += f"请求响应时间: {summary['request_response_time']:.0f}ms\n"
            if summary.get('dom_processing_time'):
                report += f"DOM处理时间: {summary['dom_processing_time']:.0f}ms\n"
            
            # Paint Timing指标
            if summary.get('first_paint_time'):
                report += f"首次绘制时间(FP): {summary['first_paint_time']:.0f}ms\n"
            if summary.get('first_contentful_paint_time'):
                report += f"首次内容绘制时间(FCP): {summary['first_contentful_paint_time']:.0f}ms\n"
            
            # 内存使用情况
            if summary.get('memory_used'):
                report += f"JavaScript堆内存使用: {summary['memory_used'] / 1024 / 1024:.2f}MB\n"
                if summary.get('memory_total'):
                    report += f"JavaScript堆内存总计: {summary['memory_total'] / 1024 / 1024:.2f}MB\n"
                if summary.get('memory_limit'):
                    report += f"JavaScript堆内存限制: {summary['memory_limit'] / 1024 / 1024:.2f}MB\n"
        
        report += "\n=== 性能评估 ===\n"
        
        # 性能评估逻辑
        page_load_time = summary.get('page_load_time', 0)
        if page_load_time > 0:
            thresholds = PERFORMANCE_THRESHOLDS['page_load_time']
            if page_load_time < thresholds['excellent']:
                report += f"✅ 页面加载速度: 优秀 ({page_load_time:.0f}ms < {thresholds['excellent']}ms)\n"
            elif page_load_time < thresholds['good']:
                report += f"⚠️  页面加载速度: 良好 ({page_load_time:.0f}ms)\n"
            else:
                report += f"❌ 页面加载速度: 需要优化 ({page_load_time:.0f}ms > {thresholds['good']}ms)\n"
        
        first_paint = summary.get('first_paint_time', 0)
        if first_paint > 0:
            paint_thresholds = PERFORMANCE_THRESHOLDS['first_paint_time']
            if first_paint < paint_thresholds['excellent']:
                report += f"✅ 首次绘制时间: 优秀 ({first_paint:.0f}ms)\n"
            elif first_paint < paint_thresholds['good']:
                report += f"⚠️  首次绘制时间: 良好 ({first_paint:.0f}ms)\n"
            else:
                report += f"❌ 首次绘制时间: 需要优化 ({first_paint:.0f}ms)\n"
        
        fcp_time = summary.get('first_contentful_paint_time', 0)
        if fcp_time > 0:
            fcp_thresholds = PERFORMANCE_THRESHOLDS['first_contentful_paint']
            if fcp_time < fcp_thresholds['excellent']:
                report += f"✅ 首次内容绘制: 优秀 ({fcp_time:.0f}ms)\n"
            elif fcp_time < fcp_thresholds['good']:
                report += f"⚠️  首次内容绘制: 良好 ({fcp_time:.0f}ms)\n"
            else:
                report += f"❌ 首次内容绘制: 需要优化 ({fcp_time:.0f}ms)\n"
        
        # TTFB评估
        ttfb = summary.get('first_byte_time', 0)
        if ttfb > 0:
            if ttfb < 200:
                report += f"✅ 首字节时间: 优秀 ({ttfb:.0f}ms)\n"
            elif ttfb < 500:
                report += f"⚠️  首字节时间: 良好 ({ttfb:.0f}ms)\n"
            else:
                report += f"❌ 首字节时间: 需要优化 ({ttfb:.0f}ms)\n"
        
        # 内存使用评估
        memory_used = summary.get('memory_used', 0)
        if memory_used > 0:
            memory_mb = memory_used / 1024 / 1024
            if memory_mb < 10:
                report += f"✅ 内存使用: 优秀 ({memory_mb:.1f}MB)\n"
            elif memory_mb < 50:
                report += f"⚠️  内存使用: 良好 ({memory_mb:.1f}MB)\n"
            else:
                report += f"❌ 内存使用: 需要关注 ({memory_mb:.1f}MB)\n"
        
        # 如果没有收集到关键数据，给出提示
        if not summary or not any([summary.get('page_load_time'), summary.get('first_paint_time')]):
            report += "\n⚠️  注意: 部分性能数据收集失败，可能是由于:\n"
            report += "   - 页面加载过快或过慢\n"
            report += "   - 网络连接问题\n"
            report += "   - 页面JavaScript执行限制\n"
            report += "   建议重试或检查目标网站\n"
        
        return report

    async def analyze_page_performance(self, url):
        """分析指定页面的性能"""
        print(f"开始分析页面性能: {url}")
        
        # 启动Chrome
        if not self.start_chrome_with_debugging():
            return None
        
        try:
            # 获取调试目标
            targets = await self.get_debug_targets()
            if not targets:
                print("未找到可用的调试目标")
                return None
            
            # 连接到第一个可用目标
            target = targets[0]
            websocket_url = target['webSocketDebuggerUrl']
            
            if not await self.connect_to_target(websocket_url):
                return None
            
            # 启用必要的域
            await self.enable_domains()
            
            # 开始性能监控
            await self.start_performance_monitoring()
            
            # 导航到目标页面
            await self.navigate_to_page(url)
            
            # 收集性能数据
            performance_data = await self.collect_performance_metrics()
            
            # 解析性能数据
            parsed_data = self.parse_performance_data(performance_data)
            
            # 生成报告
            report = self.generate_performance_report(parsed_data)
            
            return report
            
        except Exception as e:
            print(f"性能分析过程中出现错误: {e}")
            return None
        
        finally:
            # 清理资源
            if self.websocket:
                await self.websocket.close()

    def cleanup(self):
        """清理资源"""
        if self.chrome_process:
            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=5)
                print("Chrome进程已终止")
            except:
                try:
                    self.chrome_process.kill()
                    print("Chrome进程已强制终止")
                except:
                    pass
        
        # 清理临时用户数据目录
        import shutil
        temp_dir = '/tmp/chrome-debug-session'
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print("临时数据目录已清理")
            except:
                pass


async def main():
    """主函数"""
    doctor = ChromePerformanceDoctor()
    
    try:
        # 从配置文件获取要测试的URL
        test_urls = TEST_URLS if TEST_URLS else ["https://www.baidu.com"]
        
        for url in test_urls:
            print(f"\n{'='*50}")
            print(f"正在分析页面: {url}")
            print(f"{'='*50}")
            
            report = await doctor.analyze_page_performance(url)
            
            if report:
                print(report)
                
                # 根据配置保存报告到文件
                if REPORT_CONFIG['save_to_file']:
                    filename = f"{url.replace('https://', '').replace('http://', '').replace('/', '_')}_{REPORT_CONFIG['file_name']}"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report)
                    print(f"\n报告已保存到 {filename}")
            else:
                print(f"页面 {url} 性能分析失败")
            
            # 在多个URL之间稍作停顿
            if len(test_urls) > 1:
                await asyncio.sleep(2)
                
    except KeyboardInterrupt:
        print("\n分析被用户中断")
    except Exception as e:
        print(f"运行出错: {e}")
    finally:
        doctor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
