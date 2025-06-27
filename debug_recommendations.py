#!/usr/bin/env python3
"""
调试优化建议生成逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.report_generator import ReportGenerator
import json

def test_recommendations():
    """测试优化建议生成"""
    generator = ReportGenerator()
    
    # 模拟性能数据
    test_data = {
        "url": "https://example.com",
        "timestamp": 1234567890,
        "performance_data": {
            "data": {
                "PaintCollector": {
                    "data": {
                        "first-contentful-paint": 2500,  # 超过good阈值
                        "largest-contentful-paint": 3500  # 超过good阈值
                    }
                },
                "NavigationCollector": {
                    "data": {
                        "ttfb": 300,  # 超过good阈值
                        "domReady": 2500,  # 超过good阈值
                        "pageLoad": 4000,  # 超过good阈值
                        "dnsLookup": 150,  # 超过100ms
                        "tcpConnect": 120   # 超过100ms
                    }
                },
                "NetworkCollector": {
                    "data": {
                        "statistics": {
                            "totalRequests": 60,  # 超过50
                            "totalSize": 6 * 1024 * 1024,  # 6MB
                            "avgResponseTime": 600,  # 超过500ms
                            "apiRequests": 15,  # 超过10
                            "thirdPartyRequests": 20  # 超过15
                        }
                    }
                }
            }
        }
    }
    
    print("=== 测试数据 ===")
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
    test_recommendations() 