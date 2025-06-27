"""
绘制指标收集器

收集 First Contentful Paint (FCP)、Largest Contentful Paint (LCP) 等绘制相关指标
"""

import time
import logging
from typing import Dict, Any
from .base_collector import BaseCollector


class PaintCollector(BaseCollector):
    """绘制指标收集器"""
    
    def __init__(self, devtools_client):
        super().__init__(devtools_client, "PaintCollector")
        self.paint_data = {}
    
    def get_required_domains(self) -> list:
        """获取需要的 DevTools 域"""
        return ["Performance"]
    
    async def setup(self) -> bool:
        """设置绘制指标收集器"""
        try:
            await self.client.enable_domain("Performance")
            self.logger.debug("绘制指标收集器设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置绘制指标收集器失败: {e}")
            return False
    
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
        """收集 Largest Contentful Paint 数据"""
        try:
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