"""
网络收集器

收集网络请求数据
"""

import logging
from typing import Dict, Any, List

from ..base.collector import BaseCollector
from ...core.types import CollectorResult, NetworkRequest


class NetworkCollector(BaseCollector):
    """网络收集器"""
    
    def __init__(self, client):
        super().__init__(client, "NetworkCollector", "收集网络请求数据")
        self.requests = []
        self.statistics = {}
    
    def get_required_domains(self) -> List[str]:
        """获取需要的DevTools域"""
        return ["Network"]
    
    async def setup(self) -> bool:
        """设置网络收集器"""
        try:
            await self._enable_required_domains()
            return True
        except Exception as e:
            self.logger.error(f"设置网络收集器失败: {e}")
            return False
    
    async def collect(self) -> CollectorResult:
        """收集网络数据"""
        try:
            # 简化版本，实际应该监听网络事件
            network_script = """
                (function() {
                    const resources = performance.getEntriesByType('resource');
                    return resources.map(resource => ({
                        name: resource.name,
                        entryType: resource.entryType,
                        startTime: resource.startTime,
                        duration: resource.duration,
                        transferSize: resource.transferSize,
                        encodedBodySize: resource.encodedBodySize,
                        decodedBodySize: resource.decodedBodySize
                    }));
                })();
            """
            
            resources = await self.client.execute_javascript(network_script)
            
            if resources:
                self.requests = resources
                self.statistics = {
                    'totalRequests': len(resources),
                    'totalSize': sum(r.get('transferSize', 0) for r in resources),
                    'averageDuration': sum(r.get('duration', 0) for r in resources) / len(resources) if resources else 0
                }
            
            return self._create_result({
                'requests': self.requests,
                'statistics': self.statistics
            })
            
        except Exception as e:
            self.logger.error(f"收集网络数据失败: {e}")
            return self._create_result({}, str(e)) 