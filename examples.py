#!/usr/bin/env python3
"""
Chrome Performance Doctor 使用示例

展示如何使用模块化的 API 进行性能分析
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.performance_doctor import PerformanceDoctor

async def analyze_single_page():
    """分析单个页面的示例"""
    print("📊 单页面性能分析示例")
    print("=" * 40)
    
    # 创建性能诊断器
    with PerformanceDoctor() as doctor:  # 使用上下文管理器自动清理
        # 分析页面
        result = await doctor.analyze_page("https://www.baidu.com", wait_time=5)
        
        if result.get("success", True):
            print(f"✅ 分析成功: {result['url']}")
            print(f"总体评分: {result['overall_score']:.1f}/100")
            
            # 显示关键指标
            for metric, info in result.get("scores", {}).items():
                rating_emoji = {"good": "✅", "needs_improvement": "⚠️", "poor": "❌"}
                emoji = rating_emoji.get(info["rating"], "❓")
                print(f"{emoji} {metric.upper()}: {info['value']:.0f}ms")
                
            # 显示建议
            recommendations = result.get("recommendations", [])
            if recommendations:
                print("\n💡 优化建议:")
                for rec in recommendations[:3]:  # 只显示前3个
                    print(f"• {rec['category']}: {rec['issue']}")
        else:
            print(f"❌ 分析失败: {result.get('error', 'Unknown error')}")

async def analyze_multiple_pages():
    """批量分析多个页面的示例"""
    print("\n📈 批量页面性能分析示例")
    print("=" * 40)
    
    test_urls = [
        "https://www.baidu.com",
        "https://httpbin.org/html",
        "https://httpbin.org/delay/2"
    ]
    
    with PerformanceDoctor() as doctor:
        # 批量分析
        results = await doctor.analyze_multiple_pages(test_urls, wait_time=3)
        
        # 显示结果摘要
        successful = [r for r in results if r.get("success", True)]
        print(f"分析完成: {len(successful)}/{len(results)} 成功")
        
        # 显示每个页面的结果
        for i, result in enumerate(results, 1):
            if result.get("success", True):
                print(f"\n[{i}] {result['url'][:50]}...")
                print(f"    评分: {result['overall_score']:.1f}/100")
            else:
                print(f"\n[{i}] {result['url'][:50]}... ❌ 失败")
        
        # 生成汇总报告
        if len(successful) > 1:
            summary = doctor.generate_summary_report(results)
            avg_score = summary["summary"]["average_score"]
            print(f"\n📊 平均评分: {avg_score:.1f}/100")
        
        # 保存报告
        print(f"\n💾 保存报告到 reports/ 目录")
        doctor.save_reports(results)

async def custom_configuration_example():
    """自定义配置的示例"""
    print("\n⚙️  自定义配置示例")
    print("=" * 40)
    
    # 使用自定义配置创建诊断器
    doctor = PerformanceDoctor(
        chrome_path=None,  # 自动检测
        debug_port=9223    # 使用不同的端口
    )
    
    try:
        result = await doctor.analyze_page("https://httpbin.org/json", wait_time=2)
        
        if result.get("success", True):
            print(f"✅ 使用端口 9223 分析成功")
            print(f"评分: {result['overall_score']:.1f}/100")
        else:
            print(f"❌ 分析失败: {result.get('error')}")
    
    finally:
        doctor.cleanup()

async def main():
    """主函数"""
    print("🔍 Chrome Performance Doctor API 使用示例")
    print("=" * 50)
    
    try:
        # 单页面分析
        await analyze_single_page()
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 批量分析
        await analyze_multiple_pages()
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 自定义配置
        await custom_configuration_example()
        
        print(f"\n✅ 所有示例运行完成!")
        print(f"📁 查看 reports/ 目录获取详细报告")
        
    except KeyboardInterrupt:
        print("\n⚠️  示例被用户中断")
    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
