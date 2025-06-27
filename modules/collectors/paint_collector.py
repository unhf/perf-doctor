"""
绘制指标收集器

收集 First Contentful Paint (FCP)、Largest Contentful Paint (LCP) 等绘制相关指标
"""

import time
import logging
import asyncio
from typing import Dict, Any
from .base_collector import BaseCollector


class PaintCollector(BaseCollector):
    """绘制指标收集器"""
    
    def __init__(self, devtools_client):
        super().__init__(devtools_client, "PaintCollector")
        self.paint_data = {}
        self.lcp_observer_setup = False
    
    def get_required_domains(self) -> list:
        """获取需要的 DevTools 域"""
        return ["Performance"]
    
    async def setup(self) -> bool:
        """设置绘制指标收集器"""
        try:
            await self.client.enable_domain("Performance")
            
            # 在setup时就设置LCP观察器
            await self._setup_lcp_observer()
            
            self.logger.debug("绘制指标收集器设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置绘制指标收集器失败: {e}")
            return False
    
    async def _setup_lcp_observer(self):
        """设置LCP观察器，支持SPA和异步渲染页面"""
        try:
            # 检查是否支持LCP
            support_check = await self.client.execute_javascript("""
                (function() {
                    return {
                        hasPerformanceObserver: typeof PerformanceObserver !== 'undefined',
                        hasLargestContentfulPaint: PerformanceObserver && 'largest-contentful-paint' in PerformanceObserver.supportedEntryTypes
                    };
                })();
            """)
            
            if support_check and support_check.get('hasLargestContentfulPaint'):
                # 注入全局LCP监听和SPA路由变化监听
                await self.client.execute_javascript("""
                    (function() {
                        function setupLCPObserver() {
                            window.lastLCP = null;
                            if (window.lcpObserver) window.lcpObserver.disconnect();
                            window.lcpObserver = new PerformanceObserver((list) => {
                                const entries = list.getEntries();
                                const lastEntry = entries[entries.length - 1];
                                if (lastEntry) window.lastLCP = lastEntry.startTime;
                            });
                            window.lcpObserver.observe({entryTypes: ['largest-contentful-paint']});
                        }
                        setupLCPObserver();
                        // 监听SPA路由变化
                        ['pushState', 'replaceState'].forEach(fn => {
                            const orig = history[fn];
                            history[fn] = function() {
                                orig.apply(this, arguments);
                                setTimeout(setupLCPObserver, 0);
                            };
                        });
                        window.addEventListener('popstate', () => setTimeout(setupLCPObserver, 0));
                        window.addEventListener('hashchange', () => setTimeout(setupLCPObserver, 0));
                        // 可选：暴露手动触发
                        window.triggerLCPCollect = () => window.lastLCP;
                    })();
                """)
                self.lcp_observer_setup = True
                self.logger.debug("LCP观察器（SPA增强）设置成功")
            else:
                self.logger.debug("页面不支持LCP")
                
        except Exception as e:
            self.logger.debug(f"设置LCP观察器失败: {e}")
    
    async def collect(self) -> Dict[str, Any]:
        """收集绘制指标数据"""
        if not self.enabled:
            return {}
        
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
            lcp_data = await self._collect_lcp()
            if lcp_data:
                paint_data.update(lcp_data)
            
            self.paint_data = paint_data
            self.logger.debug(f"收集到绘制指标: {paint_data}")
            
            return {
                "type": "paint_metrics",
                "data": paint_data,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"收集绘制指标失败: {e}")
            return {"type": "paint_metrics", "error": str(e)}
    
    async def _collect_lcp(self) -> Dict[str, float]:
        """收集 Largest Contentful Paint 数据，支持SPA和异步渲染"""
        try:
            # 优先取window.lastLCP，必要时等待LCP事件
            if self.lcp_observer_setup:
                # 最多等待5秒，100ms轮询
                for _ in range(50):
                    lcp_time = await self.client.execute_javascript("window.lastLCP || null")
                    if lcp_time:
                        return {"largest-contentful-paint": lcp_time}
                    await asyncio.sleep(0.1)
                # 支持手动触发
                lcp_time = await self.client.execute_javascript("window.triggerLCPCollect && window.triggerLCPCollect()")
                if lcp_time:
                    return {"largest-contentful-paint": lcp_time}
            # 兜底：Performance API
            lcp_script = """
            (function() {
                try {
                    const entries = performance.getEntriesByType('largest-contentful-paint');
                    if (entries.length > 0) {
                        return entries[entries.length - 1].startTime;
                    }
                } catch (e) {}
                return null;
            })();
            """
            lcp_time = await self.client.execute_javascript(lcp_script)
            if lcp_time:
                return {"largest-contentful-paint": lcp_time}
        except Exception as e:
            self.logger.debug(f"LCP 收集失败: {e}")
        return {}
    
    def reset(self):
        """重置收集器状态"""
        super().reset()
        self.paint_data = {}
        self.lcp_observer_setup = False 