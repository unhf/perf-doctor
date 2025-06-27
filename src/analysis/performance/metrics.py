"""
性能指标计算

提供常用性能指标的计算方法
"""

from typing import Dict, Any

class PerformanceMetrics:
    """性能指标工具类"""
    @staticmethod
    def calc_fcp(paint: Dict[str, Any]) -> float:
        return paint.get('first-contentful-paint', 0)

    @staticmethod
    def calc_lcp(paint: Dict[str, Any]) -> float:
        return paint.get('largest-contentful-paint', 0)

    @staticmethod
    def calc_load_time(nav: Dict[str, Any]) -> float:
        return nav.get('pageLoad', 0)

    @staticmethod
    def calc_ttfb(nav: Dict[str, Any]) -> float:
        return nav.get('ttfb', 0)

    @staticmethod
    def calc_dom_ready(nav: Dict[str, Any]) -> float:
        return nav.get('domReady', 0)

    @staticmethod
    def calc_memory_usage(mem: Dict[str, Any]) -> float:
        return mem.get('heapUsagePercent', 0)

    @staticmethod
    def summary(paint, nav, mem) -> Dict[str, Any]:
        return {
            'fcp': PerformanceMetrics.calc_fcp(paint),
            'lcp': PerformanceMetrics.calc_lcp(paint),
            'load_time': PerformanceMetrics.calc_load_time(nav),
            'ttfb': PerformanceMetrics.calc_ttfb(nav),
            'dom_ready': PerformanceMetrics.calc_dom_ready(nav),
            'memory_usage': PerformanceMetrics.calc_memory_usage(mem)
        } 