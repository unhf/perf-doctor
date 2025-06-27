"""
Chrome管理模块

管理Chrome浏览器的启动、配置和进程控制
"""

from .manager import ChromeManager
from .process import ChromeProcess

__all__ = [
    'ChromeManager',
    'ChromeProcess'
] 