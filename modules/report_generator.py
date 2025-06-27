"""
性能报告生成模块

负责分析性能数据并生成格式化的报告，包括性能评分和优化建议
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

class ReportGenerator:
    """性能报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.logger = logging.getLogger(__name__)
        
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
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations
    
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
