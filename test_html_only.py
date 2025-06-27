#!/usr/bin/env python3
"""
测试只生成HTML报告的功能
"""

import asyncio
import os
from modules.performance_doctor import PerformanceDoctor

async def test_html_only():
    """测试只生成HTML报告的功能"""
    
    print("🧪 测试只生成HTML报告功能")
    print("=" * 50)
    
    # 创建模拟报告数据
    mock_report = {
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
                "total_requests": 65,
                "total_size_mb": 8.5,
                "avg_response_time": 320,
                "api_requests": 12,
                "third_party_requests": 18
            },
            "resources": [
                {
                    "url": "https://example.com/static/main.js",
                    "domain": "example.com",
                    "transferSize": 512000,
                    "responseTime": 120,
                    "type": "script",
                    "isApi": False,
                    "isStatic": True,
                    "isThirdParty": False
                }
            ]
        }
    }
    
    # 创建reports目录
    os.makedirs("reports", exist_ok=True)
    
    # 创建性能诊断器实例
    doctor = PerformanceDoctor()
    
    try:
        print("📄 生成HTML报告...")
        
        # 使用修改后的save_reports方法
        doctor.save_reports([mock_report], "reports")
        
        print("✅ HTML报告生成成功!")
        
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
        
        if json_files:
            print(f"\n⚠️  意外生成的JSON文件:")
            for json_file in json_files:
                print(f"  • {json_file}")
        
        if txt_files:
            print(f"\n⚠️  意外生成的TXT文件:")
            for txt_file in txt_files:
                print(f"  • {txt_file}")
        
        # 验证只生成了HTML文件
        if html_files and not json_files and not txt_files:
            print(f"\n🎉 测试通过! 只生成了HTML报告文件")
        else:
            print(f"\n❌ 测试失败! 生成了非HTML文件")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        doctor.cleanup()

if __name__ == "__main__":
    asyncio.run(test_html_only()) 