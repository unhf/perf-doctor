"""
基础收集器模块

提供收集器的基础类和通用功能
"""

from .collector import BaseCollector
from .manager import CollectorManager

__all__ = [
    'BaseCollector',
    'CollectorManager'
] 