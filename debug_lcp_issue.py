#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LCP问题调试脚本

专门用于排查LCP为0的问题，添加详细的日志输出
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.chrome_manager import ChromeManager
from modules.devtools_client import DevToolsClient
from modules.performance_collector import PerformanceCollector
from modules.report_generator import ReportGenerator

def setup_debug_logging():
    """设置调试日志"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('lcp_debug.log', encoding='utf-8')
        ]
    )

async def wait_for_page_load(devtools_client, timeout=30):
    """等待页面完全加载"""
    logger = logging.getLogger(__name__)
    logger.info("等待页面完全加载...")
    
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        try:
            # 检查页面readyState
            ready_state = await devtools_client.execute_javascript("document.readyState")
            logger.info(f"页面readyState: {ready_state}")
            
            if ready_state == "complete":
                logger.info("页面加载完成")
                return True
            
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"检查页面状态失败: {e}")
            await asyncio.sleep(1)
    
    logger.warning("页面加载超时")
    return False

async def test_lcp_collection(url: str, wait_time: int = 10):
    """测试LCP采集"""
    logger = logging.getLogger(__name__)
    logger.info(f"开始测试LCP采集: {url}")
    
    # 创建Chrome管理器
    chrome_manager = ChromeManager(
        chrome_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        debug_port=9222,
        inherit_cookies=True
    )
    
    try:
        # 启动Chrome
        logger.info("启动Chrome...")
        if not chrome_manager.start_chrome():
            logger.error("Chrome启动失败")
            return None
        
        # 新建tab并导航到目标页面
        logger.info("新建tab并导航到目标页面...")
        tab_info = chrome_manager.create_new_tab(url)
        if not tab_info or 'webSocketDebuggerUrl' not in tab_info:
            logger.error("无法获取新tab的webSocketDebuggerUrl")
            return None
        
        devtools_client = DevToolsClient(tab_info['webSocketDebuggerUrl'])
        if not await devtools_client.connect():
            logger.error("DevTools连接失败")
            return None
        
        # 启动事件监听
        logger.info("启动DevTools事件监听...")
        event_task = asyncio.create_task(devtools_client.listen_for_events())
        
        # 等待页面加载
        if not await wait_for_page_load(devtools_client, timeout=30):
            logger.warning("页面加载超时，继续执行...")
        
        # 额外等待确保页面渲染完成
        logger.info(f"额外等待 {wait_time} 秒确保页面渲染...")
        await asyncio.sleep(wait_time)
        
        # 创建性能收集器
        logger.info("创建性能收集器...")
        performance_collector = PerformanceCollector(devtools_client)
        
        # 获取收集器状态
        collector_status = performance_collector.get_collector_status()
        logger.info(f"收集器状态: {json.dumps(collector_status, indent=2, ensure_ascii=False)}")
        
        # PaintCollector重试
        logger.info("开始测试PaintCollector...")
        paint_collector = performance_collector.collector_manager.get_collector("PaintCollector")
        if paint_collector:
            logger.info("PaintCollector存在，开始设置...")
            setup_success = False
            for _ in range(3):
                try:
                    setup_success = await paint_collector.setup()
                    if setup_success:
                        break
                except Exception as e:
                    logger.error(f"PaintCollector设置异常: {e}")
                await asyncio.sleep(1)
            logger.info(f"PaintCollector设置结果: {setup_success}")
            
            if setup_success:
                # 收集PaintCollector数据
                logger.info("开始收集PaintCollector数据...")
                paint_data = await paint_collector.collect()
                logger.info(f"PaintCollector原始数据: {json.dumps(paint_data, indent=2, ensure_ascii=False)}")
                
                # 检查LCP数据
                if "data" in paint_data:
                    lcp_value = paint_data["data"].get("largest-contentful-paint")
                    logger.info(f"LCP值: {lcp_value} (类型: {type(lcp_value)})")
                    
                    if lcp_value is None or lcp_value == 0:
                        logger.warning("LCP值为空或0，尝试手动获取...")
                        await test_manual_lcp(devtools_client)
                else:
                    logger.error("PaintCollector数据格式异常")
        
        # 测试完整的性能数据收集
        logger.info("开始完整性能数据收集...")
        performance_data = await performance_collector.collect_performance_data(url, wait_time)
        
        # 打印完整的性能数据
        logger.info("完整性能数据结构:")
        logger.info(json.dumps(performance_data, indent=2, ensure_ascii=False))
        
        # 测试报告生成
        logger.info("开始生成报告...")
        report_generator = ReportGenerator()
        report = report_generator.generate_report(performance_data)
        
        # 检查报告中的LCP
        key_metrics = report.get("key_metrics", {})
        lcp_in_report = key_metrics.get("lcp", 0)
        logger.info(f"报告中的LCP值: {lcp_in_report}")
        
        # 保存调试报告
        debug_report = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "wait_time": wait_time,
            "paint_collector_data": paint_data if 'paint_data' in locals() else None,
            "performance_data": performance_data,
            "report_lcp": lcp_in_report,
            "key_metrics": key_metrics
        }
        
        with open('lcp_debug_report.json', 'w', encoding='utf-8') as f:
            json.dump(debug_report, f, indent=2, ensure_ascii=False)
        
        logger.info("调试报告已保存到 lcp_debug_report.json")
        
        return {
            "paint_data": paint_data if 'paint_data' in locals() else None,
            "performance_data": performance_data,
            "report": report,
            "lcp_value": lcp_in_report
        }
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return None
    finally:
        # 清理资源
        logger.info("清理资源...")
        if 'event_task' in locals():
            event_task.cancel()
        if 'devtools_client' in locals():
            try:
                await devtools_client.disconnect()
            except Exception as e:
                logger.warning(f"关闭DevToolsClient异常: {e}")
        if 'chrome_manager' in locals():
            chrome_manager.cleanup()

async def test_manual_lcp(devtools_client):
    """手动测试LCP获取"""
    logger = logging.getLogger(__name__)
    
    try:
        # 方法1: 使用Performance API（简化版本）
        logger.info("方法1: 使用Performance API获取LCP...")
        perf_script = """
        (function() {
            try {
                const entries = performance.getEntriesByType('largest-contentful-paint');
                return entries.length > 0 ? entries[entries.length - 1].startTime : null;
            } catch (e) {
                return null;
            }
        })();
        """
        lcp_perf = await devtools_client.execute_javascript(perf_script)
        logger.info(f"Performance API LCP: {lcp_perf}")
        
        # 方法2: 使用PerformanceObserver（简化版本）
        logger.info("方法2: 使用PerformanceObserver获取LCP...")
        observer_script = """
        (function() {
            return new Promise((resolve) => {
                try {
                    const observer = new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        const lastEntry = entries[entries.length - 1];
                        resolve(lastEntry ? lastEntry.startTime : null);
                    });
                    observer.observe({entryTypes: ['largest-contentful-paint']});
                    
                    // 立即检查是否已有数据
                    const existingEntries = performance.getEntriesByType('largest-contentful-paint');
                    if (existingEntries.length > 0) {
                        resolve(existingEntries[existingEntries.length - 1].startTime);
                    } else {
                        // 等待500ms
                        setTimeout(() => resolve(null), 500);
                    }
                } catch (e) {
                    resolve(null);
                }
            });
        })();
        """
        lcp_observer = await devtools_client.execute_javascript(observer_script)
        logger.info(f"PerformanceObserver LCP: {lcp_observer}")
        
        # 方法3: 检查页面是否支持LCP
        logger.info("方法3: 检查页面LCP支持情况...")
        support_script = """
        (function() {
            try {
                return {
                    hasPerformanceObserver: typeof PerformanceObserver !== 'undefined',
                    hasLargestContentfulPaint: PerformanceObserver && 'largest-contentful-paint' in PerformanceObserver.supportedEntryTypes,
                    paintEntries: performance.getEntriesByType('paint').length,
                    lcpEntries: performance.getEntriesByType('largest-contentful-paint').length,
                    navigationEntries: performance.getEntriesByType('navigation').length
                };
            } catch (e) {
                return {error: e.message};
            }
        })();
        """
        support_info = await devtools_client.execute_javascript(support_script)
        logger.info(f"LCP支持信息: {json.dumps(support_info, indent=2, ensure_ascii=False)}")
        
        # 方法4: 获取页面基本信息
        logger.info("方法4: 获取页面基本信息...")
        page_info_script = """
        (function() {
            try {
                return {
                    url: window.location.href,
                    title: document.title,
                    readyState: document.readyState,
                    bodyChildren: document.body ? document.body.children.length : 0,
                    images: document.images.length,
                    scripts: document.scripts.length,
                    stylesheets: document.styleSheets.length
                };
            } catch (e) {
                return {error: e.message};
            }
        })();
        """
        page_info = await devtools_client.execute_javascript(page_info_script)
        logger.info(f"页面信息: {json.dumps(page_info, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"手动LCP测试失败: {e}")

async def main():
    """主函数"""
    setup_debug_logging()
    logger = logging.getLogger(__name__)
    
    # 测试URL列表
    test_urls = [
        "https://www.github.com",  # 复杂页面，有图片和内容
        "https://www.baidu.com",   # 中文页面，有丰富内容
        "https://example.com"      # 简单页面作为对比
    ]
    
    for url in test_urls:
        logger.info(f"\n{'='*60}")
        logger.info(f"测试URL: {url}")
        logger.info(f"{'='*60}")
        
        result = await test_lcp_collection(url, wait_time=10)
        
        if result:
            lcp_value = result["lcp_value"]
            if lcp_value and lcp_value > 0:
                logger.info(f"✅ LCP采集成功: {lcp_value}ms")
            else:
                logger.warning(f"⚠️ LCP采集失败或为0: {lcp_value}")
        else:
            logger.error(f"❌ 测试失败")
        
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main()) 