"""
性能报告生成模块

负责分析性能数据并生成格式化的报告，包括性能评分和优化建议
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from .network_report_generator import NetworkReportGenerator

class ReportGenerator:
    """性能报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.logger = logging.getLogger(__name__)
        self.network_report_generator = NetworkReportGenerator()
        
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
        recommendations.extend(network_recommendations)
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
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
            "resources": []  # 添加资源列表
        }
        
        try:
            # 处理新的插件化数据结构
            if "performance_data" in data:
                performance_data = data["performance_data"]
                
                if "data" in performance_data and "NetworkCollector" in performance_data["data"]:
                    network_data = performance_data["data"]["NetworkCollector"].get("data", {})
                    
                    # 提取统计摘要
                    stats = network_data.get("statistics", {})
                    network_analysis["summary"] = {
                        "total_requests": stats.get("totalRequests", 0),
                        "total_size_mb": round(stats.get("totalSize", 0) / (1024 * 1024), 2),
                        "avg_response_time": round(stats.get("avgResponseTime", 0), 2),
                        "api_requests": stats.get("apiRequests", 0),
                        "static_requests": stats.get("staticRequests", 0),
                        "third_party_requests": stats.get("thirdPartyRequests", 0)
                    }
                    
                    # 提取详细分析数据
                    analysis = network_data.get("analysis", {})
                    network_analysis["large_resources"] = self._format_resources(
                        analysis.get("large_resources", [])
                    )
                    network_analysis["slow_requests"] = self._format_resources(
                        analysis.get("slow_requests", [])
                    )
                    network_analysis["api_requests"] = self._format_resources(
                        analysis.get("api_requests", [])
                    )
                    network_analysis["third_party_resources"] = self._format_resources(
                        analysis.get("third_party_resources", [])
                    )
                    
                    # 提取所有资源数据（增强版）
                    resources = network_data.get("resources", [])
                    network_analysis["resources"] = resources
                    
                    # 使用增强的资源分析结果重新计算所有统计信息
                    api_count = len([r for r in resources if r.get("isApi", False)])
                    static_count = len([r for r in resources if r.get("isStatic", False)])
                    third_party_count = len([r for r in resources if r.get("isThirdParty", False)])
                    
                    # 计算总大小和平均响应时间
                    total_size = sum(r.get("transferSize", 0) for r in resources)
                    response_times = [r.get("responseTime", 0) for r in resources if r.get("responseTime", 0) > 0]
                    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                    
                    # 按类型和域名统计
                    requests_by_type = {}
                    requests_by_domain = {}
                    for r in resources:
                        # 按类型统计
                        initiator_type = r.get("initiatorType", "unknown")
                        requests_by_type[initiator_type] = requests_by_type.get(initiator_type, 0) + 1
                        
                        # 按域名统计
                        domain = r.get("domain", "unknown")
                        requests_by_domain[domain] = requests_by_domain.get(domain, 0) + 1
                    
                    # 更新统计摘要，完全使用增强分析结果
                    network_analysis["summary"] = {
                        "total_requests": len(resources),
                        "total_size_mb": round(total_size / (1024 * 1024), 2),
                        "avg_response_time": round(avg_response_time, 2),
                        "api_requests": api_count,
                        "static_requests": static_count,
                        "third_party_requests": third_party_count
                    }
                    
                    # 更新请求类型和域名统计
                    network_analysis["requests_by_type"] = requests_by_type
                    network_analysis["requests_by_domain"] = requests_by_domain
            
        except Exception as e:
            self.logger.error(f"提取网络分析数据失败: {e}")
        
        return network_analysis
    
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
            
            # 提取网络分析数据
            network_analysis = report.get("network_analysis", {})
            summary = network_analysis.get("summary", {})
            
            # 提取性能指标
            key_metrics = report.get("key_metrics", {})
            scores = report.get("scores", {})
            recommendations = report.get("recommendations", [])
            
            # 获取所有资源列表
            all_resources = self._get_all_resources(network_analysis)
            
            html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>完整性能分析报告 - {url}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .url {{
            font-size: 1.2em;
            opacity: 0.9;
            word-break: break-all;
        }}
        
        .score-display {{
            font-size: 3em;
            font-weight: bold;
            margin: 20px 0;
        }}
        
        .score-good {{ color: #4caf50; }}
        .score-medium {{ color: #ff9800; }}
        .score-poor {{ color: #f44336; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .section-header {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .section-header h2 {{
            color: #333;
            font-size: 1.5em;
        }}
        
        .section-header .count {{
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        
        .section-content {{
            padding: 20px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .metric-name {{
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }}
        
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .metric-score {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
        
        .resource-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 0.9em;
        }}
        
        .resource-table th,
        .resource-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .resource-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .resource-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .category-badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }}
        
        .category-api {{
            background: #e3f2fd;
            color: #1976d2;
        }}
        
        .category-static {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        
        .category-third-party {{
            background: #fff3e0;
            color: #f57c00;
        }}
        
        .category-other {{
            background: #f1f8e9;
            color: #388e3c;
        }}
        
        .filter-controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }}
        
        .filter-btn:hover {{
            background: #f0f0f0;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .search-box {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 20px;
            width: 200px;
            font-size: 0.9em;
        }}
        
        .recommendations {{
            background: #e8f5e8;
            border-left: 4px solid #4caf50;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .recommendations h3 {{
            color: #2e7d32;
            margin-bottom: 15px;
        }}
        
        .recommendation-item {{
            margin-bottom: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #4caf50;
        }}
        
        .recommendation-priority {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
            margin-bottom: 10px;
        }}
        
        .priority-high {{
            background: #ffebee;
            color: #c62828;
        }}
        
        .priority-medium {{
            background: #fff3e0;
            color: #ef6c00;
        }}
        
        .priority-low {{
            background: #e8f5e8;
            color: #2e7d32;
        }}
        
        .recommendation-issue {{
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .recommendation-suggestions {{
            list-style: none;
            padding-left: 0;
        }}
        
        .recommendation-suggestions li {{
            padding: 5px 0;
            border-bottom: 1px solid #e8f5e8;
        }}
        
        .recommendation-suggestions li:last-child {{
            border-bottom: none;
        }}
        
        .recommendation-suggestions li:before {{
            content: "✓";
            color: #4caf50;
            font-weight: bold;
            margin-right: 10px;
        }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .summary-stat {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .summary-stat .number {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .summary-stat .label {{
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }}
        
        .hidden {{
            display: none;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            
            .resource-table {{
                font-size: 0.8em;
            }}
            
            .resource-table th,
            .resource-table td {{
                padding: 8px;
            }}
            
            .filter-controls {{
                flex-direction: column;
            }}
            
            .search-box {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 完整性能分析报告</h1>
            <div class="url">{url}</div>
            <div style="margin-top: 15px; opacity: 0.8;">
                测试时间: {timestamp}
            </div>
            <div class="score-display {self._get_score_class(overall_score)}">
                {overall_score:.1f}/100
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{summary.get('total_requests', 0)}</div>
                <div class="label">总请求数</div>
            </div>
            <div class="stat-card">
                <div class="value">{summary.get('total_size_mb', 0):.1f} MB</div>
                <div class="label">总资源大小</div>
            </div>
            <div class="stat-card">
                <div class="value">{summary.get('avg_response_time', 0):.0f} ms</div>
                <div class="label">平均响应时间</div>
            </div>
            <div class="stat-card">
                <div class="value">{summary.get('api_requests', 0)}</div>
                <div class="label">API请求数</div>
            </div>
            <div class="stat-card">
                <div class="value">{summary.get('third_party_requests', 0)}</div>
                <div class="label">第三方请求数</div>
            </div>
            <div class="stat-card">
                <div class="value">{len(network_analysis.get('large_resources', []))}</div>
                <div class="label">大资源文件</div>
            </div>
        </div>
        
        {self._generate_performance_metrics_section(key_metrics, scores)}
        {self._generate_recommendations_section(recommendations)}
        {self._generate_all_resources_section(all_resources, network_analysis)}
    </div>
    
    <script>
        // 过滤和搜索功能
        function filterResources(category) {{
            const rows = document.querySelectorAll('.resource-row');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // 更新按钮状态
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // 过滤行
            rows.forEach(row => {{
                if (category === 'all' || row.dataset.category === category) {{
                    row.classList.remove('hidden');
                }} else {{
                    row.classList.add('hidden');
                }}
            }});
        }}
        
        function searchResources() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const rows = document.querySelectorAll('.resource-row');
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    row.classList.remove('hidden');
                }} else {{
                    row.classList.add('hidden');
                }}
            }});
        }}
        
        // 排序功能
        function sortTable(columnIndex) {{
            const table = document.querySelector('.resource-table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort((a, b) => {{
                const aValue = a.cells[columnIndex].textContent;
                const bValue = b.cells[columnIndex].textContent;
                
                // 尝试数字排序
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return aNum - bNum;
                }}
                
                // 字符串排序
                return aValue.localeCompare(bValue);
            }});
            
            // 重新插入排序后的行
            rows.forEach(row => tbody.appendChild(row));
        }}
    </script>
