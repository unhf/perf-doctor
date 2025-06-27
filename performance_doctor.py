#!/usr/bin/env python3
"""
性能分析器主模块
整合所有功能模块，提供简洁的API
"""

import asyncio
import time
from chrome_manager import ChromeManager
from devtools_client import DevToolsClient
from performance_collector import PerformanceCollector
from report_generator import ReportGenerator


class PerformanceDoctor:
    """
    网页性能分析器
    
    这是主要的类，整合了Chrome管理、DevTools通信、
    性能数据收集和报告生成等功能。
    """
    
    def __init__(self, debug_port=9222):
        """
        初始化性能分析器
        
        Args:
            debug_port (int): Chrome调试端口，默认9222
        """
        self.chrome_manager = ChromeManager(debug_port)
        self.devtools_client = DevToolsClient()
        self.performance_collector = PerformanceCollector(self.devtools_client)
    
    async def analyze_page(self, url, create_new_tab=True):
        """
        分析指定页面的性能
        
        Args:
            url (str): 要分析的页面URL
            create_new_tab (bool): 是否创建新标签页进行测试
            
        Returns:
            dict: 性能分析结果，失败返回None
        """
        print(f"开始分析页面: {url}")
        
        try:
            # 1. 连接或启动Chrome
            if not self.chrome_manager.connect_or_start():
                print("Chrome连接失败")
                return None
            
            # 2. 获取或创建标签页
            target_tab = await self._get_target_tab(url, create_new_tab)
            if not target_tab:
                print("无法获取目标标签页")
                return None
            
            # 3. 建立WebSocket连接
            ws_url = target_tab['webSocketDebuggerUrl']
            if not await self.devtools_client.connect(ws_url):
                return None
            
            # 4. 启用必要的DevTools域
            if not await self.devtools_client.enable_domains():
                return None
            
            # 5. 导航到目标页面
            if not await self._navigate_to_target(url):
                return None
            
            # 6. 等待页面加载完成
            await self.devtools_client.wait_for_page_load()
            
            # 7. 收集性能数据
            performance_data = await self.performance_collector.collect_all_data()
            
            if performance_data:
                print("✅ 性能数据收集完成")
                return performance_data
            else:
                print("❌ 性能数据收集失败")
                return None
                
        except Exception as e:
            print(f"分析过程出错: {e}")
            return None
    
    async def _get_target_tab(self, url, create_new_tab):
        """
        获取目标标签页
        
        Args:
            url (str): 目标URL
            create_new_tab (bool): 是否创建新标签页
            
        Returns:
            dict: 标签页信息，失败返回None
        """
        tabs = self.chrome_manager.get_tabs()
        if not tabs:
            print("未找到可用的标签页")
            return None
        
        print(f"发现 {len(tabs)} 个标签页")
        
        if create_new_tab:
            # 创建新标签页
            new_tab = self.chrome_manager.create_new_tab(url)
            if new_tab:
                # 稍等一下让新标签页初始化
                await asyncio.sleep(2)
                
                # 重新获取标签页列表，找到新创建的标签页
                updated_tabs = self.chrome_manager.get_tabs()
                for tab in updated_tabs:
                    if tab.get('id') == new_tab.get('id'):
                        print(f"使用新创建的标签页: {tab.get('title', 'Unknown')}")
                        return tab
            
            print("创建新标签页失败，使用现有标签页")
        
        # 使用第一个可用的标签页
        target_tab = tabs[0]
        print(f"使用现有标签页: {target_tab.get('title', 'Unknown')}")
        return target_tab
    
    async def _navigate_to_target(self, url):
        """
        导航到目标页面
        
        Args:
            url (str): 目标URL
            
        Returns:
            bool: True如果导航成功，False否则
        """
        # 检查当前URL
        current_url = await self.devtools_client.get_current_url()
        
        if url in current_url:
            print(f"页面已经是目标URL: {current_url}")
            return True
        
        # 导航到新页面
        return await self.devtools_client.navigate_to_page(url)
    
    def generate_report(self, performance_data):
        """
        生成性能报告
        
        Args:
            performance_data (dict): 性能数据
            
        Returns:
            str: 格式化的报告内容
        """
        return ReportGenerator.generate_report(performance_data)
    
    def save_report(self, report_content, filename=None):
        """
        保存报告到文件
        
        Args:
            report_content (str): 报告内容
            filename (str): 文件名，可选
            
        Returns:
            str: 保存的文件名
        """
        return ReportGenerator.save_report(report_content, filename)
    
    async def cleanup(self):
        """清理所有资源"""
        await self.devtools_client.close()
        self.chrome_manager.cleanup()


# 便捷函数
async def analyze_page_performance(url, save_report=True, create_new_tab=True):
    """
    便捷函数：分析单个页面性能
    
    Args:
        url (str): 要分析的页面URL
        save_report (bool): 是否保存报告到文件
        create_new_tab (bool): 是否创建新标签页
        
    Returns:
        tuple: (performance_data, report_content)
    """
    doctor = PerformanceDoctor()
    
    try:
        print(f"=== 页面性能分析 ===")
        print(f"目标URL: {url}")
        print("=" * 50)
        
        # 分析页面性能
        perf_data = await doctor.analyze_page(url, create_new_tab)
        
        if perf_data:
            # 生成报告
            report = doctor.generate_report(perf_data)
            print(report)
            
            # 保存报告
            if save_report:
                doctor.save_report(report)
            
            return perf_data, report
        else:
            print("❌ 性能分析失败")
            return None, None
            
    except Exception as e:
        print(f"分析过程出错: {e}")
        return None, None
    finally:
        await doctor.cleanup()


async def analyze_multiple_pages(urls, save_reports=True):
    """
    便捷函数：分析多个页面性能
    
    Args:
        urls (list): URL列表
        save_reports (bool): 是否保存报告到文件
        
    Returns:
        dict: {url: (performance_data, report_content)}
    """
    results = {}
    
    for i, url in enumerate(urls):
        print(f"\n{'='*60}")
        print(f"分析进度: {i+1}/{len(urls)}")
        
        perf_data, report = await analyze_page_performance(
            url, save_reports, create_new_tab=True
        )
        
        results[url] = (perf_data, report)
        
        # 在多个URL之间稍作停顿
        if i < len(urls) - 1:
            print("等待3秒后继续下一个...")
            await asyncio.sleep(3)
    
    return results


if __name__ == "__main__":
    # 示例使用
    test_urls = [
        "https://www.baidu.com",
        # "https://www.google.com",
        # "https://www.github.com"
    ]
    
    # 分析单个页面
    if len(test_urls) == 1:
        asyncio.run(analyze_page_performance(test_urls[0]))
    else:
        # 分析多个页面
        asyncio.run(analyze_multiple_pages(test_urls))
