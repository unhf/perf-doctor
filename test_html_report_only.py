#!/usr/bin/env python3
"""
HTML报告生成功能测试脚本

只测试HTML报告生成功能，使用模拟数据
"""

import os
import logging
from modules.report_generator import ReportGenerator
from modules.performance_doctor import PerformanceDoctor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_mock_report():
    """创建模拟的性能报告数据"""
    return {
        "url": "https://example.com",
        "success": True,
        "test_date": "2024-01-15 14:30:00",
        "overall_score": 85.5,
        "key_metrics": {
            "fcp": 1200,
            "lcp": 2100,
            "ttfb": 150,
            "dom_ready": 1800,
            "page_load": 3200
        },
        "scores": {
            "fcp": {
                "value": 1200,
                "score": 92.0,
                "rating": "good",
                "threshold_good": 1800,
                "threshold_poor": 3000
            },
            "lcp": {
                "value": 2100,
                "score": 88.0,
                "rating": "good",
                "threshold_good": 2500,
                "threshold_poor": 4000
            },
            "ttfb": {
                "value": 150,
                "score": 95.0,
                "rating": "good",
                "threshold_good": 200,
                "threshold_poor": 600
            },
            "dom_ready": {
                "value": 1800,
                "score": 90.0,
                "rating": "good",
                "threshold_good": 2000,
                "threshold_poor": 4000
            },
            "page_load": {
                "value": 3200,
                "score": 78.0,
                "rating": "needs_improvement",
                "threshold_good": 3000,
                "threshold_poor": 5000
            }
        },
        "recommendations": [
            {
                "category": "Page Load Time",
                "priority": "medium",
                "issue": "页面加载时间为 3200ms，整体性能需要提升",
                "suggestions": [
                    "压缩和优化所有资源",
                    "启用 Gzip 压缩",
                    "减少 HTTP 请求数量",
                    "使用浏览器缓存"
                ]
            },
            {
                "category": "请求数量优化",
                "priority": "medium",
                "issue": "页面总请求数量为 65 个，请求过多",
                "suggestions": [
                    "合并小文件，减少 HTTP 请求数量",
                    "使用 CSS Sprites 合并图片",
                    "启用 HTTP/2 多路复用",
                    "使用内联关键 CSS 和 JavaScript"
                ]
            }
        ],
        "network_analysis": {
            "summary": {
                "total_requests": 65,
                "total_size_mb": 8.5,
                "avg_response_time": 320,
                "api_requests": 12,
                "static_requests": 35,
                "third_party_requests": 18
            },
            "resources": [
                {
                    "name": "https://example.com/api/users",
                    "domain": "example.com",
                    "transferSize": 2048,
                    "responseTime": 450,
                    "initiatorType": "xmlhttprequest",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False
                },
                {
                    "name": "https://example.com/static/main.js",
                    "domain": "example.com",
                    "transferSize": 512000,
                    "responseTime": 120,
                    "initiatorType": "script",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": False
                },
                {
                    "name": "https://cdn.example.com/images/logo.png",
                    "domain": "cdn.example.com",
                    "transferSize": 256000,
                    "responseTime": 80,
                    "initiatorType": "img",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": True
                },
                {
                    "name": "https://analytics.google.com/collect",
                    "domain": "analytics.google.com",
                    "transferSize": 1024,
                    "responseTime": 200,
                    "initiatorType": "img",
                    "isApi": False,
                    "isStatic": False,
                    "isThirdParty": True
                },
                {
                    "name": "https://example.com/api/products",
                    "domain": "example.com",
                    "transferSize": 1536,
                    "responseTime": 380,
                    "initiatorType": "xmlhttprequest",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False
                },
                {
                    "name": "https://example.com/static/style.css",
                    "domain": "example.com",
                    "transferSize": 128000,
                    "responseTime": 95,
                    "initiatorType": "link",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": False
                },
                {
                    "name": "https://fonts.googleapis.com/css2",
                    "domain": "fonts.googleapis.com",
                    "transferSize": 64000,
                    "responseTime": 150,
                    "initiatorType": "link",
                    "isApi": False,
                    "isStatic": False,
                    "isThirdParty": True
                },
                {
                    "name": "https://example.com/api/orders",
                    "domain": "example.com",
                    "transferSize": 3072,
                    "responseTime": 520,
                    "initiatorType": "xmlhttprequest",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False
                }
            ],
            "large_resources": [
                {
                    "name": "https://example.com/static/main.js",
                    "domain": "example.com",
                    "transferSize": 512000,
                    "responseTime": 120,
                    "initiatorType": "script",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": False
                },
                {
                    "name": "https://cdn.example.com/images/logo.png",
                    "domain": "cdn.example.com",
                    "transferSize": 256000,
                    "responseTime": 80,
                    "initiatorType": "img",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": True
                }
            ],
            "slow_requests": [
                {
                    "name": "https://example.com/api/orders",
                    "domain": "example.com",
                    "transferSize": 3072,
                    "responseTime": 520,
                    "initiatorType": "xmlhttprequest",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False
                }
            ],
            "api_requests": [
                {
                    "name": "https://example.com/api/users",
                    "domain": "example.com",
                    "transferSize": 2048,
                    "responseTime": 450,
                    "initiatorType": "xmlhttprequest",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False
                },
                {
                    "name": "https://example.com/api/products",
                    "domain": "example.com",
                    "transferSize": 1536,
                    "responseTime": 380,
                    "initiatorType": "xmlhttprequest",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False
                },
                {
                    "name": "https://example.com/api/orders",
                    "domain": "example.com",
                    "transferSize": 3072,
                    "responseTime": 520,
                    "initiatorType": "xmlhttprequest",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False
                }
            ],
            "third_party_resources": [
                {
                    "name": "https://cdn.example.com/images/logo.png",
                    "domain": "cdn.example.com",
                    "transferSize": 256000,
                    "responseTime": 80,
                    "initiatorType": "img",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": True
                },
                {
                    "name": "https://analytics.google.com/collect",
                    "domain": "analytics.google.com",
                    "transferSize": 1024,
                    "responseTime": 200,
                    "initiatorType": "img",
                    "isApi": False,
                    "isStatic": False,
                    "isThirdParty": True
                },
                {
                    "name": "https://fonts.googleapis.com/css2",
                    "domain": "fonts.googleapis.com",
                    "transferSize": 64000,
                    "responseTime": 150,
                    "initiatorType": "link",
                    "isApi": False,
                    "isStatic": False,
                    "isThirdParty": True
                }
            ]
        }
    }

