#!/usr/bin/env python3
"""
测试增强的网络收集和报告生成功能
"""

import asyncio
import os
from modules.performance_doctor import PerformanceDoctor

async def test_enhanced_network():
    """测试增强的网络收集功能"""
    
    print("🧪 测试增强的网络收集功能")
    print("=" * 60)
    
    # 创建模拟的增强网络数据
    mock_enhanced_report = {
        "url": "https://example.com",
        "success": True,
        "overall_score": 85.5,
        "scores": {
            "fcp": {"value": 1200, "rating": "good", "score": 92.0},
            "lcp": {"value": 2100, "rating": "good", "score": 88.0},
            "ttfb": {"value": 150, "rating": "good", "score": 95.0},
            "dom_ready": {"value": 1800, "rating": "good", "score": 90.0},
            "page_load": {"value": 3200, "rating": "needs_improvement", "score": 78.0}
        },
        "recommendations": [
            {
                "category": "页面加载时间优化",
                "priority": "medium",
                "issue": "页面加载时间为 3200ms，整体性能需要提升",
                "suggestions": ["压缩和优化所有资源", "启用 Gzip 压缩", "减少 HTTP 请求数量", "使用浏览器缓存"]
            }
        ],
        "network_analysis": {
            "summary": {
                "total_requests": 8,
                "total_size_mb": 2.5,
                "avg_response_time": 320,
                "api_requests": 3,
                "third_party_requests": 2
            },
            "resources": [
                {
                    "requestId": "1",
                    "url": "https://example.com/api/users",
                    "method": "GET",
                    "status": 200,
                    "mimeType": "application/json",
                    "transferSize": 2048,
                    "responseTime": 450,
                    "domain": "example.com",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False,
                    "category": "API",
                    "requestHeaders": {
                        "Accept": "application/json",
                        "Authorization": "Bearer ***",
                        "User-Agent": "Mozilla/5.0..."
                    },
                    "responseHeaders": {
                        "Content-Type": "application/json",
                        "Cache-Control": "no-cache",
                        "Content-Length": "2048"
                    },
                    "requestBody": "",
                    "responseBody": '{"users": [{"id": 1, "name": "John Doe", "email": "john@example.com"}, {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}]}'
                },
                {
                    "requestId": "2",
                    "url": "https://example.com/static/main.js",
                    "method": "GET",
                    "status": 200,
                    "mimeType": "application/javascript",
                    "transferSize": 512000,
                    "responseTime": 120,
                    "domain": "example.com",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": False,
                    "category": "Static",
                    "requestHeaders": {
                        "Accept": "*/*",
                        "User-Agent": "Mozilla/5.0..."
                    },
                    "responseHeaders": {
                        "Content-Type": "application/javascript",
                        "Cache-Control": "public, max-age=31536000",
                        "Content-Length": "512000"
                    },
                    "requestBody": "",
                    "responseBody": "// 这里是压缩后的JavaScript代码...\n(function(){console.log('Hello World');})();"
                },
                {
                    "requestId": "3",
                    "url": "https://example.com/api/products",
                    "method": "POST",
                    "status": 201,
                    "mimeType": "application/json",
                    "transferSize": 1536,
                    "responseTime": 380,
                    "domain": "example.com",
                    "isApi": True,
                    "isStatic": False,
                    "isThirdParty": False,
                    "category": "API",
                    "requestHeaders": {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": "Bearer ***"
                    },
                    "responseHeaders": {
                        "Content-Type": "application/json",
                        "Location": "/api/products/123"
                    },
                    "requestBody": '{"name": "New Product", "price": 99.99, "category": "electronics"}',
                    "responseBody": '{"id": 123, "name": "New Product", "price": 99.99, "status": "created"}'
                },
                {
                    "requestId": "4",
                    "url": "https://cdn.example.com/images/logo.png",
                    "method": "GET",
                    "status": 200,
                    "mimeType": "image/png",
                    "transferSize": 256000,
                    "responseTime": 80,
                    "domain": "cdn.example.com",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": True,
                    "category": "Third-party",
                    "requestHeaders": {
                        "Accept": "image/*",
                        "User-Agent": "Mozilla/5.0..."
                    },
                    "responseHeaders": {
                        "Content-Type": "image/png",
                        "Cache-Control": "public, max-age=86400"
                    },
                    "requestBody": "",
                    "responseBody": ""  # 图片数据不显示
                },
                {
                    "requestId": "5",
                    "url": "https://fonts.googleapis.com/css2",
                    "method": "GET",
                    "status": 200,
                    "mimeType": "text/css",
                    "transferSize": 64000,
                    "responseTime": 150,
                    "domain": "fonts.googleapis.com",
                    "isApi": False,
                    "isStatic": False,
                    "isThirdParty": True,
                    "category": "Third-party",
                    "requestHeaders": {
                        "Accept": "text/css,*/*;q=0.1",
                        "User-Agent": "Mozilla/5.0..."
                    },
                    "responseHeaders": {
                        "Content-Type": "text/css",
                        "Cache-Control": "public, max-age=86400"
                    },
                    "requestBody": "",
                    "responseBody": "@font-face{font-family:'Roboto';font-style:normal;font-weight:400;src:url(https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxK.woff2) format('woff2');}"
                }
            ]
        }
    }
    
    # 创建reports目录
    os.makedirs("reports", exist_ok=True)
    
    # 创建性能诊断器实例
    doctor = PerformanceDoctor()
    
    try:
        print("📄 生成增强的HTML报告...")
        
        # 使用增强的save_reports方法
        doctor.save_reports([mock_enhanced_report], "reports")
        
        print("✅ 增强HTML报告生成成功!")
        
        # 检查生成的文件
        files = os.listdir("reports")
        html_files = [f for f in files if f.endswith('.html')]
        
        print(f"\n📁 生成的文件:")
        print(f"  • HTML文件: {len(html_files)} 个")
        
        if html_files:
            print(f"\n📄 HTML报告文件:")
            for html_file in html_files:
                file_path = os.path.join("reports", html_file)
                file_size = os.path.getsize(file_path)
                print(f"  • {html_file} ({file_size} bytes)")
        
        # 显示报告摘要
        network_analysis = mock_enhanced_report.get("network_analysis", {})
        summary = network_analysis.get("summary", {})
        
        print(f"\n📊 报告摘要:")
        print(f"  • 总体评分: {mock_enhanced_report.get('overall_score', 0):.1f}/100")
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
        
        # 显示详细信息示例
        print(f"\n🔍 详细信息示例:")
        for i, resource in enumerate(all_resources[:2], 1):
            print(f"  {i}. {resource['method']} {resource['url']}")
            print(f"     状态码: {resource['status']}")
            print(f"     大小: {resource['transferSize']/1024:.1f}KB")
            print(f"     响应时间: {resource['responseTime']:.0f}ms")
            print(f"     分类: {resource['category']}")
            if resource.get('requestBody'):
                print(f"     请求体: {resource['requestBody'][:50]}...")
            if resource.get('responseBody'):
                print(f"     响应体: {resource['responseBody'][:50]}...")
            print()
        
        print(f"\n🎉 测试完成!")
        if html_files:
            latest_html = max(html_files, key=lambda x: os.path.getmtime(os.path.join("reports", x)))
            print(f"📄 请打开增强HTML报告查看详细信息: reports/{latest_html}")
            print(f"💡 在报告中可以点击'查看详情'按钮查看每个资源的完整信息")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        doctor.cleanup()

if __name__ == "__main__":
    asyncio.run(test_enhanced_network()) 