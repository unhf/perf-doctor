#!/usr/bin/env python3
"""
检查实际性能数据结构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.report_generator import ReportGenerator
import json

def check_real_data():
    """检查实际数据结构"""
    generator = ReportGenerator()
    
    # 模拟一个简单的测试数据
    test_data = {
        "url": "https://example.com",
        "timestamp": 1234567890,
        "performance_data": {
            "data": {
                "PaintCollector": {
                    "data": {
                        "first-contentful-paint": 1800,  # 刚好在good阈值
                        "largest-contentful-paint": 2500  # 刚好在good阈值
                    }
                },
                "NavigationCollector": {
                    "data": {
                        "ttfb": 200,  # 刚好在good阈值
                        "domReady": 2000,  # 刚好在good阈值
                        "pageLoad": 3000,  # 刚好在good阈值
                        "dnsLookup": 50,  # 低于100ms
                        "tcpConnect": 50   # 低于100ms
                    }
                },
                "NetworkCollector": {
                    "data": {
                        "statistics": {
                            "totalRequests": 30,  # 低于50
                            "totalSize": 2 * 1024 * 1024,  # 2MB
                            "avgResponseTime": 300,  # 低于500ms
                            "apiRequests": 5,  # 低于10
                            "thirdPartyRequests": 10  # 低于15
                        }
                    }
                }
            }
        }
    }
    
    print("=== 测试数据（所有指标都在good范围内）===")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    
    # 生成报告
    report = generator.generate_report(test_data)
    
    print("\n=== 提取的关键指标 ===")
    print(json.dumps(report["key_metrics"], indent=2, ensure_ascii=False))
    
    print("\n=== 性能评分 ===")
    print(json.dumps(report["scores"], indent=2, ensure_ascii=False))
    
    print("\n=== 优化建议 ===")
    print(f"建议数量: {len(report['recommendations'])}")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"\n建议 {i}:")
        print(f"  类别: {rec['category']}")
        print(f"  优先级: {rec['priority']}")
        print(f"  问题: {rec['issue']}")
        print(f"  建议: {rec['suggestions']}")
    
    print(f"\n=== 综合评分 ===")
    print(f"综合评分: {report['overall_score']:.1f}")

if __name__ == "__main__":
    check_real_data() 