def test_html_report_generation():
    """测试HTML报告生成功能"""
    
    print("🚀 测试HTML报告生成功能")
    print("=" * 60)
    
    # 创建模拟报告数据
    print("📊 创建模拟报告数据...")
    mock_report = create_mock_report()
    
    # 创建reports目录
    os.makedirs("reports", exist_ok=True)
    
    # 创建性能诊断器实例
    doctor = PerformanceDoctor()
    
    try:
        print("📄 生成综合报告...")
        
        # 直接使用save_reports方法，只生成HTML报告
        doctor.save_reports([mock_report], "reports")
        
        print("✅ 报告生成成功!")
        
        # 检查生成的文件
        files = os.listdir("reports")
        html_files = [f for f in files if f.endswith('.html')]
        json_files = [f for f in files if f.endswith('.json')]
        txt_files = [f for f in files if f.endswith('.txt')]
        
        print(f"\n📁 生成的文件:")
        print(f"  • HTML文件: {len(html_files)} 个")
        print(f"  • JSON文件: {len(json_files)} 个")
        print(f"  • TXT文件: {len(txt_files)} 个")
        
        if html_files:
            print(f"\n📄 HTML报告文件:")
            for html_file in html_files:
                file_path = os.path.join("reports", html_file)
                file_size = os.path.getsize(file_path)
                print(f"  • {html_file} ({file_size} bytes)")
        
        # 显示报告摘要
        network_analysis = mock_report.get("network_analysis", {})
        summary = network_analysis.get("summary", {})
        
        print(f"\n📊 报告摘要:")
        print(f"  • 总体评分: {mock_report.get('overall_score', 0):.1f}/100")
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
        
        # 显示大文件和慢请求
        large_resources = network_analysis.get("large_resources", [])
        slow_requests = network_analysis.get("slow_requests", [])
        
        if large_resources:
            print(f"\n📁 大资源文件 (>500KB): {len(large_resources)} 个")
            for i, resource in enumerate(large_resources[:3], 1):
                size_kb = resource.get("transferSize", 0) / 1024
                print(f"  {i}. {resource['domain']} - {size_kb:.1f}KB")
        
        if slow_requests:
            print(f"\n🐌 慢请求 (>1秒): {len(slow_requests)} 个")
            for i, resource in enumerate(slow_requests[:3], 1):
                response_time = resource.get("responseTime", 0)
                print(f"  {i}. {resource['domain']} - {response_time:.0f}ms")
        
        # 显示优化建议
        recommendations = mock_report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 主要优化建议:")
            for i, rec in enumerate(recommendations[:3], 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                emoji = priority_emoji.get(rec["priority"], "⚪")
                print(f"  {i}. {emoji} {rec['category']}: {rec['issue']}")
        
        # 验证只生成了HTML文件
        if html_files and not json_files and not txt_files:
            print(f"\n🎉 测试通过! 只生成了HTML报告文件")
        else:
            print(f"\n⚠️  注意: 还生成了非HTML文件")
        
        print(f"\n🎉 测试完成!")
        if html_files:
            latest_html = max(html_files, key=lambda x: os.path.getmtime(os.path.join("reports", x)))
            print(f"📄 请打开完整HTML报告查看详细信息: reports/{latest_html}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        doctor.cleanup()

def main():
    """主函数"""
    print("HTML报告生成功能测试")
    print("=" * 60)
    print("本测试将生成包含以下内容的完整HTML报告:")
    print("• 📊 性能指标详情")
    print("• 💡 优化建议")
    print("• 📋 所有资源请求列表")
    print("• 🔍 搜索和过滤功能")
    print("• 📱 响应式设计")
    print("=" * 60)
    
    # 运行测试
    test_html_report_generation()

if __name__ == "__main__":
    main() 