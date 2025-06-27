"""
报告服务

负责生成各种格式的报告
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import asdict, is_dataclass
from jinja2 import Template, Environment, FileSystemLoader
import sys

from ..core import Config
from ..core.types import ReportData


class ReportService:
    """报告服务"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化 Jinja2 环境
        self._init_jinja_env()
        
        # 性能阈值配置（毫秒）
        self.thresholds = {
            "fcp": {"good": 1800, "poor": 3000},      # First Contentful Paint
            "lcp": {"good": 2500, "poor": 4000},      # Largest Contentful Paint
            "ttfb": {"good": 200, "poor": 600},       # Time to First Byte
            "dom_ready": {"good": 2000, "poor": 4000}, # DOM Ready
            "page_load": {"good": 3000, "poor": 5000}  # Page Load
        }
    
    def _init_jinja_env(self):
        """初始化Jinja2环境"""
        try:
            # 尝试从当前目录的 templates 文件夹加载
            template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
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
            self.jinja_env = None
    
    async def generate_json_report(self, performance_data: Dict[str, Any]) -> str:
        """生成JSON报告"""
        self.logger.info("开始生成JSON报告")
        
        try:
            # 确保输出目录存在
            os.makedirs(self.config.report.output_dir, exist_ok=True)
            
            # 生成JSON报告
            json_report_path = f"{self.config.report.output_dir}/performance_report.json"
            serializable_data = self._convert_to_serializable(performance_data)
            
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON报告已生成: {json_report_path}")
            return json_report_path
            
        except Exception as e:
            self.logger.error(f"生成JSON报告失败: {e}")
            raise
    
    async def generate_html_report(self, performance_data: Dict[str, Any]) -> str:
        """生成HTML报告"""
        self.logger.info("开始生成HTML报告")
        
        try:
            # 确保输出目录存在
            os.makedirs(self.config.report.output_dir, exist_ok=True)
            
            # 生成HTML报告
            html_report_path = f"{self.config.report.output_dir}/performance_report.html"
            html_content = self._generate_html_content(performance_data)
            
            with open(html_report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML报告已生成: {html_report_path}")
            return html_report_path
            
        except Exception as e:
            self.logger.error(f"生成HTML报告失败: {e}")
            raise
    
    async def generate_all_reports(self, performance_data: Dict[str, Any]) -> Dict[str, str]:
        """生成所有格式的报告"""
        self.logger.info("开始生成所有格式的报告")
        
        try:
            json_path = await self.generate_json_report(performance_data)
            html_path = await self.generate_html_report(performance_data)
            
            return {
                "json": json_path,
                "html": html_path
            }
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            raise
    
    def _generate_html_content(self, performance_data: Dict[str, Any]) -> str:
        """生成HTML报告内容"""
        try:
            # 提取关键指标
            key_metrics = self._extract_key_metrics(performance_data)
            
            # 计算性能评分
            scores = self._calculate_scores(key_metrics)
            
            # 生成优化建议
            recommendations = self._generate_recommendations(key_metrics, scores)
            
            # 构建报告数据
            report_data = {
                "url": performance_data.get("url", "Unknown"),
                "timestamp": performance_data.get("timestamp", datetime.now().timestamp()),
                "test_date": datetime.fromtimestamp(
                    performance_data.get("timestamp", datetime.now().timestamp())
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "key_metrics": key_metrics,
                "scores": scores,
                "overall_score": self._calculate_overall_score(scores),
                "recommendations": recommendations,
                "raw_data": performance_data
            }
            
            # 使用Jinja2模板生成HTML
            if self.jinja_env:
                template = self.jinja_env.get_template('report_template.html')
                return template.render(report=report_data)
            else:
                # 如果模板加载失败，使用简单的HTML
                return self._generate_simple_html(report_data)
                
        except Exception as e:
            self.logger.error(f"生成HTML报告失败: {e}")
            return self._generate_error_html(str(e))
    
    def _extract_key_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """提取关键性能指标"""
        metrics = {}
        
        # 从收集器数据中提取指标
        if "data" in data:
            collector_data = data["data"]
            
            # 从 PaintCollector 中提取绘制指标
            if "PaintCollector" in collector_data:
                paint_result = collector_data["PaintCollector"]
                if hasattr(paint_result, 'data') and paint_result.data:
                    paint_data = paint_result.data
                    if "first-contentful-paint" in paint_data:
                        metrics["fcp"] = paint_data["first-contentful-paint"]
                    if "largest-contentful-paint" in paint_data:
                        metrics["lcp"] = paint_data["largest-contentful-paint"]
            
            # 从 NavigationCollector 中提取导航时序
            if "NavigationCollector" in collector_data:
                nav_result = collector_data["NavigationCollector"]
                if hasattr(nav_result, 'data') and nav_result.data:
                    nav_data = nav_result.data
                    if nav_data:
                        metrics["ttfb"] = nav_data.get("ttfb", 0)
                        metrics["dom_ready"] = nav_data.get("domReady", 0)
                        metrics["page_load"] = nav_data.get("pageLoad", 0)
                        metrics["dns_lookup"] = nav_data.get("dnsLookup", 0)
                        metrics["tcp_connect"] = nav_data.get("tcpConnect", 0)
            
            # 从 PerformanceMetricsCollector 中提取性能指标
            if "PerformanceMetricsCollector" in collector_data:
                perf_result = collector_data["PerformanceMetricsCollector"]
                if hasattr(perf_result, 'data') and perf_result.data:
                    perf_data = perf_result.data
                    for key, value in perf_data.items():
                        if key not in metrics and isinstance(value, (int, float)):
                            metrics[key] = value
            
            # 从 MemoryCollector 中提取内存指标
            if "MemoryCollector" in collector_data:
                memory_result = collector_data["MemoryCollector"]
                if hasattr(memory_result, 'data') and memory_result.data:
                    memory_data = memory_result.data
                    if memory_data:
                        metrics["memory_used"] = memory_data.get("usedJSHeapSize", 0)
                        metrics["memory_total"] = memory_data.get("totalJSHeapSize", 0)
                        metrics["memory_limit"] = memory_data.get("jsHeapSizeLimit", 0)
            
            # 从 NetworkCollector 中提取网络指标
            if "NetworkCollector" in collector_data:
                network_result = collector_data["NetworkCollector"]
                if hasattr(network_result, 'data') and network_result.data:
                    network_data = network_result.data
                    if network_data:
                        stats = network_data.get("statistics", {})
                        metrics["total_requests"] = stats.get("totalRequests", 0)
                        metrics["total_size"] = stats.get("totalSize", 0)
                        metrics["avg_response_time"] = stats.get("avgResponseTime", 0)
                        metrics["api_requests"] = stats.get("apiRequests", 0)
                        metrics["third_party_requests"] = stats.get("thirdPartyRequests", 0)
        
        return metrics
    
    def _calculate_scores(self, metrics: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """计算各项指标的评分"""
        scores = {}
        
        for metric_name, value in metrics.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]
                scores[metric_name] = self._calculate_metric_score(value, threshold)
        
        return scores
    
    def _calculate_metric_score(self, value: float, threshold: Dict[str, float]) -> Dict[str, Any]:
        """计算单个指标的评分"""
        if value <= threshold["good"]:
            score = 100
            status = "good"
        elif value <= threshold["poor"]:
            score = 50
            status = "needs-improvement"
        else:
            score = 0
            status = "poor"
        
        return {
            "score": score,
            "status": status,
            "value": value
        }
    
    def _calculate_overall_score(self, scores: Dict[str, Dict[str, Any]]) -> float:
        """计算总体评分"""
        if not scores:
            return 0
        
        total_score = sum(score_data["score"] for score_data in scores.values())
        return round(total_score / len(scores), 1)
    
    def _generate_recommendations(self, metrics: Dict[str, float], 
                                scores: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
        """生成优化建议"""
        recommendations = []
        
        # FCP建议
        if "fcp" in metrics:
            fcp = metrics["fcp"]
            if fcp > self.thresholds["fcp"]["poor"]:
                recommendations.append({
                    "type": "performance",
                    "title": "First Contentful Paint 过慢",
                    "description": f"FCP时间为{fcp:.0f}ms，建议优化到1800ms以下"
                })
        
        # LCP建议
        if "lcp" in metrics:
            lcp = metrics["lcp"]
            if lcp > self.thresholds["lcp"]["poor"]:
                recommendations.append({
                    "type": "performance",
                    "title": "Largest Contentful Paint 过慢",
                    "description": f"LCP时间为{lcp:.0f}ms，建议优化到2500ms以下"
                })
        
        # 网络请求建议
        if "total_requests" in metrics:
            total_requests = metrics["total_requests"]
            if total_requests > 50:
                recommendations.append({
                    "type": "network",
                    "title": "请求数量过多",
                    "description": f"总请求数{total_requests}个，建议减少到50个以下"
                })
        
        return recommendations
    
    def _convert_to_serializable(self, data: Any) -> Any:
        """转换数据为可JSON序列化的格式，递归支持所有dataclass对象"""
        from dataclasses import is_dataclass, asdict
        if is_dataclass(data):
            return {k: self._convert_to_serializable(getattr(data, k)) for k in data.__dataclass_fields__}
        elif hasattr(data, '__dataclass_fields__'):
            # 兼容未用is_dataclass注册的dataclass
            return {k: self._convert_to_serializable(getattr(data, k)) for k in data.__dataclass_fields__}
        elif isinstance(data, dict):
            return {k: self._convert_to_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_serializable(item) for item in data]
        elif isinstance(data, (int, float, str, bool, type(None))):
            return data
        else:
            # 对于其他类型，尝试转换为字符串
            return str(data)
    
    def _generate_simple_html(self, report_data: Dict[str, Any]) -> str:
        """生成简单的HTML报告（模板加载失败时的备选方案）"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>性能分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .metric {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
        .score {{ font-size: 24px; font-weight: bold; }}
        .good {{ color: green; }}
        .needs-improvement {{ color: orange; }}
        .poor {{ color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>性能分析报告</h1>
        <p><strong>URL:</strong> {report_data['url']}</p>
        <p><strong>测试时间:</strong> {report_data['test_date']}</p>
        <p><strong>总体评分:</strong> <span class="score">{report_data['overall_score']}</span></p>
    </div>
    
    <h2>关键指标</h2>
    {self._generate_metrics_html(report_data['key_metrics'], report_data['scores'])}
    
    <h2>优化建议</h2>
    {self._generate_recommendations_html(report_data['recommendations'])}
</body>
</html>
        """
    
    def _generate_metrics_html(self, metrics: Dict[str, float], scores: Dict[str, Any]) -> str:
        """生成指标HTML"""
        html = ""
        for metric_name, value in metrics.items():
            score_data = scores.get(metric_name, {})
            score = score_data.get("score", 0)
            status = score_data.get("status", "unknown")
            html += f"""
            <div class="metric">
                <strong>{metric_name}:</strong> {value:.2f}
                <span class="score {status}">({score}分)</span>
            </div>
            """
        return html
    
    def _generate_recommendations_html(self, recommendations: List[Dict[str, str]]) -> str:
        """生成建议HTML"""
        if not recommendations:
            return "<p>暂无优化建议</p>"
        
        html = "<ul>"
        for rec in recommendations:
            html += f"<li><strong>{rec['title']}:</strong> {rec['description']}</li>"
        html += "</ul>"
        return html
    
    def _generate_error_html(self, error_msg: str) -> str:
        """生成错误HTML"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>报告生成错误</title>
</head>
<body>
    <h1>报告生成失败</h1>
    <p>错误信息: {error_msg}</p>
</body>
</html>
        """ 