</body>
</html>
"""
            
            return html
            
        except Exception as e:
            self.logger.error(f"生成完整HTML报告失败: {e}")
            return f"<html><body><h1>报告生成失败</h1><p>错误: {e}</p></body></html>"
    
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
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>📊 性能指标详情</h2>
            </div>
            <div class="section-content">
                <div class="metrics-grid">
        """
        
        for metric_name, value in key_metrics.items():
            if metric_name in scores:
                score_info = scores[metric_name]
                rating_emoji = {"good": "✅", "needs_improvement": "⚠️", "poor": "❌"}
                emoji = rating_emoji.get(score_info["rating"], "❓")
                
                html += f"""
                    <div class="metric-card">
                        <div class="metric-name">{emoji} {metric_name.upper()}</div>
                        <div class="metric-value">{value:.0f} ms</div>
                        <div class="metric-score">评分: {score_info['score']:.1f}/100</div>
                    </div>
                """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _generate_recommendations_section(self, recommendations: List[Dict[str, Any]]) -> str:
        """生成优化建议部分"""
        if not recommendations:
            return ""
        
        html = f"""
        <div class="section">
            <div class="section-header">
                <h2>💡 优化建议</h2>
                <div class="count">{len(recommendations)} 条建议</div>
            </div>
            <div class="section-content">
        """
        
        for rec in recommendations:
            priority_class = f"priority-{rec['priority']}"
            html += f"""
                <div class="recommendation-item">
                    <span class="recommendation-priority {priority_class}">{rec['priority'].upper()}</span>
                    <div class="recommendation-issue">{rec['issue']}</div>
                    <ul class="recommendation-suggestions">
            """
            
            for suggestion in rec["suggestions"]:
                html += f"<li>{suggestion}</li>"
            
            html += """
                    </ul>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _generate_all_resources_section(self, all_resources: List[Dict[str, Any]], network_analysis: Dict[str, Any]) -> str:
        """生成所有资源列表部分（增强版，包含详细信息）"""
        if not all_resources:
            return ""
        
        # 统计信息
        total_resources = len(all_resources)
        api_count = len([r for r in all_resources if r.get("isApi", False)])
        static_count = len([r for r in all_resources if r.get("isStatic", False)])
        third_party_count = len([r for r in all_resources if r.get("isThirdParty", False)])
        
        html = f"""
        <div class="section">
            <div class="section-header">
                <h2>📋 所有资源请求详细信息 ({total_resources} 个)</h2>
            </div>
            <div class="section-content">
                <div class="summary-stats">
                    <div class="summary-stat">
                        <div class="number">{api_count}</div>
                        <div class="label">API请求</div>
                    </div>
                    <div class="summary-stat">
                        <div class="number">{static_count}</div>
                        <div class="label">静态资源</div>
                    </div>
                    <div class="summary-stat">
                        <div class="number">{third_party_count}</div>
                        <div class="label">第三方资源</div>
                    </div>
                    <div class="summary-stat">
                        <div class="number">{total_resources - api_count - static_count - third_party_count}</div>
                        <div class="label">其他资源</div>
                    </div>
                </div>
                
                <div class="filter-controls">
                    <input type="text" id="searchInput" class="search-box" placeholder="搜索资源..." onkeyup="searchResources()">
                    <button class="filter-btn active" onclick="filterResources('all')">全部</button>
                    <button class="filter-btn" onclick="filterResources('API')">API</button>
                    <button class="filter-btn" onclick="filterResources('Static')">静态资源</button>
                    <button class="filter-btn" onclick="filterResources('Third-party')">第三方</button>
                    <button class="filter-btn" onclick="filterResources('Other')">其他</button>
                </div>
                
                <table class="resource-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)" style="cursor: pointer;">域名</th>
                            <th onclick="sortTable(1)" style="cursor: pointer;">方法</th>
                            <th onclick="sortTable(2)" style="cursor: pointer;">状态码</th>
                            <th onclick="sortTable(3)" style="cursor: pointer;">大小 (KB)</th>
                            <th onclick="sortTable(4)" style="cursor: pointer;">响应时间 (ms)</th>
                            <th onclick="sortTable(5)" style="cursor: pointer;">类型</th>
                            <th onclick="sortTable(6)" style="cursor: pointer;">分类</th>
                            <th>URL</th>
                            <th>详细信息</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for i, resource in enumerate(all_resources):
            # 确定资源分类
            if resource.get("isApi", False):
                category = "API"
                category_class = "category-api"
            elif resource.get("isStatic", False):
                category = "Static"
                category_class = "category-static"
            elif resource.get("isThirdParty", False):
                category = "Third-party"
                category_class = "category-third-party"
            else:
                category = "Other"
                category_class = "category-other"
            
            # 提取详细信息
            method = resource.get("method", "GET")
            status = resource.get("status", 0)
            size_kb = resource.get("transferSize", 0) / 1024
            response_time = resource.get("responseTime", 0)
            mime_type = resource.get("mimeType", "")
            url = resource.get("url", resource.get("name", ""))
            domain = resource.get("domain", "")
            
            # 准备详细信息内容
            request_headers = resource.get("requestHeaders", {})
            response_headers = resource.get("responseHeaders", {})
            request_body = resource.get("requestBody", "")
            response_body = resource.get("responseBody", "")
            
            # 生成详细信息HTML
            details_html = self._generate_resource_details_html(
                i, method, status, mime_type, request_headers, response_headers, 
                request_body, response_body, url
            )
            
            html += f"""
                        <tr class="resource-row" data-category="{category}">
                            <td><strong>{domain}</strong></td>
                            <td><span class="method-badge method-{method.lower()}">{method}</span></td>
                            <td><span class="status-badge status-{status//100}xx">{status}</span></td>
                            <td>{size_kb:.1f}</td>
                            <td>{response_time:.0f}</td>
                            <td>{mime_type}</td>
                            <td><span class="category-badge {category_class}">{category}</span></td>
                            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{url}">
                                {url}
                            </td>
                            <td>
                                <button class="details-btn" onclick="toggleDetails({i})">查看详情</button>
                            </td>
                        </tr>
                        <tr class="details-row" id="details-{i}" style="display: none;">
                            <td colspan="9">
                                {details_html}
                            </td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <style>
        .method-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 500;
        }
        .method-get { background: #e8f5e8; color: #2e7d32; }
        .method-post { background: #fff3e0; color: #f57c00; }
        .method-put { background: #e3f2fd; color: #1976d2; }
        .method-delete { background: #ffebee; color: #c62828; }
        
        .status-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 500;
        }
        .status-2xx { background: #e8f5e8; color: #2e7d32; }
        .status-3xx { background: #fff3e0; color: #f57c00; }
        .status-4xx { background: #ffebee; color: #c62828; }
        .status-5xx { background: #ffebee; color: #c62828; }
        
        .details-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
        }
        .details-btn:hover {
            background: #5a6fd8;
        }
        
        .details-content {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .details-section {
            margin-bottom: 15px;
        }
        
        .details-section h4 {
            margin: 0 0 8px 0;
            color: #333;
            font-size: 0.9em;
        }
        
        .details-content pre {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            margin: 0;
            font-size: 0.8em;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .details-content .headers {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .details-content .header-item {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            font-size: 0.8em;
        }
        
        .details-content .header-name {
            font-weight: 600;
            color: #333;
        }
        
        .details-content .header-value {
            color: #666;
            word-break: break-all;
        }
        </style>
        
        <script>
        function toggleDetails(index) {
            const detailsRow = document.getElementById('details-' + index);
            const btn = event.target;
            
            if (detailsRow.style.display === 'none') {
                detailsRow.style.display = 'table-row';
                btn.textContent = '隐藏详情';
            } else {
                detailsRow.style.display = 'none';
                btn.textContent = '查看详情';
            }
        }
        </script>
        """
        
        return html
    
    def _generate_resource_details_html(self, index: int, method: str, status: int, 
                                       mime_type: str, request_headers: Dict, response_headers: Dict,
                                       request_body: str, response_body: str, url: str) -> str:
        """生成资源详细信息HTML"""
        
        html = f"""
        <div class="details-content">
            <div class="details-section">
                <h4>🔗 请求信息</h4>
                <div><strong>URL:</strong> {url}</div>
                <div><strong>方法:</strong> {method}</div>
                <div><strong>状态码:</strong> {status}</div>
                <div><strong>MIME类型:</strong> {mime_type}</div>
            </div>
        """
        
        # 请求头
        if request_headers:
            html += """
            <div class="details-section">
                <h4>📤 请求头</h4>
                <div class="headers">
            """
            for name, value in request_headers.items():
                html += f"""
                    <div class="header-item">
                        <div class="header-name">{name}</div>
                        <div class="header-value">{value}</div>
                    </div>
                """
            html += "</div></div>"
        
        # 响应头
        if response_headers:
            html += """
            <div class="details-section">
                <h4>📥 响应头</h4>
                <div class="headers">
            """
            for name, value in response_headers.items():
                html += f"""
                    <div class="header-item">
                        <div class="header-name">{name}</div>
                        <div class="header-value">{value}</div>
                    </div>
                """
            html += "</div></div>"
        
        # 请求体
        if request_body:
            html += f"""
            <div class="details-section">
                <h4>📤 请求体</h4>
                <pre>{request_body}</pre>
            </div>
            """
        
        # 响应体
        if response_body:
            html += f"""
            <div class="details-section">
                <h4>📥 响应体</h4>
                <pre>{response_body}</pre>
            </div>
            """
        
        html += "</div>"
        return html
