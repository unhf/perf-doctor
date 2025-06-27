"""
网络请求收集器

收集网络请求相关的性能数据，包括请求数量、响应时间、资源大小等
增强版本：采集所有资源的详细信息（method、status、headers、body等）
"""

import time
import logging
import json
import asyncio
from typing import Dict, Any, List
from .base_collector import BaseCollector


class NetworkCollector(BaseCollector):
    """网络请求收集器"""
    
    def __init__(self, devtools_client):
        super().__init__(devtools_client, "NetworkCollector")
        self.network_events = []
        self.request_data = {}
        self.resource_analysis = {
            "large_resources": [],
            "slow_requests": [],
            "api_requests": [],
            "static_resources": [],
            "third_party_resources": []
        }
    
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
        try:
            # 获取增强的资源时序数据（只用增强结果，不再用JS统计）
            resources = await self._get_enhanced_resource_timing()
            
            # 分析资源
            await self._analyze_resources(resources)
            
            # 统计信息全部基于增强资源分析
            api_count = len([r for r in resources if r.get("isApi", False)])
            static_count = len([r for r in resources if r.get("isStatic", False)])
            third_party_count = len([r for r in resources if r.get("isThirdParty", False)])
            total_size = sum(r.get("transferSize", 0) for r in resources)
            response_times = [r.get("responseTime", 0) for r in resources if r.get("responseTime", 0) > 0]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            requests_by_type = {}
            requests_by_domain = {}
            for r in resources:
                initiator_type = r.get("initiatorType", "unknown")
                requests_by_type[initiator_type] = requests_by_type.get(initiator_type, 0) + 1
                domain = r.get("domain", "unknown")
                requests_by_domain[domain] = requests_by_domain.get(domain, 0) + 1
            statistics = {
                "totalRequests": len(resources),
                "totalSize": total_size,
                "avgResponseTime": avg_response_time,
                "apiRequests": api_count,
                "staticRequests": static_count,
                "thirdPartyRequests": third_party_count,
                "requestsByType": requests_by_type,
                "requestsByDomain": requests_by_domain
            }
            return {
                "type": "network_requests",
                "data": {
                    "statistics": statistics,
                    "resources": resources,
                    "analysis": self.resource_analysis
                }
            }
        except Exception as e:
            self.logger.error(f"收集网络数据失败: {e}")
            return {
                "type": "network_requests",
                "data": {
                    "statistics": {},
                    "resources": [],
                    "analysis": {}
                }
            }
    
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
                    requestsByDomain: {},
                    requestsByProtocol: {},
                    apiRequests: 0,
                    staticRequests: 0,
                    thirdPartyRequests: 0
                };
                
                let totalTime = 0;
                const currentDomain = window.location.hostname;
                
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
                        const url = new URL(entry.name);
                        const domain = url.hostname;
                        stats.requestsByDomain[domain] = (stats.requestsByDomain[domain] || 0) + 1;
                        
                        // 统计第三方请求
                        if (domain !== currentDomain) {
                            stats.thirdPartyRequests++;
                        }
                        
                        // 统计API请求
                        if (url.pathname.includes('/api/') || url.pathname.includes('/rest/') || 
                            url.pathname.includes('/graphql') || url.pathname.includes('/v1/') ||
                            url.pathname.includes('/v2/') || url.pathname.includes('/v3/')) {
                            stats.apiRequests++;
                        } else if (['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot'].some(ext => url.pathname.includes(ext))) {
                            stats.staticRequests++;
                        }
                        
                        // 按协议统计
                        const protocol = url.protocol.replace(':', '');
                        stats.requestsByProtocol[protocol] = (stats.requestsByProtocol[protocol] || 0) + 1;
                        
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
    
    async def _get_enhanced_resource_timing(self) -> List[Dict[str, Any]]:
        """获取增强的资源加载时序数据（包含详细信息）"""
        try:
            # 合并 DevTools 事件数据和 Performance API 数据
            enhanced_resources = []
            
            # 处理所有收集到的请求数据
            for request_id, request_info in self.request_data.items():
                if request_info.get("type") == "loading_finished":
                    # 构建完整的资源信息
                    resource_info = {
                        "requestId": request_id,
                        "url": request_info.get("url", ""),
                        "method": request_info.get("method", "GET"),
                        "status": request_info.get("status", 0),
                        "mimeType": request_info.get("mimeType", ""),
                        "transferSize": request_info.get("encodedDataLength", 0),
                        "responseTime": request_info.get("responseTime", 0),
                        "requestHeaders": request_info.get("requestHeaders", {}),
                        "responseHeaders": request_info.get("responseHeaders", {}),
                        "requestBody": request_info.get("requestBody", ""),
                        "responseBody": request_info.get("responseBody", ""),
                        "errorText": request_info.get("errorText", ""),
                        "timestamp": request_info.get("timestamp", 0)
                    }
                    
                    # 解析域名和类型
                    try:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(resource_info["url"])
                        resource_info["domain"] = parsed_url.netloc
                        
                        # 判断资源类型
                        path = parsed_url.path.lower()
                        domain = parsed_url.netloc.lower()
                        query = parsed_url.query.lower()
                        
                        # 优先判断静态资源
                        static_exts = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.ogg', '.wav', '.json', '.map']
                        is_static = any(path.endswith(ext) for ext in static_exts)
                        mime_type = resource_info.get("mimeType", "").lower()
                        static_mimes = ['image/', 'font/', 'audio/', 'video/', 'application/javascript', 'text/css']
                        is_static = is_static or any(mime_type.startswith(m) for m in static_mimes)
                        resource_info["isStatic"] = is_static

                        # 只有非静态资源才考虑API
                        is_api = False
                        api_features = []
                        initiator_type = resource_info.get("initiatorType", "").lower()
                        method = resource_info.get("method", "GET").upper()
                        
                        # 只考虑XHR、fetch或POST/PUT/DELETE/PATCH
                        if (initiator_type in ["xhr", "fetch"] or method in ["POST", "PUT", "DELETE", "PATCH"]):
                            # 1. 路径特征
                            api_paths = ['/api/', '/rest/', '/graphql', '/v1/', '/v2/', '/v3/', '/api', '/service', '/data', '/endpoint']
                            if any(api_path in path for api_path in api_paths):
                                api_features.append('api_path')
                            # 2. 查询参数特征
                            api_params = ['functionid', 'appid', 'action', 'method', 'operation', 'cmd', 'service', 'api_key', 'token']
                            if any(param in query for param in api_params):
                                api_features.append('api_params')
                            # 3. MIME类型特征
                            if any(api_mime in mime_type for api_mime in ['json', 'xml', 'text/plain']):
                                api_features.append('api_mime')
                            # 4. 域名特征
                            if any(keyword in domain for keyword in ['api', 'rest', 'service', 'data', 'backend']):
                                api_features.append('api_domain')
                            # 5. 响应大小特征
                            transfer_size = resource_info.get("transferSize", 0)
                            if 0 < transfer_size < 10240:
                                api_features.append('api_size')
                            # 满足2个及以上特征才算API
                            if len(api_features) >= 2:
                                is_api = True
                        resource_info["isApi"] = is_api
                        if is_api:
                            self.logger.debug(f"识别为API: {resource_info['url']}, 特征: {api_features}")
                        resource_info["isThirdParty"] = parsed_url.netloc != urlparse(self.client.page_url).netloc if hasattr(self.client, 'page_url') else False
                        
                        # 设置资源分类
                        if resource_info["isApi"]:
                            resource_info["category"] = "API"
                        elif resource_info["isStatic"]:
                            resource_info["category"] = "Static"
                        elif resource_info["isThirdParty"]:
                            resource_info["category"] = "Third-party"
                        else:
                            resource_info["category"] = "Other"
                            
                    except Exception as e:
                        self.logger.debug(f"解析URL失败: {e}")
                        resource_info["domain"] = ""
                        resource_info["isApi"] = False
                        resource_info["isStatic"] = False
                        resource_info["isThirdParty"] = False
                        resource_info["category"] = "Other"
                    
                    enhanced_resources.append(resource_info)
            
            return enhanced_resources
            
        except Exception as e:
            self.logger.error(f"获取增强资源时序失败: {e}")
            return []
    
    async def _analyze_resources(self, resources: List[Dict[str, Any]]):
        """分析资源请求，识别大文件和慢请求"""
        try:
            # 分析大资源（超过500KB）
            large_threshold = 500 * 1024  # 500KB
            self.resource_analysis["large_resources"] = [
                resource for resource in resources
                if resource.get("transferSize", 0) > large_threshold
            ]
            
            # 分析慢请求（响应时间超过1秒）
            slow_threshold = 1000  # 1秒
            self.resource_analysis["slow_requests"] = [
                resource for resource in resources
                if resource.get("responseTime", 0) > slow_threshold
            ]
            
            # 分析API请求
            self.resource_analysis["api_requests"] = [
                resource for resource in resources
                if resource.get("isApi", False)
            ]
            
            # 分析静态资源
            self.resource_analysis["static_resources"] = [
                resource for resource in resources
                if resource.get("isStatic", False)
            ]
            
            # 分析第三方资源
            self.resource_analysis["third_party_resources"] = [
                resource for resource in resources
                if resource.get("isThirdParty", False)
            ]
            
            # 按大小排序
            self.resource_analysis["large_resources"].sort(
                key=lambda x: x.get("transferSize", 0), reverse=True
            )
            
            # 按响应时间排序
            self.resource_analysis["slow_requests"].sort(
                key=lambda x: x.get("responseTime", 0), reverse=True
            )
            
            self.logger.debug(f"资源分析完成: 大资源{len(self.resource_analysis['large_resources'])}个, "
                            f"慢请求{len(self.resource_analysis['slow_requests'])}个, "
                            f"API请求{len(self.resource_analysis['api_requests'])}个")
            
        except Exception as e:
            self.logger.error(f"分析资源失败: {e}")
    
    def _on_request_sent(self, params: Dict[str, Any]):
        """处理请求发送事件"""
        request_id = params.get("requestId")
        if request_id:
            request = params.get("request", {})
            self.request_data[request_id] = {
                "requestId": request_id,
                "url": request.get("url"),
                "method": request.get("method", "GET"),
                "requestHeaders": request.get("headers", {}),
                "requestBody": request.get("postData", ""),
                "timestamp": time.time(),
                "type": "request_sent"
            }
            self.network_events.append(self.request_data[request_id])
    
    def _on_response_received(self, params: Dict[str, Any]):
        """处理响应接收事件"""
        request_id = params.get("requestId")
        if request_id and request_id in self.request_data:
            response = params.get("response", {})
            self.request_data[request_id].update({
                "status": response.get("status"),
                "mimeType": response.get("mimeType"),
                "responseHeaders": response.get("headers", {}),
                "responseTimestamp": time.time(),
                "type": "response_received"
            })
            
            # 计算响应时间
            if "timestamp" in self.request_data[request_id]:
                self.request_data[request_id]["responseTime"] = (
                    time.time() - self.request_data[request_id]["timestamp"]
                ) * 1000  # 转换为毫秒
    
    def _on_loading_finished(self, params: Dict[str, Any]):
        """处理加载完成事件"""
        request_id = params.get("requestId")
        if request_id and request_id in self.request_data:
            self.request_data[request_id].update({
                "encodedDataLength": params.get("encodedDataLength", 0),
                "finishTimestamp": time.time(),
                "type": "loading_finished"
            })
            
            # 异步获取响应体内容（仅对文本类型）
            try:
                mime_type = self.request_data[request_id].get("mimeType", "")
                if any(text_type in mime_type.lower() for text_type in ["json", "text", "xml", "html", "javascript", "css"]):
                    # 创建异步任务获取响应体
                    asyncio.create_task(self._get_response_body_async(request_id))
            except Exception as e:
                self.logger.debug(f"获取响应体失败: {e}")
    
    def _on_loading_failed(self, params: Dict[str, Any]):
        """处理加载失败事件"""
        request_id = params.get("requestId")
        if request_id and request_id in self.request_data:
            self.request_data[request_id].update({
                "errorText": params.get("errorText"),
                "failTimestamp": time.time(),
                "type": "loading_failed"
            })
    
    async def _get_response_body(self, request_id: str) -> str:
        """获取响应体内容"""
        try:
            # 使用 DevTools Protocol 获取响应体
            response = await self.client.send_command("Network.getResponseBody", {
                "requestId": request_id
            })
            
            if response and "body" in response:
                body = response["body"]
                # 限制响应体大小，避免内存问题
                if len(body) > 2048:  # 2KB
                    return body[:2048] + "\n... (内容已截断)"
                return body
            
        except Exception as e:
            self.logger.debug(f"获取响应体失败: {e}")
        
        return ""
    
    async def _get_response_body_async(self, request_id: str):
        """异步获取响应体内容"""
        try:
            response_body = await self._get_response_body(request_id)
            if response_body and request_id in self.request_data:
                self.request_data[request_id]["responseBody"] = response_body
        except Exception as e:
            self.logger.debug(f"异步获取响应体失败: {e}")
    
    def reset(self):
        """重置收集器状态"""
        super().reset()
        self.network_events = []
        self.request_data = {}
        self.resource_analysis = {
            "large_resources": [],
            "slow_requests": [],
            "api_requests": [],
            "static_resources": [],
            "third_party_resources": []
        } 