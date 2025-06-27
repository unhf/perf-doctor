#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能医生主入口

重构后的主程序入口
"""

import asyncio
import logging
import sys
import os
import argparse
from typing import Optional

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core import Config, PerfDoctorException
from src.infrastructure import ChromeManager, DevToolsClient
from src.collectors import CollectorManager
from src.collectors.performance import (
    PaintCollector, NavigationCollector, MemoryCollector, PerformanceMetricsCollector
)
from src.collectors.network import NetworkCollector
from src.services.performance_service import PerformanceService
from src.services.report_service import ReportService


def setup_logging(level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="性能医生 - 网页性能分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s https://example.com                    # 分析单个页面
  %(prog)s --debug https://example.com            # 调试模式
  %(prog)s --wait-time 20 https://example.com     # 自定义等待时间
        """
    )
    
    parser.add_argument(
        'url',
        help='要分析的URL'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--wait-time',
        type=int,
        default=None,  # 使用配置文件中的默认值
        help='页面加载等待时间(秒) (默认: 10秒)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='无头模式运行Chrome'
    )
    
    return parser.parse_args()


async def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 设置日志
        log_level = "DEBUG" if args.debug else "INFO"
        setup_logging(log_level)
        logger = logging.getLogger(__name__)
        
        # 加载配置
        config = Config()
        logger.info("配置加载完成")
        
        # 设置等待时间（命令行参数优先，否则使用配置文件默认值）
        wait_time = args.wait_time if args.wait_time is not None else config.collection.wait_time
        
        logger.info("🚀 性能医生 - 重构版启动")
        logger.info(f"分析URL: {args.url}")
        logger.info(f"调试模式: {args.debug}")
        logger.info(f"等待时间: {wait_time}秒")
        logger.info(f"无头模式: {args.headless}")
        
        # 创建Chrome管理器
        chrome_manager = ChromeManager(
            chrome_path=config.chrome.chrome_path,
            debug_port=config.chrome.debug_port,
            inherit_cookies=config.chrome.inherit_cookies
        )
        
        # 启动Chrome
        if not chrome_manager.start_chrome(headless=args.headless):
            raise PerfDoctorException("Chrome启动失败")
        
        # 创建新标签页
        tab_info = chrome_manager.create_new_tab()
        if not tab_info or 'webSocketDebuggerUrl' not in tab_info:
            raise PerfDoctorException("无法获取标签页信息")
        
        # 创建DevTools客户端
        devtools_client = DevToolsClient(tab_info['webSocketDebuggerUrl'])
        if not await devtools_client.connect():
            raise PerfDoctorException("DevTools连接失败")
        
        # 创建收集器管理器
        collector_manager = CollectorManager(devtools_client)
        
        # 注册收集器
        if config.collection.enable_performance:
            collector_manager.register_collector(PaintCollector(devtools_client))
            collector_manager.register_collector(NavigationCollector(devtools_client))
            collector_manager.register_collector(PerformanceMetricsCollector(devtools_client))
        
        if config.collection.enable_memory:
            collector_manager.register_collector(MemoryCollector(devtools_client))
        
        if config.collection.enable_network:
            collector_manager.register_collector(NetworkCollector(devtools_client))
        
        # 创建性能服务
        performance_service = PerformanceService(
            collector_manager, 
            config
        )
        
        # 创建报告服务
        report_service = ReportService(config)
        
        # 分析指定URL
        url = args.url
        logger.info(f"开始分析URL: {url}")
        
        # 导航到目标页面
        if not await devtools_client.navigate_to(url):
            raise PerfDoctorException("页面导航失败")
        
        # 等待页面加载
        logger.info(f"等待页面稳定: {wait_time}秒")
        await asyncio.sleep(wait_time)
        
        # 收集性能数据
        performance_data = await performance_service.collect_performance_data(url)
        
        # 生成所有格式的报告
        reports = await report_service.generate_all_reports(performance_data)
        
        logger.info("🎉 性能分析完成")
        logger.info(f"📄 JSON报告: {reports['json']}")
        logger.info(f"📄 HTML报告: {reports['html']}")
        
    except PerfDoctorException as e:
        logger.error(f"性能医生错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # 清理资源
        if 'devtools_client' in locals():
            await devtools_client.disconnect()
        if 'chrome_manager' in locals():
            chrome_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 