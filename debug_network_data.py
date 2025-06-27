#!/usr/bin/env python3
"""
调试网络数据收集和报告生成过程
"""

import asyncio
import json
import os
from modules.performance_doctor import PerformanceDoctor

async def debug_network_data():
    """调试网络数据收集过程"""
    
    print("🔍 调试网络数据收集过程")
    print("=" * 60)
    
    # 创建性能诊断器实例
    doctor = PerformanceDoctor()
    
    try:
        print("📊 开始分析页面...")
        
        # 分析页面
        report = await doctor.analyze_page("https://locdetails.jd.com/h5/index.html#/orderId/319487125867", wait_time=5)
        
        if report.get("success", True):
            print("✅ 页面分析成功")
            
            # 检查网络分析数据
            network_analysis = report.get("network_analysis", {})
            print(f"\n📋 网络分析数据:")
            print(f"  • 网络分析存在: {'network_analysis' in report}")
            print(f"  • 网络分析内容: {list(network_analysis.keys()) if network_analysis else 'None'}")
            
            # 检查资源数据
            resources = network_analysis.get("resources", [])
            print(f"  • 资源数量: {len(resources)}")
            
            if resources:
                print(f"\n📄 前3个资源示例:")
                for i, resource in enumerate(resources[:3], 1):
                    print(f"  {i}. URL: {resource.get('url', resource.get('name', 'N/A'))}")
                    print(f"     方法: {resource.get('method', 'N/A')}")
                    print(f"     状态码: {resource.get('status', 'N/A')}")
                    print(f"     大小: {resource.get('transferSize', 0)/1024:.1f}KB")
                    print(f"     分类: {resource.get('category', 'N/A')}")
                    print()
            else:
                print("❌ 没有收集到资源数据")
            
            # 检查统计信息
            summary = network_analysis.get("summary", {})
            print(f"\n📊 统计信息:")
            print(f"  • 总请求数: {summary.get('total_requests', 0)}")
            print(f"  • 总大小: {summary.get('total_size_mb', 0):.1f}MB")
            print(f"  • API请求数: {summary.get('api_requests', 0)}")
            print(f"  • 第三方请求数: {summary.get('third_party_requests', 0)}")
            
            # 保存原始数据用于调试
            debug_file = "debug_network_data.json"
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n💾 原始数据已保存到: {debug_file}")
            
            # 测试报告生成器
            print(f"\n🔧 测试报告生成器...")
            from modules.report_generator import ReportGenerator
            report_generator = ReportGenerator()
            
            # 获取所有资源
            all_resources = report_generator._get_all_resources(network_analysis)
            print(f"  • 报告生成器提取的资源数量: {len(all_resources)}")
            
            if all_resources:
                print(f"  • 前3个资源:")
                for i, resource in enumerate(all_resources[:3], 1):
                    print(f"    {i}. {resource.get('url', resource.get('name', 'N/A'))}")
            else:
                print("  ❌ 报告生成器没有提取到资源")
            
            # 生成HTML报告
            print(f"\n📄 生成HTML报告...")
            doctor.save_reports([report], "reports")
            
            # 检查生成的HTML文件
            files = os.listdir("reports")
            html_files = [f for f in files if f.endswith('.html')]
            
            if html_files:
                latest_html = max(html_files, key=lambda x: os.path.getmtime(os.path.join("reports", x)))
                print(f"  ✅ HTML报告已生成: reports/{latest_html}")
                
                # 检查HTML文件是否包含资源表格
                with open(os.path.join("reports", latest_html), 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                if "所有资源请求详细信息" in html_content:
                    print("  ✅ HTML包含资源表格标题")
                else:
                    print("  ❌ HTML不包含资源表格标题")
                
                if "resource-table" in html_content:
                    print("  ✅ HTML包含资源表格")
                else:
                    print("  ❌ HTML不包含资源表格")
                
                if "resource-row" in html_content:
                    print("  ✅ HTML包含资源行")
                else:
                    print("  ❌ HTML不包含资源行")
            
        else:
            print(f"❌ 页面分析失败: {report.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        doctor.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_network_data()) 