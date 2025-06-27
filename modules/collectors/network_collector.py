"""
网络请求收集器

收集网络请求相关的性能数据，包括请求数量、响应时间、资源大小等
"""

import time
import logging
from typing import Dict, Any, List
from .base_collector import BaseCollector


class NetworkCollector(BaseCollector):
    """网络请求收集器"""
    
    def __init__(self, devtools_client):
        super().__init__(devtools_client, "NetworkCollector")
        self.network_events = []
        self.request_data = {}
    
    def get_required_domains(self) -> list:
        """获取需要的 DevTools 域"""
        return ["Network"]
    
    async def setup(self) -> bool:
        """设置网络请求收集器"""
        try:
            await self.client.enable_domain("Network")
            
            # 设置事件处理器
            self.client.add_event_handler("Network.requestWillBeSent", self._on_request_sent)
            self.client.add_event_handler("Network.responseReceived", self._on_response_received)
            self.client.add_event_handler("Network.loadingFinished", self._on_loading_finished)
            self.client.add_event_handler("Network.loadingFailed", self._on_loading_failed)
            
            self.logger.debug("网络请求收集器设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置网络请求收集器失败: {e}")
            return False
    
    async def collect(self) -> Dict[str, Any]:
        """收集网络请求数据"""
        if not self.enabled:
            return {}
        
        try:
            # 获取网络请求统计
            network_stats = await self._get_network_statistics()
            
            # 获取资源加载数据
            resource_data = await self._get_resource_timing()
            
            result = {
                "type": "network_requests",
                "data": {
                    "statistics": network_stats,
                    "resources": resource_data,
                    "events": self.network_events
                },
                "timestamp": time.time()
            }
            
            self.logger.debug(f"收集到网络请求数据: {len(self.network_events)} 个事件")
            
            return result
            
        except Exception as e:
            self.logger.error(f"收集网络请求失败: {e}")
            return {"type": "network_requests", "error": str(e)}
    
    async def _get_network_statistics(self) -> Dict[str, Any]:
        """获取网络请求统计信息"""
        try:
            stats_script = """
            (function() {
                const entries = performance.getEntriesByType('resource');
                const stats = {
                    totalRequests: entries.length,
                    totalSize: 0,
                    avgResponseTime: 0,
                    requestsByType: {},
                    requestsByDomain: {}
                };
                
                let totalTime = 0;
                
                entries.forEach(entry => {
                    // 计算总大小
                    if (entry.transferSize) {
                        stats.totalSize += entry.transferSize;
                    }
                    
                    // 计算响应时间
                    const responseTime = entry.responseEnd - entry.responseStart;
                    totalTime += responseTime;
                    
                    // 按类型统计
                    const type = entry.initiatorType || 'unknown';
                    stats.requestsByType[type] = (stats.requestsByType[type] || 0) + 1;
                    
                    // 按域名统计
                    try {
                        const domain = new URL(entry.name).hostname;
                        stats.requestsByDomain[domain] = (stats.requestsByDomain[domain] || 0) + 1;
                    } catch (e) {
                        // 忽略无效URL
                    }
                });
                
                if (entries.length > 0) {
                    stats.avgResponseTime = totalTime / entries.length;
                }
                
                return stats;
            })();
            """
            
            stats = await self.client.execute_javascript(stats_script)
            return stats or {}
            
        except Exception as e:
            self.logger.error(f"获取网络统计失败: {e}")
            return {}
    
    async def _get_resource_timing(self) -> List[Dict[str, Any]]:
        """获取资源加载时序数据"""
        try:
            resource_script = """
            (function() {
                const entries = performance.getEntriesByType('resource');
                return entries.map(entry => ({
                    name: entry.name,
                    entryType: entry.entryType,
                    initiatorType: entry.initiatorType,
                    startTime: entry.startTime,
                    duration: entry.duration,
                    transferSize: entry.transferSize,
                    encodedBodySize: entry.encodedBodySize,
                    decodedBodySize: entry.decodedBodySize,
                    responseStart: entry.responseStart,
                    responseEnd: entry.responseEnd
                }));
            })();
            """
            
            resources = await self.client.execute_javascript(resource_script)
            return resources or []
            
        except Exception as e:
            self.logger.error(f"获取资源时序失败: {e}")
            return []
    
    def _on_request_sent(self, params: Dict[str, Any]):
        """处理请求发送事件"""
        request_id = params.get("requestId")
        if request_id:
            self.request_data[request_id] = {
                "requestId": request_id,
                "url": params.get("request", {}).get("url"),
                "method": params.get("request", {}).get("method"),
                "timestamp": time.time(),
                "type": "request_sent"
            }
            self.network_events.append(self.request_data[request_id])
    
    def _on_response_received(self, params: Dict[str, Any]):
        """处理响应接收事件"""
        request_id = params.get("requestId")
        if request_id and request_id in self.request_data:
            self.request_data[request_id].update({
                "status": params.get("response", {}).get("status"),
                "mimeType": params.get("response", {}).get("mimeType"),
                "responseTimestamp": time.time(),
                "type": "response_received"
            })
    
    def _on_loading_finished(self, params: Dict[str, Any]):
        """处理加载完成事件"""
        request_id = params.get("requestId")
        if request_id and request_id in self.request_data:
            self.request_data[request_id].update({
                "encodedDataLength": params.get("encodedDataLength"),
                "finishTimestamp": time.time(),
                "type": "loading_finished"
            })
    
    def _on_loading_failed(self, params: Dict[str, Any]):
        """处理加载失败事件"""
        request_id = params.get("requestId")
        if request_id and request_id in self.request_data:
            self.request_data[request_id].update({
                "errorText": params.get("errorText"),
                "failTimestamp": time.time(),
                "type": "loading_failed"
            })
    
    def reset(self):
        """重置收集器状态"""
        super().reset()
        self.network_events = []
        self.request_data = {} 