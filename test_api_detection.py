#!/usr/bin/env python3
"""
测试API识别逻辑
"""

import asyncio
from modules.performance_doctor import PerformanceDoctor

async def test_api_detection():
    """测试API识别功能"""
    
    print("🔍 测试API识别逻辑")
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
            resources = network_analysis.get("resources", [])
            
            print(f"\n📋 资源统计:")
            print(f"  • 总资源数量: {len(resources)}")
            
            # 统计API请求
            api_resources = [r for r in resources if r.get("isApi", False)]
            print(f"  • API请求数量: {len(api_resources)}")
            
            if api_resources:
                print(f"\n🔌 识别到的API请求:")
                for i, api in enumerate(api_resources[:10], 1):  # 显示前10个
                    url = api.get("url", "")
                    method = api.get("method", "")
                    status = api.get("status", "")
                    size = api.get("transferSize", 0)
                    print(f"  {i}. {method} {status} {size}bytes - {url[:80]}{'...' if len(url) > 80 else ''}")
            else:
                print("  ❌ 没有识别到API请求")
            
            # 检查统计信息
            summary = network_analysis.get("summary", {})
            print(f"\n📊 网络分析统计:")
            print(f"  • 总请求数: {summary.get('total_requests', 0)}")
            print(f"  • API请求数: {summary.get('api_requests', 0)}")
            print(f"  • 静态请求数: {summary.get('static_requests', 0)}")
            print(f"  • 第三方请求数: {summary.get('third_party_requests', 0)}")
            
            # 分析所有请求的域名分布
            domain_stats = {}
            for resource in resources:
                domain = resource.get("domain", "")
                if domain:
                    domain_stats[domain] = domain_stats.get(domain, 0) + 1
            
            print(f"\n🌐 域名分布 (前10个):")
            sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)
            for domain, count in sorted_domains[:10]:
                print(f"  • {domain}: {count} 个请求")
            
            # 检查可能的API域名
            print(f"\n🔍 可能的API域名:")
            for domain, count in sorted_domains:
                if any(keyword in domain.lower() for keyword in ['api', 'rest', 'service', 'data']):
                    print(f"  • {domain}: {count} 个请求")
            
        else:
            print(f"❌ 页面分析失败: {report.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        doctor.cleanup()

if __name__ == "__main__":
    asyncio.run(test_api_detection()) 