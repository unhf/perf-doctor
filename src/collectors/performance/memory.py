"""
内存收集器

收集JavaScript内存使用情况
"""

import logging
from typing import Dict, Any, List

from ..base.collector import BaseCollector
from ...core.types import CollectorResult, MemoryData


class MemoryCollector(BaseCollector):
    """内存收集器"""
    
    def __init__(self, client):
        super().__init__(client, "MemoryCollector", "收集内存使用数据")
        self.memory_data = {}
    
    def get_required_domains(self) -> List[str]:
        """获取需要的DevTools域"""
        return ["Runtime"]
    
    async def setup(self) -> bool:
        """设置内存收集器"""
        try:
            await self._enable_required_domains()
            return True
        except Exception as e:
            self.logger.error(f"设置内存收集器失败: {e}")
            return False
    
    async def collect(self) -> CollectorResult:
        """收集内存数据"""
        try:
            memory_script = """
                (function() {
                    if (performance.memory) {
                        const memory = performance.memory;
                        return {
                            usedJSHeapSize: memory.usedJSHeapSize,
                            totalJSHeapSize: memory.totalJSHeapSize,
                            jsHeapSizeLimit: memory.jsHeapSizeLimit,
                            heapUsagePercent: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
                        };
                    }
                    return null;
                })();
            """
            
            memory_info = await self.client.execute_javascript(memory_script)
            
            if memory_info:
                self.memory_data = memory_info
            else:
                self.memory_data = {
                    'usedJSHeapSize': 0,
                    'totalJSHeapSize': 0,
                    'jsHeapSizeLimit': 0,
                    'heapUsagePercent': 0
                }
            
            return self._create_result(self.memory_data)
            
        except Exception as e:
            self.logger.error(f"收集内存数据失败: {e}")
            return self._create_result({}, str(e)) 