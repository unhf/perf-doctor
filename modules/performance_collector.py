"""
性能数据收集模块

负责收集页面性能指标，包括加载时间、FCP、LCP 等关键指标
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from .devtools_client import DevToolsClient

class PerformanceCollector:
    """性能数据收集器"""
    
    def __init__(self, devtools_client: DevToolsClient):
        """
        初始化性能收集器
        
        Args:
            devtools_client: DevTools 客户端实例
        """
        self.client = devtools_client
        self.performance_data = {}
        self.paint_events = []
        self.network_events = []
        self.logger = logging.getLogger(__name__)
        
        # 设置事件处理器
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        self.client.add_event_handler("Performance.metrics", self._on_performance_metrics)
        self.client.add_event_handler("Page.loadEventFired", self._on_load_event)
        self.client.add_event_handler("Page.domContentLoadedEventFired", self._on_dom_loaded)
    
    def _on_performance_metrics(self, params: Dict[str, Any]):
        """处理性能指标事件"""
        metrics = params.get("metrics", [])
        for metric in metrics:
            name = metric.get("name")
            value = metric.get("value")
            if name and value is not None:
                self.performance_data[name] = value
        self.logger.debug(f"收到性能指标: {len(metrics)} 项")
    
    def _on_load_event(self, params: Dict[str, Any]):
        """处理页面加载完成事件"""
        timestamp = params.get("timestamp", time.time())
        self.performance_data["load_timestamp"] = timestamp
        self.logger.debug("页面加载完成")
    
    def _on_dom_loaded(self, params: Dict[str, Any]):
        """处理 DOM 加载完成事件"""
        timestamp = params.get("timestamp", time.time())
        self.performance_data["dom_loaded_timestamp"] = timestamp
        self.logger.debug("DOM 加载完成")
    
    async def collect_performance_data(self, url: str, wait_time: int = 5) -> Dict[str, Any]:
        """
        收集指定页面的性能数据
        
        Args:
            url: 目标页面URL
            wait_time: 等待时间（秒）
            
        Returns:
            性能数据字典
        """
        self.logger.info(f"开始收集性能数据: {url}")
        
        # 清理之前的数据
        self.performance_data = {}
        self.paint_events = []
        self.network_events = []
        
        try:
            # 启用必要的域
            await self._enable_required_domains()
            
            # 开始性能追踪
            start_time = time.time()
            await self.client.send_command("Performance.enable")
            
            # 导航到目标页面
            if not await self.client.navigate_to(url):
                raise Exception(f"导航失败: {url}")
            
            # 等待页面加载
            await asyncio.sleep(wait_time)
            
            # 收集性能指标
            performance_metrics = await self._collect_performance_metrics()
            paint_metrics = await self._collect_paint_metrics()
            navigation_metrics = await self._collect_navigation_timing()
            
            # 合并所有数据
            result = {
                "url": url,
                "timestamp": start_time,
                "load_time": time.time() - start_time,
                "performance_metrics": performance_metrics,
                "paint_metrics": paint_metrics,
                "navigation_timing": navigation_metrics,
                "raw_data": self.performance_data
            }
            
            self.logger.info(f"性能数据收集完成: {url}")
            return result
            
        except Exception as e:
            self.logger.error(f"收集性能数据失败: {e}")
            return {"url": url, "error": str(e)}
    
    async def _enable_required_domains(self):
        """启用收集性能数据所需的域"""
        domains = ["Performance", "Page", "Runtime", "Network"]
        for domain in domains:
            await self.client.enable_domain(domain)
    
    async def _collect_performance_metrics(self) -> Dict[str, float]:
        """收集 Performance API 指标"""
        try:
            response = await self.client.send_command("Performance.getMetrics")
            if not response or "metrics" not in response:
                return {}
            
            metrics = {}
            for metric in response["metrics"]:
                name = metric.get("name")
                value = metric.get("value")
                if name and value is not None:
                    metrics[name] = value
            
            self.logger.debug(f"收集到 {len(metrics)} 个性能指标")
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集性能指标失败: {e}")
            return {}
    
    async def _collect_paint_metrics(self) -> Dict[str, float]:
        """收集绘制相关指标（FCP, LCP 等）"""
        try:
            # 获取 Paint Timing API 数据
            paint_script = """
            (function() {
                const paintEntries = performance.getEntriesByType('paint');
                const result = {};
                paintEntries.forEach(entry => {
                    result[entry.name] = entry.startTime;
                });
                return result;
            })();
            """
            
            paint_data = await self.client.execute_javascript(paint_script)
            if not paint_data:
                paint_data = {}
            
            # 获取 LCP 数据
            lcp_script = """
            (function() {
                return new Promise((resolve) => {
                    const observer = new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        const lastEntry = entries[entries.length - 1];
                        resolve(lastEntry ? lastEntry.startTime : null);
                    });
                    observer.observe({entryTypes: ['largest-contentful-paint']});
                    
                    // 超时处理
                    setTimeout(() => resolve(null), 3000);
                });
            })();
            """
            
            try:
                lcp_time = await self.client.execute_javascript(lcp_script)
                if lcp_time:
                    paint_data["largest-contentful-paint"] = lcp_time
            except Exception as e:
                self.logger.debug(f"LCP 收集失败: {e}")
            
            self.logger.debug(f"收集到绘制指标: {paint_data}")
            return paint_data
            
        except Exception as e:
            self.logger.error(f"收集绘制指标失败: {e}")
            return {}
    
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
            if not timing_data:
                timing_data = {}
            
            self.logger.debug(f"收集到导航时序数据")
            return timing_data
            
        except Exception as e:
            self.logger.error(f"收集导航时序失败: {e}")
            return {}
    
    async def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        try:
            memory_script = """
            (function() {
                if (performance.memory) {
                    return {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize,
                        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                    };
                }
                return {};
            })();
            """
            
            memory_data = await self.client.execute_javascript(memory_script)
            return memory_data or {}
            
        except Exception as e:
            self.logger.error(f"获取内存使用失败: {e}")
            return {}
    
    def reset(self):
        """重置收集器状态"""
        self.performance_data = {}
        self.paint_events = []
        self.network_events = []
        self.logger.debug("重置性能收集器")
