#!/usr/bin/env python3
"""
完整HTML性能报告测试脚本

测试生成包含所有请求和接口信息的完整静态HTML报告
"""

import asyncio
import logging
import os
from modules.performance_doctor import PerformanceDoctor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_full_html_report():
    """测试完整HTML报告生成功能"""
    
    # 测试URL
    test_url = "https://www.baidu.com"
    
    print("🚀 测试完整HTML性能报告生成")
    print("=" * 60)
    print(f"测试URL: {test_url}")
    print("=" * 60)
    
    # 创建reports目录
    os.makedirs("reports", exist_ok=True)
    
    async with PerformanceDoctor() as doctor:
        try:
            print("📊 开始分析页面...")
            
            # 分析页面性能
            report = await doctor.analyze_page(test_url, wait_time=8)
            
            if report.get("success", True):
                print("✅ 页面分析成功")
                
                # 生成综合报告
                print("📄 生成综合报告...")
                report_files = doctor.report_generator.generate_comprehensive_report(report, "reports")
                
                if report_files:
                    print("✅ 报告生成成功!")
                    print("\n📁 生成的文件:")
                    print(f"  • JSON报告: {report_files['json_report']}")
                    print(f"  • 文本报告: {report_files['text_report']}")
                    print(f"  • HTML网络分析: {report_files['html_network_report']}")
                    print(f"  • 完整HTML报告: {report_files['full_html_report']}")
                    
                    # 显示报告摘要
                    network_analysis = report.get("network_analysis", {})
                    summary = network_analysis.get("summary", {})
                    
                    print(f"\n📊 报告摘要:")
                    print(f"  • 总体评分: {report.get('overall_score', 0):.1f}/100")
                    print(f"  • 总请求数: {summary.get('total_requests', 0)} 个")
                    print(f"  • 总资源大小: {summary.get('total_size_mb', 0):.1f} MB")
                    print(f"  • API请求数: {summary.get('api_requests', 0)} 个")
                    print(f"  • 第三方请求数: {summary.get('third_party_requests', 0)} 个")
                    
                    # 显示所有资源统计
                    all_resources = network_analysis.get("resources", [])
                    if all_resources:
                        api_count = len([r for r in all_resources if r.get("isApi", False)])
                        static_count = len([r for r in all_resources if r.get("isStatic", False)])
                        third_party_count = len([r for r in all_resources if r.get("isThirdParty", False)])
                        
                        print(f"\n📋 资源分类统计:")
                        print(f"  • API请求: {api_count} 个")
                        print(f"  • 静态资源: {static_count} 个")
                        print(f"  • 第三方资源: {third_party_count} 个")
                        print(f"  • 其他资源: {len(all_resources) - api_count - static_count - third_party_count} 个")
                    
                    print(f"\n🎉 测试完成!")
                    print(f"📄 请打开完整HTML报告查看详细信息: {report_files['full_html_report']}")
                    
                else:
                    print("❌ 报告生成失败")
                    
            else:
                print(f"❌ 页面分析失败: {report.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")

def main():
    """主函数"""
    print("完整HTML性能报告测试")
    print("=" * 60)
    print("本测试将生成包含以下内容的完整HTML报告:")
    print("• 📊 性能指标详情")
    print("• 💡 优化建议")
    print("• 📋 所有资源请求列表")
    print("• 🔍 搜索和过滤功能")
    print("• 📱 响应式设计")
    print("=" * 60)
    
    # 运行测试
    asyncio.run(test_full_html_report())

if __name__ == "__main__":
    main() 