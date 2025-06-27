"""
性能报告生成模块

负责分析性能数据并生成格式化的报告，包括性能评分和优化建议
"""

import json
import logging
import os
from datetime import datetime
from jinja2 import Template, Environment, FileSystemLoader
import base64
from typing import Dict, Any, List, Tuple
from .network_report_generator import NetworkReportGenerator
import sys

from .collectors.performance_metrics_collector import PerformanceMetricsCollector
from .collectors.memory_collector import MemoryCollector
from .collectors.navigation_collector import NavigationCollector
from .collectors.network_collector import NetworkCollector
from .collectors.paint_collector import PaintCollector

class ReportGenerator:
    """性能报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.logger = logging.getLogger(__name__)
        self.network_report_generator = NetworkReportGenerator()
        
        # 初始化 Jinja2 环境，支持打包后的路径
        try:
            # 尝试从当前目录的 templates 文件夹加载
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
            if os.path.exists(template_dir):
                self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
            else:
                # 打包后的路径：从可执行文件所在目录加载
                if getattr(sys, 'frozen', False):
                    # 打包后的路径
                    base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
                    template_dir = os.path.join(base_path, 'templates')
                else:
                    # 开发环境路径
                    template_dir = os.path.join(os.getcwd(), 'templates')
                
                self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
                
        except Exception as e:
            self.logger.error(f"初始化 Jinja2 环境失败: {e}")
            # 如果模板加载失败，使用字符串模板作为备选方案
            self.jinja_env = None
        
        # 性能阈值配置（毫秒）
        self.thresholds = {
            "fcp": {"good": 1800, "poor": 3000},      # First Contentful Paint
            "lcp": {"good": 2500, "poor": 4000},      # Largest Contentful Paint
            "ttfb": {"good": 200, "poor": 600},       # Time to First Byte
            "dom_ready": {"good": 2000, "poor": 4000}, # DOM Ready
            "page_load": {"good": 3000, "poor": 5000}  # Page Load
        }
    
    def generate_report(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成性能分析报告
        
        Args:
            performance_data: 性能数据
            
        Returns:
            格式化的性能报告
        """
        if "error" in performance_data:
            return self._generate_error_report(performance_data)
        
        try:
            # 提取关键指标
            key_metrics = self._extract_key_metrics(performance_data)
            
            # 计算性能评分
            scores = self._calculate_scores(key_metrics)
            
            # 生成优化建议
            recommendations = self._generate_recommendations(key_metrics, scores)
            
            # 提取网络请求详细分析
            network_analysis = self._extract_network_analysis(performance_data)
            
            # 构建完整报告
            report = {
                "url": performance_data.get("url", "Unknown"),
                "timestamp": performance_data.get("timestamp", datetime.now().timestamp()),
                "test_date": datetime.fromtimestamp(
                    performance_data.get("timestamp", datetime.now().timestamp())
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "load_time": performance_data.get("load_time", 0),
                "key_metrics": key_metrics,
                "scores": scores,
                "overall_score": self._calculate_overall_score(scores),
                "recommendations": recommendations,
                "network_analysis": network_analysis,
                "raw_data": performance_data
            }
            
            self.logger.info(f"生成性能报告: {report['url']}")
            return report
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            return self._generate_error_report({"url": performance_data.get("url"), "error": str(e)})
    
    def _extract_key_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """提取关键性能指标"""
        metrics = {}
        
        # 处理新的插件化数据结构
        if "performance_data" in data:
            # 新的插件化架构数据结构
            performance_data = data["performance_data"]
            
            # 从收集器数据中提取指标
            if "data" in performance_data:
                collector_data = performance_data["data"]
                
                # 从 PaintCollector 中提取绘制指标
                if "PaintCollector" in collector_data:
                    paint_data = collector_data["PaintCollector"].get("data", {})
                    if "first-contentful-paint" in paint_data:
                        metrics["fcp"] = paint_data["first-contentful-paint"]
                    if "largest-contentful-paint" in paint_data:
                        metrics["lcp"] = paint_data["largest-contentful-paint"]
                
                # 从 NavigationCollector 中提取导航时序
                if "NavigationCollector" in collector_data:
                    nav_data = collector_data["NavigationCollector"].get("data", {})
                    if nav_data:
                        metrics["ttfb"] = nav_data.get("ttfb", 0)
                        metrics["dom_ready"] = nav_data.get("domReady", 0)
                        metrics["page_load"] = nav_data.get("pageLoad", 0)
                        metrics["dns_lookup"] = nav_data.get("dnsLookup", 0)
                        metrics["tcp_connect"] = nav_data.get("tcpConnect", 0)
                
                # 从 PerformanceCollector 中提取性能指标
                if "PerformanceMetricsCollector" in collector_data:
                    perf_data = collector_data["PerformanceMetricsCollector"].get("data", {})
                    for key, value in perf_data.items():
                        if key not in metrics and isinstance(value, (int, float)):
                            metrics[key] = value
                
                # 从 MemoryCollector 中提取内存指标
                if "MemoryCollector" in collector_data:
                    memory_data = collector_data["MemoryCollector"].get("data", {})
                    if memory_data:
                        metrics["memory_used"] = memory_data.get("usedJSHeapSize", 0)
                        metrics["memory_total"] = memory_data.get("totalJSHeapSize", 0)
                        metrics["memory_limit"] = memory_data.get("jsHeapSizeLimit", 0)
                
                # 从 NetworkCollector 中提取网络指标
                if "NetworkCollector" in collector_data:
                    network_data = collector_data["NetworkCollector"].get("data", {})
                    if network_data:
                        stats = network_data.get("statistics", {})
                        metrics["total_requests"] = stats.get("totalRequests", 0)
                        metrics["total_size"] = stats.get("totalSize", 0)
                        metrics["avg_response_time"] = stats.get("avgResponseTime", 0)
                        metrics["api_requests"] = stats.get("apiRequests", 0)
                        metrics["third_party_requests"] = stats.get("thirdPartyRequests", 0)
        
        # 兼容旧的数据结构格式
        else:
            # 从绘制指标中提取
            paint_metrics = data.get("paint_metrics", {})
            if "first-contentful-paint" in paint_metrics:
                metrics["fcp"] = paint_metrics["first-contentful-paint"]
            if "largest-contentful-paint" in paint_metrics:
                metrics["lcp"] = paint_metrics["largest-contentful-paint"]
            
            # 从导航时序中提取
            nav_timing = data.get("navigation_timing", {})
            if nav_timing:
                metrics["ttfb"] = nav_timing.get("ttfb", 0)
                metrics["dom_ready"] = nav_timing.get("domReady", 0)
                metrics["page_load"] = nav_timing.get("pageLoad", 0)
                metrics["dns_lookup"] = nav_timing.get("dnsLookup", 0)
                metrics["tcp_connect"] = nav_timing.get("tcpConnect", 0)
            
            # 从性能指标中补充
            perf_metrics = data.get("performance_metrics", {})
            for key, value in perf_metrics.items():
                if key not in metrics and isinstance(value, (int, float)):
                    metrics[key] = value
        
        self.logger.debug(f"提取到 {len(metrics)} 个关键指标: {list(metrics.keys())}")
        return metrics
    
    def _calculate_scores(self, metrics: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """计算各项性能评分"""
        scores = {}
        
        for metric_name, value in metrics.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]
                score_info = self._calculate_metric_score(value, threshold)
                scores[metric_name] = score_info
        
        return scores
    
    def _calculate_metric_score(self, value: float, threshold: Dict[str, float]) -> Dict[str, Any]:
        """计算单个指标的评分"""
        good_threshold = threshold["good"]
        poor_threshold = threshold["poor"]
        
        if value <= good_threshold:
            rating = "good"
            score = 90 + (good_threshold - value) / good_threshold * 10
        elif value <= poor_threshold:
            rating = "needs_improvement"
            score = 50 + (poor_threshold - value) / (poor_threshold - good_threshold) * 40
        else:
            rating = "poor"
            score = max(0, 50 - (value - poor_threshold) / poor_threshold * 50)
        
        return {
            "value": value,
            "score": min(100, max(0, score)),
            "rating": rating,
            "threshold_good": good_threshold,
            "threshold_poor": poor_threshold
        }
    
    def _calculate_overall_score(self, scores: Dict[str, Dict[str, Any]]) -> float:
        """计算综合评分"""
        if not scores:
            return 0.0
        
        # 权重配置
        weights = {
            "fcp": 0.25,
            "lcp": 0.25,
            "ttfb": 0.20,
            "dom_ready": 0.15,
            "page_load": 0.15
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric_name, score_info in scores.items():
            weight = weights.get(metric_name, 0.1)
            total_score += score_info["score"] * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_recommendations(self, metrics: Dict[str, float], 
                                scores: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
        """生成优化建议"""
        recommendations = []
        
        # FCP 优化建议
        if "fcp" in scores and scores["fcp"]["rating"] != "good":
            recommendations.append({
                "category": "First Contentful Paint",
                "priority": "high" if scores["fcp"]["rating"] == "poor" else "medium",
                "issue": f"首次内容绘制时间为 {scores['fcp']['value']:.0f}ms，需要优化",
                "suggestions": [
                    "优化关键渲染路径，减少阻塞资源",
                    "压缩和优化 CSS、JavaScript 文件",
                    "使用 CDN 加速静态资源加载",
                    "启用服务器端渲染或预渲染"
                ]
            })
        
        # LCP 优化建议
        if "lcp" in scores and scores["lcp"]["rating"] != "good":
            recommendations.append({
                "category": "Largest Contentful Paint",
                "priority": "high" if scores["lcp"]["rating"] == "poor" else "medium",
                "issue": f"最大内容绘制时间为 {scores['lcp']['value']:.0f}ms，需要优化",
                "suggestions": [
                    "优化图片加载，使用适当的格式和尺寸",
                    "预加载关键资源",
                    "优化服务器响应时间",
                    "避免大型布局偏移"
                ]
            })
        
        # TTFB 优化建议
        if "ttfb" in scores and scores["ttfb"]["rating"] != "good":
            recommendations.append({
                "category": "Time to First Byte",
                "priority": "high",
                "issue": f"首字节时间为 {scores['ttfb']['value']:.0f}ms，服务器响应较慢",
                "suggestions": [
                    "优化服务器性能和数据库查询",
                    "使用缓存策略",
                    "选择更好的服务器或托管服务",
                    "优化网络连接"
                ]
            })
        
        # DOM Ready 优化建议
        if "dom_ready" in scores and scores["dom_ready"]["rating"] != "good":
            recommendations.append({
                "category": "DOM Ready Time",
                "priority": "medium",
                "issue": f"DOM 准备时间为 {scores['dom_ready']['value']:.0f}ms，需要优化",
                "suggestions": [
                    "减少 DOM 复杂度",
                    "异步加载非关键 JavaScript",
                    "优化 CSS 加载顺序",
                    "使用代码分割技术"
                ]
            })
        
        # Page Load 优化建议
        if "page_load" in scores and scores["page_load"]["rating"] != "good":
            recommendations.append({
                "category": "Page Load Time",
                "priority": "medium",
                "issue": f"页面加载时间为 {scores['page_load']['value']:.0f}ms，整体性能需要提升",
                "suggestions": [
                    "压缩和优化所有资源",
                    "启用 Gzip 压缩",
                    "减少 HTTP 请求数量",
                    "使用浏览器缓存"
                ]
            })
        
        # 网络相关建议
        dns_time = metrics.get("dns_lookup", 0)
        if dns_time > 100:
            recommendations.append({
                "category": "DNS Lookup",
                "priority": "low",
                "issue": f"DNS 查询时间为 {dns_time:.0f}ms，可以优化",
                "suggestions": [
                    "使用更快的 DNS 服务器",
                    "启用 DNS 预解析",
                    "减少外部域名引用"
                ]
            })
        
        tcp_time = metrics.get("tcp_connect", 0)
        if tcp_time > 100:
            recommendations.append({
                "category": "TCP Connection",
                "priority": "low",
                "issue": f"TCP 连接时间为 {tcp_time:.0f}ms，可以优化",
                "suggestions": [
                    "启用 HTTP/2 或 HTTP/3",
                    "使用 CDN 减少连接距离",
                    "启用 Keep-Alive 连接"
                ]
            })
        
        # 网络请求分析建议
        network_recommendations = self._generate_network_recommendations(metrics)
        # 过滤掉内容为空的建议
        for rec in network_recommendations:
            if rec.get("issue") and rec.get("suggestions"):
                recommendations.append(rec)
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        # 过滤掉suggestions为空的建议
        recommendations = [rec for rec in recommendations if rec.get("suggestions") and any(s.strip() for s in rec["suggestions"])]
        
        return recommendations
    
    def _generate_network_recommendations(self, metrics: Dict[str, float]) -> List[Dict[str, str]]:
        """生成网络请求相关的优化建议"""
        recommendations = []
        
        # 总请求数量分析
        total_requests = metrics.get("total_requests", 0)
        if total_requests > 50:
            recommendations.append({
                "category": "请求数量优化",
                "priority": "medium",
                "issue": f"页面总请求数量为 {total_requests} 个，请求过多",
                "suggestions": [
                    "合并小文件，减少 HTTP 请求数量",
                    "使用 CSS Sprites 合并图片",
                    "启用 HTTP/2 多路复用",
                    "使用内联关键 CSS 和 JavaScript"
                ]
            })
        
        # 总资源大小分析
        total_size = metrics.get("total_size", 0)
        total_size_mb = total_size / (1024 * 1024)
        if total_size_mb > 5:  # 超过5MB
            recommendations.append({
                "category": "资源大小优化",
                "priority": "high" if total_size_mb > 10 else "medium",
                "issue": f"页面总资源大小为 {total_size_mb:.1f}MB，资源过大",
                "suggestions": [
                    "压缩图片，使用 WebP 格式",
                    "启用 Gzip/Brotli 压缩",
                    "移除未使用的 CSS 和 JavaScript",
                    "使用懒加载技术",
                    "优化字体文件大小"
                ]
            })
        
        # API请求分析
        api_requests = metrics.get("api_requests", 0)
        if api_requests > 10:
            recommendations.append({
                "category": "API请求优化",
                "priority": "medium",
                "issue": f"API请求数量为 {api_requests} 个，可能存在过度请求",
                "suggestions": [
                    "合并多个API请求为批量请求",
                    "实现API响应缓存",
                    "使用 GraphQL 减少请求数量",
                    "优化API响应数据结构"
                ]
            })
        
        # 第三方请求分析
        third_party_requests = metrics.get("third_party_requests", 0)
        if third_party_requests > 15:
            recommendations.append({
                "category": "第三方资源优化",
                "priority": "medium",
                "issue": f"第三方请求数量为 {third_party_requests} 个，可能影响性能",
                "suggestions": [
                    "评估第三方脚本的必要性",
                    "使用异步加载第三方资源",
                    "考虑自托管关键第三方资源",
                    "使用 Resource Hints 预连接第三方域名"
                ]
            })
        
        # 平均响应时间分析
        avg_response_time = metrics.get("avg_response_time", 0)
        if avg_response_time > 500:  # 超过500ms
            recommendations.append({
                "category": "响应时间优化",
                "priority": "high" if avg_response_time > 1000 else "medium",
                "issue": f"平均响应时间为 {avg_response_time:.0f}ms，响应较慢",
                "suggestions": [
                    "优化服务器性能",
                    "使用 CDN 加速",
                    "启用缓存策略",
                    "优化数据库查询",
                    "使用 HTTP/2 或 HTTP/3"
                ]
            })
        
        return recommendations
    
    def _extract_network_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取网络请求详细分析数据"""
        network_analysis = {
            "summary": {},
            "large_resources": [],
            "slow_requests": [],
            "api_requests": [],
            "third_party_resources": [],
            "requests_by_type": {},
            "requests_by_domain": {},
            "resources": [],  # 添加资源列表
            "api_count": 0,
            "static_count": 0
        }
        
        try:
            # 处理新的插件化数据结构
            if "performance_data" in data:
                performance_data = data["performance_data"]
                
                if "data" in performance_data and "NetworkCollector" in performance_data["data"]:
                    network_data = performance_data["data"]["NetworkCollector"].get("data", {})
                    
                    # 提取所有资源数据（增强版）
                    resources = network_data.get("resources", [])
                    # 去重
                    unique_resources = {}
                    for resource in resources:
                        url = resource.get("url", resource.get("name", ""))
                        if url and url not in unique_resources:
                            unique_resources[url] = resource
                    resources = list(unique_resources.values())
                    
                    # 格式化资源数据以适配模板
                    formatted_resources = []
                    for resource in resources:
                        formatted_resource = {
                            "url": resource.get("url", resource.get("name", "")),
                            "method": resource.get("method", "GET"),
                            "status": resource.get("status", 0),
                            "status_class": "success" if resource.get("status", 0) < 400 else "error" if resource.get("status", 0) >= 500 else "warning",
                            "size": self._format_size(resource.get("transferSize", 0)),
                            "duration": int(resource.get("responseTime", 0)),
                            "type": "API" if resource.get("isApi", False) else "Static" if resource.get("isStatic", False) else "Other",
                            "type_color": "danger" if resource.get("isApi", False) else "success" if resource.get("isStatic", False) else "secondary",
                            "request_headers": resource.get("requestHeaders", {}),
                            "response_headers": resource.get("responseHeaders", {}),
                            "request_body": resource.get("requestBody", ""),
                            "response_body": resource.get("responseBody", ""),
                            "isApi": bool(resource.get("isApi", False)),
                            "isStatic": bool(resource.get("isStatic", False)),
                            "isThirdParty": bool(resource.get("isThirdParty", False)),
                        }
                        formatted_resources.append(formatted_resource)
                    
                    network_analysis["resources"] = formatted_resources
                    
                    # 使用去重后的资源分析结果重新计算所有统计信息
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
                    
                    network_analysis["summary"] = {
                        "total_requests": len(resources),
                        "total_size_mb": round(total_size / (1024 * 1024), 2),
                        "avg_response_time": round(avg_response_time, 2),
                        "api_requests": api_count,
                        "static_requests": static_count,
                        "third_party_requests": third_party_count
                    }
                    network_analysis["api_count"] = api_count
                    network_analysis["static_count"] = static_count
                    network_analysis["requests_by_type"] = requests_by_type
                    network_analysis["requests_by_domain"] = requests_by_domain
            
        except Exception as e:
            self.logger.error(f"提取网络分析数据失败: {e}")
        
        return network_analysis
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _format_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化资源数据，添加可读的大小和域名信息"""
        formatted = []
        
        for resource in resources:
            formatted_resource = {
                "url": resource.get("name", ""),
                "domain": resource.get("domain", ""),
                "type": resource.get("initiatorType", "unknown"),
                "size_kb": round(resource.get("transferSize", 0) / 1024, 2),
                "response_time_ms": round(resource.get("responseTime", 0), 2),
                "duration_ms": round(resource.get("duration", 0), 2)
            }
            
            # 添加资源类型标识
            if resource.get("isApi", False):
                formatted_resource["category"] = "API"
            elif resource.get("isStatic", False):
                formatted_resource["category"] = "Static"
            elif resource.get("isThirdParty", False):
                formatted_resource["category"] = "Third-party"
            else:
                formatted_resource["category"] = "Other"
            
            formatted.append(formatted_resource)
        
        return formatted
    
    def _generate_error_report(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成错误报告"""
        return {
            "url": error_data.get("url", "Unknown"),
            "timestamp": datetime.now().timestamp(),
            "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": error_data.get("error", "Unknown error"),
            "success": False
        }
    
    def format_report_text(self, report: Dict[str, Any]) -> str:
        """格式化报告为文本格式"""
        if not report.get("success", True):
            return f"""
性能测试报告
{'='*50}

URL: {report['url']}
测试时间: {report['test_date']}
状态: 测试失败
错误: {report.get('error', 'Unknown error')}
"""
        
        text = f"""
性能测试报告
{'='*50}

URL: {report['url']}
测试时间: {report['test_date']}
总体评分: {report['overall_score']:.1f}/100

关键指标:
{'-'*30}
"""
        
        # 添加关键指标
        for metric_name, score_info in report.get("scores", {}).items():
            rating_emoji = {"good": "✅", "needs_improvement": "⚠️", "poor": "❌"}
            emoji = rating_emoji.get(score_info["rating"], "❓")
            
            text += f"{emoji} {metric_name.upper()}: {score_info['value']:.0f}ms (评分: {score_info['score']:.1f})\n"
        
        # 添加网络请求分析
        network_analysis = report.get("network_analysis", {})
        if network_analysis and network_analysis.get("summary"):
            text += f"\n网络请求分析:\n{'-'*30}\n"
            
            summary = network_analysis["summary"]
            text += f"📊 总请求数: {summary.get('total_requests', 0)} 个\n"
            text += f"📦 总资源大小: {summary.get('total_size_mb', 0)} MB\n"
            text += f"⏱️  平均响应时间: {summary.get('avg_response_time', 0)} ms\n"
            text += f"🔗 API请求数: {summary.get('api_requests', 0)} 个\n"
            text += f"🌐 第三方请求数: {summary.get('third_party_requests', 0)} 个\n"
            
            # 大资源分析
            large_resources = network_analysis.get("large_resources", [])
            if large_resources:
                text += f"\n📁 大资源文件 (>500KB):\n"
                for i, resource in enumerate(large_resources[:5], 1):  # 只显示前5个
                    text += f"  {i}. {resource['domain']} - {resource['size_kb']:.1f}KB ({resource['category']})\n"
                    text += f"     {resource['url'][:80]}{'...' if len(resource['url']) > 80 else ''}\n"
            
            # 慢请求分析
            slow_requests = network_analysis.get("slow_requests", [])
            if slow_requests:
                text += f"\n🐌 慢请求 (>1秒):\n"
                for i, resource in enumerate(slow_requests[:5], 1):  # 只显示前5个
                    text += f"  {i}. {resource['domain']} - {resource['response_time_ms']:.0f}ms ({resource['category']})\n"
                    text += f"     {resource['url'][:80]}{'...' if len(resource['url']) > 80 else ''}\n"
            
            # API请求分析
            api_requests = network_analysis.get("api_requests", [])
            if api_requests:
                text += f"\n🔌 API请求详情:\n"
                for i, resource in enumerate(api_requests[:5], 1):  # 只显示前5个
                    text += f"  {i}. {resource['domain']} - {resource['response_time_ms']:.0f}ms\n"
                    text += f"     {resource['url'][:80]}{'...' if len(resource['url']) > 80 else ''}\n"
            
            # 第三方资源分析
            third_party_resources = network_analysis.get("third_party_resources", [])
            if third_party_resources:
                text += f"\n🌍 第三方资源:\n"
                domain_count = {}
                for resource in third_party_resources:
                    domain = resource['domain']
                    domain_count[domain] = domain_count.get(domain, 0) + 1
                
                for domain, count in sorted(domain_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                    text += f"  • {domain}: {count} 个请求\n"
        
        # 添加优化建议
        recommendations = report.get("recommendations", [])
        if recommendations:
            text += f"\n优化建议:\n{'-'*30}\n"
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                emoji = priority_emoji.get(rec["priority"], "⚪")
                
                text += f"\n{i}. {emoji} {rec['category']}\n"
                text += f"   问题: {rec['issue']}\n"
                text += f"   建议:\n"
                for suggestion in rec["suggestions"]:
                    text += f"   • {suggestion}\n"
        
        return text
    
    def save_report(self, report: Dict[str, Any], filepath: str, format_type: str = "json"):
        """
        保存报告到文件
        
        Args:
            report: 报告数据
            filepath: 保存路径
            format_type: 格式类型 ('json' 或 'txt')
        """
        try:
            if format_type.lower() == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
            else:
                text_report = self.format_report_text(report)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text_report)
            
            self.logger.info(f"报告已保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
    
    def save_network_html_report(self, report: Dict[str, Any], filepath: str):
        """
        保存HTML格式的网络请求分析报告
        
        Args:
            report: 性能报告数据
            filepath: 保存路径
        """
        try:
            if not report.get("success", True):
                self.logger.warning("报告包含错误，无法生成网络分析报告")
                return
            
            network_analysis = report.get("network_analysis", {})
            url = report.get("url", "Unknown")
            
            if not network_analysis or not network_analysis.get("summary"):
                self.logger.warning("没有网络分析数据，无法生成网络报告")
                return
            
            # 使用网络报告生成器生成HTML报告
            self.network_report_generator.save_html_report(network_analysis, url, filepath)
            
        except Exception as e:
            self.logger.error(f"保存网络HTML报告失败: {e}")
    
    def generate_comprehensive_report(self, report: Dict[str, Any], output_dir: str = "reports"):
        """
        生成综合报告，包括JSON、文本和HTML格式
        
        Args:
            report: 性能报告数据
            output_dir: 输出目录
        """
        try:
            import os
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            url = report.get("url", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 清理URL用于文件名
            safe_url = "".join(c for c in url if c.isalnum() or c in ('-', '_')).rstrip()
            safe_url = safe_url[:50]  # 限制长度
            
            base_filename = f"{timestamp}_{safe_url}"
            
            # 保存JSON报告
            json_filepath = os.path.join(output_dir, f"{base_filename}_report.json")
            self.save_report(report, json_filepath, "json")
            
            # 保存文本报告
            txt_filepath = os.path.join(output_dir, f"{base_filename}_report.txt")
            self.save_report(report, txt_filepath, "txt")
            
            # 保存HTML网络分析报告
            html_filepath = os.path.join(output_dir, f"{base_filename}_network_analysis.html")
            self.save_network_html_report(report, html_filepath)
            
            # 保存完整HTML性能报告
            full_html_filepath = os.path.join(output_dir, f"{base_filename}_full_report.html")
            self.save_full_html_report(report, full_html_filepath)
            
            self.logger.info(f"综合报告已生成:")
            self.logger.info(f"  JSON报告: {json_filepath}")
            self.logger.info(f"  文本报告: {txt_filepath}")
            self.logger.info(f"  HTML网络分析: {html_filepath}")
            self.logger.info(f"  完整HTML报告: {full_html_filepath}")
            
            return {
                "json_report": json_filepath,
                "text_report": txt_filepath,
                "html_network_report": html_filepath,
                "full_html_report": full_html_filepath
            }
            
        except Exception as e:
            self.logger.error(f"生成综合报告失败: {e}")
            return None
    
    def save_full_html_report(self, report: Dict[str, Any], filepath: str):
        """
        保存完整的HTML性能报告，包含所有请求和接口信息
        
        Args:
            report: 性能报告数据
            filepath: 保存路径
        """
        try:
            if not report.get("success", True):
                self.logger.warning("报告包含错误，无法生成完整HTML报告")
                return
            
            html_content = self.generate_full_html_report(report)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"完整HTML性能报告已保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存完整HTML报告失败: {e}")
    
    def generate_full_html_report(self, report: Dict[str, Any]) -> str:
        """
        生成完整的HTML性能报告

        Args:
            report: 性能报告数据
        Returns:
            HTML格式的完整报告
        """
        try:
            url = report.get("url", "Unknown")
            timestamp = report.get("test_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            overall_score = report.get("overall_score", 0)
            network_analysis = report.get("network_analysis", {})
            key_metrics = report.get("key_metrics", {})
            scores = report.get("scores", {})
            recommendations = report.get("recommendations", [])

            # 统一资源统计，确保与资源表格一致
            all_resources = self._get_all_resources(network_analysis)
            api_count = sum(1 for r in all_resources if r.get('isApi'))
            static_count = sum(1 for r in all_resources if r.get('isStatic'))
            third_party_count = sum(1 for r in all_resources if r.get('isThirdParty'))
            total_requests = len(all_resources)

            template_data = {
                "report_title": f"性能分析报告 - {url}",
                "url": url,
                "analysis_time": timestamp,
                "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0.0",
                "total_duration": int(report.get("load_time", 0)),
                "key_metrics": [
                    {"name": "首屏绘制", "value": f"{key_metrics.get('fcp', 0):.0f}", "unit": "ms", "icon": "bi-speedometer2"},
                    {"name": "最大内容绘制", "value": f"{key_metrics.get('lcp', 0):.0f}", "unit": "ms", "icon": "bi-display"},
                    {"name": "首次字节", "value": f"{key_metrics.get('ttfb', 0):.0f}", "unit": "ms", "icon": "bi-clock"},
                    {"name": "综合评分", "value": f"{overall_score:.0f}", "unit": "分", "icon": "bi-star-fill"}
                ],
                "performance_metrics": {
                    "页面加载": [
                        {"name": "DOM就绪", "value": f"{key_metrics.get('dom_ready', 0):.0f}", "unit": "ms"},
                        {"name": "页面加载", "value": f"{key_metrics.get('page_load', 0):.0f}", "unit": "ms"},
                        {"name": "DNS查询", "value": f"{key_metrics.get('dns_lookup', 0):.0f}", "unit": "ms"},
                        {"name": "TCP连接", "value": f"{key_metrics.get('tcp_connect', 0):.0f}", "unit": "ms"}
                    ],
                    "网络请求": [
                        {"name": "总请求数", "value": f"{total_requests}", "unit": ""},
                        {"name": "API请求数", "value": f"{api_count}", "unit": ""},
                        {"name": "第三方请求", "value": f"{third_party_count}", "unit": ""},
                        {"name": "平均响应时间", "value": f"{key_metrics.get('avg_response_time', 0):.0f}", "unit": "ms"}
                    ]
                },
                "network_analysis": {
                    **network_analysis,
                    "api_count": api_count,
                    "static_count": static_count,
                    "third_party_count": third_party_count,
                    "total_requests": total_requests
                },
                "optimization_suggestions": [
                    {
                        "title": rec.get("issue", "优化建议"),
                        "description": "<br>".join(rec.get("suggestions", []) or ["请检查具体性能指标，或联系开发者完善建议内容。"]),
                        "level": rec.get("priority", "medium"),
                        "level_color": "danger" if rec.get("priority") == "high" else "warning" if rec.get("priority") == "medium" else "info",
                        "icon": "exclamation-circle" if rec.get("priority") == "high" else "exclamation-triangle" if rec.get("priority") == "medium" else "info-circle",
                        "details": ""
                    }
                    for rec in recommendations
                ],
                "memory_analysis": {
                    "metrics": [
                        {"name": "已用内存", "value": f"{key_metrics.get('memory_used', 0) / 1024 / 1024:.1f}", "unit": "MB"},
                        {"name": "总内存", "value": f"{key_metrics.get('memory_total', 0) / 1024 / 1024:.1f}", "unit": "MB"},
                        {"name": "内存限制", "value": f"{key_metrics.get('memory_limit', 0) / 1024 / 1024:.1f}", "unit": "MB"},
                        {"name": "内存使用率", "value": f"{(key_metrics.get('memory_used', 0) / key_metrics.get('memory_limit', 1)) * 100:.1f}", "unit": "%"}
                    ]
                } if key_metrics.get('memory_used') else None
            }

            if self.jinja_env:
                try:
                    template = self.jinja_env.get_template('report_template.html')
                    html = template.render(**template_data)
                    return html
                except Exception as e:
                    self.logger.error(f"模板渲染失败: {e}")
                    return self._generate_fallback_html(template_data)
            else:
                return self._generate_fallback_html(template_data)
        except Exception as e:
            self.logger.error(f"生成完整HTML报告失败: {e}")
            return f"<html><body><h1>报告生成失败</h1><p>错误: {e}</p></body></html>"
    
    def _generate_fallback_html(self, data: Dict[str, Any]) -> str:
        """生成备选的简单 HTML 报告"""
        # 生成关键指标卡片
        metrics_html = ""
        for metric in data['key_metrics']:
            metrics_html += f"""
            <div class="col-md-3 mb-3">
                <div class="card metric-card h-100">
                    <div class="card-body text-center">
                        <h5>{metric['name']}</h5>
                        <h3 class="text-primary">{metric['value']}</h3>
                        <small class="text-muted">{metric['unit']}</small>
                    </div>
                </div>
            </div>
            """
        
        # 生成网络分析部分
        network_html = ""
        if data.get('network_analysis'):
            network_html = f"""
        <div class="card mt-4">
            <div class="card-header">
                <h5>网络请求分析</h5>
            </div>
            <div class="card-body">
                <p>API 请求: {data['network_analysis'].get('api_count', 0)} 个</p>
                <p>静态资源: {data['network_analysis'].get('static_count', 0)} 个</p>
            </div>
        </div>
        """
        
        # 生成优化建议部分
        suggestions_html = ""
        if data.get('optimization_suggestions'):
            suggestions_content = ""
            for suggestion in data['optimization_suggestions']:
                suggestions_content += f"""
                <div class="mb-3">
                    <h6>{suggestion['title']}</h6>
                    <p>{suggestion['description']}</p>
                </div>
                """
            
            suggestions_html = f"""
        <div class="card mt-4">
            <div class="card-header">
                <h5>优化建议 ({len(data['optimization_suggestions'])}条)</h5>
            </div>
            <div class="card-body">
                {suggestions_content}
            </div>
        </div>
        """
        
        # 组装完整的 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['report_title']}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .metric-card {{ transition: transform 0.2s; }}
        .metric-card:hover {{ transform: translateY(-2px); }}
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-primary">
        <div class="container-fluid">
            <span class="navbar-brand">性能医生</span>
            <span class="navbar-text">分析时间: {data['analysis_time']}</span>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-body text-center">
                <h1 class="text-primary">性能分析报告</h1>
                <p class="text-muted">网站: {data['url']} | 总耗时: {data['total_duration']}ms</p>
            </div>
        </div>

        <div class="row mt-4">
            {metrics_html}
        </div>

        {network_html}
        {suggestions_html}
    </div>

    <footer class="bg-dark text-light py-3 mt-5">
        <div class="container text-center">
            <p class="mb-0">由 性能医生 生成 | 版本: {data['version']} | 生成时间: {data['generation_time']}</p>
        </div>
    </footer>
</body>
</html>"""
        
        return html
    
    def _get_score_class(self, score: float) -> str:
        """获取评分对应的CSS类"""
        if score >= 80:
            return "score-good"
        elif score >= 60:
            return "score-medium"
        else:
            return "score-poor"
    
    def _get_all_resources(self, network_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取所有资源列表（增强版）"""
        all_resources = []
        
        # 从网络分析数据中提取所有资源
        if "resources" in network_analysis:
            all_resources.extend(network_analysis["resources"])
        
        # 去重并排序
        unique_resources = {}
        for resource in all_resources:
            url = resource.get("url", resource.get("name", ""))
            if url and url not in unique_resources:
                unique_resources[url] = resource
        
        # 按大小排序
        sorted_resources = sorted(
            unique_resources.values(),
            key=lambda x: x.get("transferSize", 0),
            reverse=True
        )
        
        return sorted_resources
    
    def _generate_performance_metrics_section(self, key_metrics: Dict[str, float], scores: Dict[str, Any]) -> str:
        """生成性能指标部分"""
        if not key_metrics:
            return ""
        
        template = self.jinja_env.get_template('performance_metrics_section.html')
        return template.render(
            key_metrics=key_metrics,
            scores=scores
        )
    
    def _generate_recommendations_section(self, recommendations: List[Dict[str, Any]]) -> str:
        """生成优化建议部分"""
        if not recommendations:
            return ""
        
        template = self.jinja_env.get_template('recommendations_section.html')
        return template.render(
            recommendations=recommendations
        )
    
    def _generate_all_resources_section(self, all_resources: List[Dict[str, Any]], network_analysis: Dict[str, Any]) -> str:
        """生成所有资源请求详细信息部分"""
        if not all_resources:
            return ""
        
        # 调试：统计API资源
        api_resources = [r for r in all_resources if r.get("isApi", False)]
        static_resources = [r for r in all_resources if r.get("isStatic", False)]
        third_party_resources = [r for r in all_resources if r.get("isThirdParty", False)]
        other_resources = [r for r in all_resources if not r.get("isApi", False) and not r.get("isStatic", False) and not r.get("isThirdParty", False)]
        
        template = self.jinja_env.get_template('all_resources_section.html')
        return template.render(
            api_resources=api_resources,
            static_resources=static_resources,
            third_party_resources=third_party_resources,
            other_resources=other_resources,
            network_analysis=network_analysis
        )
    
    def _generate_network_section(self, network_analysis: Dict[str, Any]) -> str:
        """生成网络分析部分"""
        if not network_analysis or not network_analysis.get("summary"):
            return ""
        
        summary = network_analysis["summary"]
        
        template = self.jinja_env.get_template('network_section.html')
        return template.render(
            summary=summary
        )
