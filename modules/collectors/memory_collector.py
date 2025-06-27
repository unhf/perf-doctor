"""
内存使用收集器

收集 JavaScript 内存使用情况，包括堆内存使用量、内存限制等
"""

import time
import logging
from typing import Dict, Any
from .base_collector import BaseCollector


class MemoryCollector(BaseCollector):
    """内存使用收集器"""
    
    def __init__(self, devtools_client):
        super().__init__(devtools_client, "MemoryCollector")
        self.memory_data = {}
    
    def get_required_domains(self) -> list:
        """获取需要的 DevTools 域"""
        return ["Runtime"]
    
    async def setup(self) -> bool:
        """设置内存使用收集器"""
        try:
            await self.client.enable_domain("Runtime")
            self.logger.debug("内存使用收集器设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置内存使用收集器失败: {e}")
            return False
    
    async def collect(self) -> Dict[str, Any]:
        """收集内存使用数据"""
        if not self.enabled:
            return {}
        
        try:
            # 获取内存使用情况
            memory_data = await self._get_memory_usage()
            
            # 计算内存使用率
            if memory_data.get("totalJSHeapSize") and memory_data.get("usedJSHeapSize"):
                used = memory_data["usedJSHeapSize"]
                total = memory_data["totalJSHeapSize"]
                memory_data["heapUsagePercent"] = (used / total) * 100 if total > 0 else 0
            
            self.memory_data = memory_data
            self.logger.debug(f"收集到内存使用数据: {memory_data}")
            
            return {
                "type": "memory_usage",
                "data": memory_data,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"收集内存使用失败: {e}")
            return {"type": "memory_usage", "error": str(e)}
    
    async def _get_memory_usage(self) -> Dict[str, float]:
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
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取内存使用摘要"""
        if not self.memory_data:
            return {}
        
        used = self.memory_data.get("usedJSHeapSize", 0)
        total = self.memory_data.get("totalJSHeapSize", 0)
        limit = self.memory_data.get("jsHeapSizeLimit", 0)
        
        return {
            "used_mb": round(used / 1024 / 1024, 2),
            "total_mb": round(total / 1024 / 1024, 2),
            "limit_mb": round(limit / 1024 / 1024, 2),
            "usage_percent": self.memory_data.get("heapUsagePercent", 0)
        }
    
    def reset(self):
        """重置收集器状态"""
        super().reset()
        self.memory_data = {} 