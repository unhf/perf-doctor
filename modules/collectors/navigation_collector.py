"""
导航时序收集器

收集页面导航时序数据，包括 DNS 查询、TCP 连接、DOM 加载等关键时序指标
"""

import time
import logging
from typing import Dict, Any
from .base_collector import BaseCollector


class NavigationCollector(BaseCollector):
    """导航时序收集器"""
    
    def __init__(self, devtools_client):
        super().__init__(devtools_client, "NavigationCollector")
        self.timing_data = {}
        self.load_events = {}
    
    def get_required_domains(self) -> list:
        """获取需要的 DevTools 域"""
        return ["Page"]
    
    async def setup(self) -> bool:
        """设置导航时序收集器"""
        try:
            await self.client.enable_domain("Page")
            
            # 设置事件处理器
            self.client.add_event_handler("Page.loadEventFired", self._on_load_event)
            self.client.add_event_handler("Page.domContentLoadedEventFired", self._on_dom_loaded)
            
            self.logger.debug("导航时序收集器设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置导航时序收集器失败: {e}")
            return False
    
    async def collect(self) -> Dict[str, Any]:
        """收集导航时序数据"""
        if not self.enabled:
            return {}
        
        try:
            # 获取导航时序数据
            timing_data = await self._collect_navigation_timing()
            
            # 合并加载事件数据
            result = {
                "type": "navigation_timing",
                "data": timing_data,
                "load_events": self.load_events,
                "timestamp": time.time()
            }
            
            self.timing_data = timing_data
            self.logger.debug("收集到导航时序数据")
            
            return result
            
        except Exception as e:
            self.logger.error(f"收集导航时序失败: {e}")
            return {"type": "navigation_timing", "error": str(e)}
    
    async def _collect_navigation_timing(self) -> Dict[str, float]:
        """收集导航时序数据"""
        try:
            timing_script = """
            (function() {
                const timing = performance.timing;
                const navigation = performance.navigation;
                
                return {
                    // 基础时序
                    navigationStart: timing.navigationStart,
                    fetchStart: timing.fetchStart,
                    domainLookupStart: timing.domainLookupStart,
                    domainLookupEnd: timing.domainLookupEnd,
                    connectStart: timing.connectStart,
                    connectEnd: timing.connectEnd,
                    requestStart: timing.requestStart,
                    responseStart: timing.responseStart,
                    responseEnd: timing.responseEnd,
                    domLoading: timing.domLoading,
                    domInteractive: timing.domInteractive,
                    domContentLoadedEventStart: timing.domContentLoadedEventStart,
                    domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                    domComplete: timing.domComplete,
                    loadEventStart: timing.loadEventStart,
                    loadEventEnd: timing.loadEventEnd,
                    
                    // 计算关键指标
                    dnsLookup: timing.domainLookupEnd - timing.domainLookupStart,
                    tcpConnect: timing.connectEnd - timing.connectStart,
                    ttfb: timing.responseStart - timing.requestStart,
                    domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
                    pageLoad: timing.loadEventEnd - timing.navigationStart,
                    
                    // 导航类型
                    navigationType: navigation.type,
                    redirectCount: navigation.redirectCount
                };
            })();
            """
            
            timing_data = await self.client.execute_javascript(timing_script)
            return timing_data or {}
            
        except Exception as e:
            self.logger.error(f"收集导航时序失败: {e}")
            return {}
    
    def _on_load_event(self, params: Dict[str, Any]):
        """处理页面加载完成事件"""
        timestamp = params.get("timestamp", time.time())
        self.load_events["loadEventFired"] = timestamp
        self.logger.debug("页面加载完成")
    
    def _on_dom_loaded(self, params: Dict[str, Any]):
        """处理 DOM 加载完成事件"""
        timestamp = params.get("timestamp", time.time())
        self.load_events["domContentLoadedEventFired"] = timestamp
        self.logger.debug("DOM 加载完成")
    
    def reset(self):
        """重置收集器状态"""
        super().reset()
        self.timing_data = {}
        self.load_events = {} 