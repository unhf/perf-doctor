#!/usr/bin/env python3
"""
Chrome Performance Doctor 使用示例
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.main import ChromePerformanceDoctor


async def analyze_single_page():
    """分析单个页面的示例"""
    doctor = ChromePerformanceDoctor()
    
    try:
        url = "https://www.baidu.com"  # 改为更常见的网站
        print(f"正在分析页面: {url}")
        
        report = await doctor.analyze_page_performance(url)
        
        if report:
            print(report)
        else:
            print("分析失败")
            
    finally:
        doctor.cleanup()


async def compare_multiple_pages():
    """比较多个页面性能的示例"""
    doctor = ChromePerformanceDoctor()
    
    urls = [
        "https://www.baidu.com",
        "https://www.google.com",
        "https://www.bing.com"
    ]
    
    results = {}
    
    try:
        for url in urls:
            print(f"\n正在分析: {url}")
            report = await doctor.analyze_page_performance(url)
            results[url] = report
            
            # 稍作停顿
            await asyncio.sleep(2)
        
        # 输出比较结果
        print("\n" + "="*60)
        print("性能比较结果")
        print("="*60)
        
        for url, report in results.items():
            print(f"\n{url}:")
            if report:
                # 简化输出，只显示关键指标
                lines = report.split('\n')
                for line in lines:
                    if '页面加载时间:' in line or '首次绘制时间:' in line:
                        print(f"  {line}")
            else:
                print("  分析失败")
                
    finally:
        doctor.cleanup()


if __name__ == "__main__":
    print("Chrome Performance Doctor 示例")
    print("1. 分析单个页面")
    print("2. 比较多个页面")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        asyncio.run(analyze_single_page())
    elif choice == "2":
        asyncio.run(compare_multiple_pages())
    else:
        print("无效选择")
