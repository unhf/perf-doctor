#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Doctor 可执行文件入口

用于 PyInstaller 打包的主入口文件
"""

import sys
import os
import asyncio

# 确保项目根目录在 Python 路径中
if getattr(sys, 'frozen', False):
    # 运行在 PyInstaller 打包的环境中
    application_path = sys._MEIPASS
else:
    # 运行在正常 Python 环境中
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

def main():
    """主函数入口"""
    try:
        # 导入主程序
        from core.main import main as core_main
        
        # 运行主程序
        return asyncio.run(core_main())
        
    except KeyboardInterrupt:
        print("\n⚠️  程序被用户中断")
        return 1
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
