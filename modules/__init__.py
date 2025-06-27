"""
Chrome Performance Doctor 模块包
"""

from .chrome_manager import ChromeManager
from .devtools_client import DevToolsClient
from .performance_collector import PerformanceCollector
from .report_generator import ReportGenerator

# 收集器插件
from .collectors import (
    BaseCollector,
    PerformanceCollector as CollectorPerformanceCollector,
    PaintCollector,
    NavigationCollector,
    MemoryCollector,
    NetworkCollector,
    CollectorManager
)

__all__ = [
    'ChromeManager', 
    'DevToolsClient', 
    'PerformanceCollector', 
    'ReportGenerator',
    'BaseCollector',
    'CollectorPerformanceCollector',
    'PaintCollector',
    'NavigationCollector', 
    'MemoryCollector',
    'NetworkCollector',
    'CollectorManager'
]
