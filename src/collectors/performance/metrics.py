"""
性能指标收集器

收集各种性能指标
"""

import logging
from typing import Dict, Any, List

from ..base.collector import BaseCollector
from ...core.types import CollectorResult


class PerformanceMetricsCollector(BaseCollector):
    """性能指标收集器"""
    
    def __init__(self, client):
        super().__init__(client, "PerformanceMetricsCollector", "收集性能指标")
        self.metrics_data = {}
    
    def get_required_domains(self) -> List[str]:
        """获取需要的DevTools域"""
        return ["Performance"]
    
    async def setup(self) -> bool:
        """设置性能指标收集器"""
        try:
            await self._enable_required_domains()
            return True
        except Exception as e:
            self.logger.error(f"设置性能指标收集器失败: {e}")
            return False
    
    async def collect(self) -> CollectorResult:
        """收集性能指标"""
        try:
            metrics_script = """
                (function() {
                    const metrics = {};
                    
                    // 基本性能指标
                    if (performance.timing) {
                        const timing = performance.timing;
                        metrics.loadTime = timing.loadEventEnd - timing.navigationStart;
                        metrics.domReadyTime = timing.domContentLoadedEventEnd - timing.navigationStart;
                        metrics.firstPaintTime = timing.responseEnd - timing.navigationStart;
                    }
                    
                    // 现代性能API
                    if (performance.getEntriesByType) {
                        const navigationEntries = performance.getEntriesByType('navigation');
                        if (navigationEntries.length > 0) {
                            const nav = navigationEntries[0];
                            metrics.loadTime = nav.loadEventEnd - nav.startTime;
                            metrics.domReadyTime = nav.domContentLoadedEventEnd - nav.startTime;
                            metrics.firstPaintTime = nav.responseEnd - nav.startTime;
                        }
                        
                        const paintEntries = performance.getEntriesByType('paint');
                        paintEntries.forEach(entry => {
                            if (entry.name === 'first-paint') {
                                metrics.firstPaint = entry.startTime;
                            }
                            if (entry.name === 'first-contentful-paint') {
                                metrics.firstContentfulPaint = entry.startTime;
                            }
                        });
                    }
                    
                    // 资源加载时间
                    if (performance.getEntriesByType) {
                        const resourceEntries = performance.getEntriesByType('resource');
                        metrics.resourceCount = resourceEntries.length;
                        metrics.totalResourceSize = resourceEntries.reduce((sum, entry) => sum + (entry.transferSize || 0), 0);
                    }
                    
                    return metrics;
                })();
            """
            
            metrics = await self.client.execute_javascript(metrics_script)
            
            if metrics:
                self.metrics_data = metrics
            else:
                self.metrics_data = {}
            
            return self._create_result(self.metrics_data)
            
        except Exception as e:
            self.logger.error(f"收集性能指标失败: {e}")
            return self._create_result({}, str(e)) 