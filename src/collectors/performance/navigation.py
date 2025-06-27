"""
导航时序收集器

收集页面导航时序数据
"""

import logging
from typing import Dict, Any, List

from ..base.collector import BaseCollector
from ...core.types import CollectorResult, NavigationData


class NavigationCollector(BaseCollector):
    """导航时序收集器"""
    
    def __init__(self, client):
        super().__init__(client, "NavigationCollector", "收集导航时序数据")
        self.navigation_data = {}
    
    def get_required_domains(self) -> List[str]:
        """获取需要的DevTools域"""
        return ["Performance"]
    
    async def setup(self) -> bool:
        """设置导航时序收集器"""
        try:
            await self._enable_required_domains()
            return True
        except Exception as e:
            self.logger.error(f"设置导航收集器失败: {e}")
            return False
    
    async def collect(self) -> CollectorResult:
        """收集导航时序数据"""
        try:
            navigation_script = """
                (function() {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    if (!navigation) return null;
                    
                    return {
                        navigationStart: navigation.startTime,
                        fetchStart: navigation.fetchStart,
                        domainLookupStart: navigation.domainLookupStart,
                        domainLookupEnd: navigation.domainLookupEnd,
                        connectStart: navigation.connectStart,
                        connectEnd: navigation.connectEnd,
                        requestStart: navigation.requestStart,
                        responseStart: navigation.responseStart,
                        responseEnd: navigation.responseEnd,
                        domLoading: navigation.domLoading,
                        domInteractive: navigation.domInteractive,
                        domContentLoadedEventStart: navigation.domContentLoadedEventStart,
                        domContentLoadedEventEnd: navigation.domContentLoadedEventEnd,
                        domComplete: navigation.domComplete,
                        loadEventStart: navigation.loadEventStart,
                        loadEventEnd: navigation.loadEventEnd,
                        navigationType: navigation.type,
                        redirectCount: navigation.redirectCount
                    };
                })();
            """
            
            navigation_timing = await self.client.execute_javascript(navigation_script)
            
            if navigation_timing:
                # 计算衍生指标
                navigation_timing.update({
                    'dnsLookup': navigation_timing.get('domainLookupEnd', 0) - navigation_timing.get('domainLookupStart', 0),
                    'tcpConnect': navigation_timing.get('connectEnd', 0) - navigation_timing.get('connectStart', 0),
                    'ttfb': navigation_timing.get('responseStart', 0) - navigation_timing.get('requestStart', 0),
                    'domReady': navigation_timing.get('domInteractive', 0) - navigation_timing.get('domLoading', 0),
                    'pageLoad': navigation_timing.get('loadEventEnd', 0) - navigation_timing.get('navigationStart', 0)
                })
                
                self.navigation_data = navigation_timing
            
            return self._create_result(self.navigation_data)
            
        except Exception as e:
            self.logger.error(f"收集导航时序数据失败: {e}")
            return self._create_result({}, str(e)) 