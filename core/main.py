#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome Performance Doctor - 主程序

通过 WebSocket 连接 Chrome DevTools，自动分析页面性能并生成报告
支持自动启动 Chrome、创建新标签页、收集性能数据、生成详细报告

使用方法：
    python main.py [URL1] [URL2] ...
    
如果不提供 URL，将使用配置中的默认测试 URL 列表
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.performance_doctor import PerformanceDoctor
from config import (
    CHROME_CONFIG, 
    PERFORMANCE_CONFIG, 
    DEFAULT_TEST_URLS, 
    REPORT_CONFIG,
    LOGGING_CONFIG
)

def setup_logging():
    """设置日志配置"""
    log_level = getattr(logging, LOGGING_CONFIG["level"].upper(), logging.INFO)
    log_format = LOGGING_CONFIG["format"]
    log_file = LOGGING_CONFIG.get("file")
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        filename=log_file,
        filemode='a' if log_file else None
    )

def show_help():
    """显示帮助信息"""
    help_text = """
🔍 Chrome Performance Doctor - 网页性能分析工具

用法:
    perf-doctor [OPTIONS] [URL...]

参数:
    URL...              要分析的网页 URL（支持多个）

选项:
    -h, --help         显示此帮助信息
    -v, --version      显示版本信息

示例:
    perf-doctor https://example.com
    perf-doctor https://site1.com https://site2.com https://site3.com

功能特性:
    ✅ 自动继承 Chrome 登录状态，免登录分析业务页面
    ✅ 自动启动 Chrome 调试实例
    ✅ 收集完整的性能指标（FCP、LCP、TTFB 等）
    ✅ 生成详细的性能分析报告
    ✅ 支持批量页面分析
    ✅ 识别性能瓶颈并提供优化建议

报告输出:
    • 终端显示概要信息和关键指标
    • JSON 格式详细报告保存到 reports/ 目录
    • 包含具体的优化建议和改进措施

技术实现:
    • 通过 Chrome DevTools Protocol 收集性能数据
    • 自动复制主 Chrome 的登录信息到调试实例
    • 支持复杂业务页面的深度性能分析
"""
    print(help_text)

async def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 处理帮助和版本参数
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            show_help()
            return 0
        elif sys.argv[1] in ['-v', '--version']:
            print("Chrome Performance Doctor v1.0.0")
            return 0
    
    # 从命令行参数获取 URL，如果没有则使用默认 URL
    test_urls = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_TEST_URLS
    
    logger.info("Chrome Performance Doctor 启动")
    logger.info(f"测试 URLs: {test_urls}")
    logger.info(f"配置: 等待时间={PERFORMANCE_CONFIG['wait_time']}s, 并发数={PERFORMANCE_CONFIG['concurrent']}")
    
    # 创建性能诊断器
    doctor = PerformanceDoctor(
        chrome_path=CHROME_CONFIG["path"],
        debug_port=CHROME_CONFIG["debug_port"],
        inherit_cookies=CHROME_CONFIG["inherit_cookies"],
        user_data_dir=CHROME_CONFIG["user_data_dir"]
    )
    
    try:
        # 分析页面
        if len(test_urls) == 1:
            logger.info("开始单页面分析")
            results = [await doctor.analyze_page(test_urls[0], PERFORMANCE_CONFIG["wait_time"])]
        else:
            logger.info("开始批量页面分析")
            results = await doctor.analyze_multiple_pages(
                test_urls, 
                wait_time=PERFORMANCE_CONFIG["wait_time"],
                concurrent=PERFORMANCE_CONFIG["concurrent"]
            )
        
        # 统计结果
        successful_count = sum(1 for r in results if r.get("success", True))
        logger.info(f"分析完成: {successful_count}/{len(results)} 成功")
        
        # 显示结果摘要
        print(f"\n🔍 Chrome Performance Doctor 分析报告")
        print(f"{'='*60}")
        print(f"总页面数: {len(results)}")
        print(f"成功分析: {successful_count}")
        print(f"失败分析: {len(results) - successful_count}")
        
        # 显示每个页面的关键指标
        for i, result in enumerate(results, 1):
            if result.get("success", True):
                print(f"\n📊 [{i}] {result['url']}")
                print(f"    总体评分: {result['overall_score']:.1f}/100")
                
                # 显示关键指标
                key_metrics = ["fcp", "lcp", "ttfb", "dom_ready", "page_load"]
                scores = result.get("scores", {})
                
                for metric in key_metrics:
                    if metric in scores:
                        score_info = scores[metric]
                        rating = score_info["rating"]
                        value = score_info["value"]
                        
                        rating_emoji = {
                            "good": "✅", 
                            "needs_improvement": "⚠️", 
                            "poor": "❌"
                        }
                        emoji = rating_emoji.get(rating, "❓")
                        
                        print(f"    {emoji} {metric.upper()}: {value:.0f}ms ({rating})")
                
                # 显示高优先级建议
                recommendations = result.get("recommendations", [])
                high_priority = [r for r in recommendations if r.get("priority") == "high"]
                if high_priority:
                    print(f"    🔴 高优先级问题: {len(high_priority)} 项")
                    for rec in high_priority[:2]:  # 只显示前两个
                        print(f"       • {rec['category']}: {rec['issue']}")
            else:
                print(f"\n❌ [{i}] {result['url']}")
                print(f"    错误: {result.get('error', 'Unknown error')}")
        
        # 生成汇总报告（多页面时）
        if len(results) > 1:
            summary = doctor.generate_summary_report(results)
            print(f"\n📈 汇总统计")
            print(f"{'='*40}")
            
            avg_score = summary["summary"]["average_score"]
            rating_dist = summary["summary"]["rating_distribution"]
            
            print(f"平均评分: {avg_score:.1f}/100")
            print(f"评级分布:")
            print(f"  ✅ 优秀 (≥80分): {rating_dist['good']} 个")
            print(f"  ⚠️  一般 (50-79分): {rating_dist['needs_improvement']} 个")
            print(f"  ❌ 较差 (<50分): {rating_dist['poor']} 个")
            
            if summary.get("failed_urls"):
                print(f"\n❌ 失败的 URL:")
                for url in summary["failed_urls"]:
                    print(f"  • {url}")
        
        # 保存报告
        if REPORT_CONFIG["save_json"] or REPORT_CONFIG["save_text"]:
            print(f"\n💾 保存报告到: {REPORT_CONFIG['output_dir']}")
            doctor.save_reports(results, REPORT_CONFIG["output_dir"])
        
        print(f"\n✅ 分析完成!")
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        print("\n⚠️  程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"\n❌ 程序执行失败: {e}")
        return 1
    finally:
        # 清理资源
        logger.info("清理资源")
        doctor.cleanup()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  程序被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        sys.exit(1)
