#!/usr/bin/env python3
"""
简化的测试脚本，用于验证模块化代码的功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.chrome_manager import ChromeManager
from modules.performance_doctor import PerformanceDoctor

async def test_chrome_manager():
    """测试 Chrome 管理器"""
    print("🧪 测试 Chrome 管理器...")
    
    manager = ChromeManager()
    print(f"Chrome 路径: {manager.chrome_path}")
    print(f"调试端口: {manager.debug_port}")
    
    # 测试启动 Chrome
    print("启动 Chrome...")
    success = manager.start_chrome()
    print(f"启动结果: {'成功' if success else '失败'}")
    
    if success:
        # 获取标签页
        tabs = manager.get_tabs()
        print(f"当前标签页数量: {len(tabs)}")
        
        # 创建新标签页
        new_tab = manager.create_new_tab("https://httpbin.org/html")
        if new_tab:
            print(f"创建新标签页成功: {new_tab['id']}")
            
            # 等待一下
            await asyncio.sleep(2)
            
            # 关闭标签页
            manager.close_tab(new_tab['id'])
            print("关闭测试标签页")
    
    # 清理
    manager.cleanup()
    print("Chrome 管理器测试完成")

async def test_performance_doctor():
    """测试性能诊断器"""
    print("\n🧪 测试性能诊断器...")
    
    doctor = PerformanceDoctor()
    
    try:
        # 分析一个简单的页面
        result = await doctor.analyze_page("https://httpbin.org/html", wait_time=3)
        
        if result.get("success", True):
            print("✅ 性能分析成功!")
            print(f"URL: {result['url']}")
            print(f"总体评分: {result.get('overall_score', 0):.1f}/100")
            
            # 显示关键指标
            scores = result.get("scores", {})
            for metric, info in scores.items():
                print(f"{metric.upper()}: {info['value']:.0f}ms ({info['rating']})")
        else:
            print(f"❌ 性能分析失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        doctor.cleanup()
    
    print("性能诊断器测试完成")

async def main():
    """主测试函数"""
    print("=== Chrome Performance Doctor 模块测试 ===\n")
    
    # 测试 Chrome 管理器
    await test_chrome_manager()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试性能诊断器
    await test_performance_doctor()
    
    print("\n=== 所有测试完成 ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
