"""
网络请求分析报告生成器

专门用于生成详细的网络请求分析报告，包括资源请求、API请求、性能分析等
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

class NetworkReportGenerator:
    """网络请求分析报告生成器"""
    
    def __init__(self):
        """初始化网络报告生成器"""
        self.logger = logging.getLogger(__name__)
    
    def generate_html_report(self, network_analysis: Dict[str, Any], url: str) -> str:
        """
        生成HTML格式的网络请求分析报告
        
        Args:
            network_analysis: 网络分析数据
            url: 分析的页面URL
            
        Returns:
            HTML格式的报告
        """
        try:
            summary = network_analysis.get("summary", {})
            
            html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>网络请求分析报告 - {url}</title>
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
            max-width: 1200px;
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
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
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
        }}
        
        .section-header h2 {{
            color: #333;
            font-size: 1.5em;
        }}
        
        .section-content {{
            padding: 20px;
        }}
        
        .resource-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
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
        
        .domain-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .domain-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .domain-name {{
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .domain-count {{
            font-size: 1.5em;
            color: #667eea;
            font-weight: bold;
        }}
        
        .optimization-tips {{
            background: #e8f5e8;
            border-left: 4px solid #4caf50;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .optimization-tips h3 {{
            color: #2e7d32;
            margin-bottom: 15px;
        }}
        
        .optimization-tips ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .optimization-tips li {{
            padding: 8px 0;
            border-bottom: 1px solid #c8e6c9;
        }}
        
        .optimization-tips li:last-child {{
            border-bottom: none;
        }}
        
        .optimization-tips li:before {{
            content: "✓";
            color: #4caf50;
            font-weight: bold;
            margin-right: 10px;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .resource-table {{
                font-size: 0.9em;
            }}
            
            .resource-table th,
            .resource-table td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 网络请求分析报告</h1>
            <div class="url">{url}</div>
            <div style="margin-top: 15px; opacity: 0.8;">
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
        
        {self._generate_large_resources_section(network_analysis)}
        {self._generate_slow_requests_section(network_analysis)}
        {self._generate_api_requests_section(network_analysis)}
        {self._generate_third_party_section(network_analysis)}
        {self._generate_optimization_tips(network_analysis)}
    </div>
</body>
</html>
"""
            
            return html
            
        except Exception as e:
            self.logger.error(f"生成HTML报告失败: {e}")
            return f"<html><body><h1>报告生成失败</h1><p>错误: {e}</p></body></html>"
    
    def _generate_large_resources_section(self, network_analysis: Dict[str, Any]) -> str:
        """生成大资源文件分析部分"""
        large_resources = network_analysis.get("large_resources", [])
        
        if not large_resources:
            return ""
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>📁 大资源文件分析 (>500KB)</h2>
            </div>
            <div class="section-content">
                <p>以下资源文件大小超过500KB，可能影响页面加载性能：</p>
                <table class="resource-table">
                    <thead>
                        <tr>
                            <th>域名</th>
                            <th>大小</th>
                            <th>类型</th>
                            <th>响应时间</th>
                            <th>URL</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for resource in large_resources[:10]:  # 只显示前10个
            category_class = f"category-{resource['category'].lower().replace('-', '')}"
            html += f"""
                        <tr>
                            <td><strong>{resource['domain']}</strong></td>
                            <td>{resource['size_kb']:.1f} KB</td>
                            <td><span class="category-badge {category_class}">{resource['category']}</span></td>
                            <td>{resource['response_time_ms']:.0f} ms</td>
                            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                {resource['url']}
                            </td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        return html
    
    def _generate_slow_requests_section(self, network_analysis: Dict[str, Any]) -> str:
        """生成慢请求分析部分"""
        slow_requests = network_analysis.get("slow_requests", [])
        
        if not slow_requests:
            return ""
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>🐌 慢请求分析 (>1秒)</h2>
            </div>
            <div class="section-content">
                <p>以下请求响应时间超过1秒，需要重点关注：</p>
                <table class="resource-table">
                    <thead>
                        <tr>
                            <th>域名</th>
                            <th>响应时间</th>
                            <th>类型</th>
                            <th>大小</th>
                            <th>URL</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for resource in slow_requests[:10]:  # 只显示前10个
            category_class = f"category-{resource['category'].lower().replace('-', '')}"
            html += f"""
                        <tr>
                            <td><strong>{resource['domain']}</strong></td>
                            <td style="color: #d32f2f; font-weight: bold;">{resource['response_time_ms']:.0f} ms</td>
                            <td><span class="category-badge {category_class}">{resource['category']}</span></td>
                            <td>{resource['size_kb']:.1f} KB</td>
                            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                {resource['url']}
                            </td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        return html
    
    def _generate_api_requests_section(self, network_analysis: Dict[str, Any]) -> str:
        """生成API请求分析部分"""
        api_requests = network_analysis.get("api_requests", [])
        
        if not api_requests:
            return ""
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>🔌 API请求分析</h2>
            </div>
            <div class="section-content">
                <p>检测到的API请求详情：</p>
                <table class="resource-table">
                    <thead>
                        <tr>
                            <th>域名</th>
                            <th>响应时间</th>
                            <th>大小</th>
                            <th>URL</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for resource in api_requests[:15]:  # 显示前15个
            html += f"""
                        <tr>
                            <td><strong>{resource['domain']}</strong></td>
                            <td>{resource['response_time_ms']:.0f} ms</td>
                            <td>{resource['size_kb']:.1f} KB</td>
                            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                {resource['url']}
                            </td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        return html
    
    def _generate_third_party_section(self, network_analysis: Dict[str, Any]) -> str:
        """生成第三方资源分析部分"""
        third_party_resources = network_analysis.get("third_party_resources", [])
        requests_by_domain = network_analysis.get("requests_by_domain", {})
        
        if not third_party_resources:
            return ""
        
        # 统计第三方域名
        third_party_domains = {}
        for resource in third_party_resources:
            domain = resource['domain']
            if domain not in third_party_domains:
                third_party_domains[domain] = {
                    'count': 0,
                    'total_size': 0,
                    'avg_response_time': 0
                }
            third_party_domains[domain]['count'] += 1
            third_party_domains[domain]['total_size'] += resource['size_kb']
            third_party_domains[domain]['avg_response_time'] += resource['response_time_ms']
        
        # 计算平均值
        for domain in third_party_domains:
            count = third_party_domains[domain]['count']
            third_party_domains[domain]['avg_response_time'] /= count
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>🌍 第三方资源分析</h2>
            </div>
            <div class="section-content">
                <p>第三方域名请求统计：</p>
                <div class="domain-stats">
        """
        
        # 按请求数量排序
        sorted_domains = sorted(third_party_domains.items(), 
                              key=lambda x: x[1]['count'], reverse=True)
        
        for domain, stats in sorted_domains[:8]:  # 显示前8个
            html += f"""
                    <div class="domain-item">
                        <div class="domain-name">{domain}</div>
                        <div class="domain-count">{stats['count']}</div>
                        <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
                            {stats['total_size']:.1f}KB | {stats['avg_response_time']:.0f}ms
                        </div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _generate_optimization_tips(self, network_analysis: Dict[str, Any]) -> str:
        """生成优化建议部分"""
        summary = network_analysis.get("summary", {})
        tips = []
        
        # 基于分析结果生成建议
        total_requests = summary.get("total_requests", 0)
        total_size_mb = summary.get("total_size_mb", 0)
        api_requests = summary.get("api_requests", 0)
        third_party_requests = summary.get("third_party_requests", 0)
        large_resources_count = len(network_analysis.get("large_resources", []))
        slow_requests_count = len(network_analysis.get("slow_requests", []))
        
        if total_requests > 50:
            tips.append("合并小文件，减少HTTP请求数量")
            tips.append("使用CSS Sprites合并图片")
            tips.append("启用HTTP/2多路复用")
        
        if total_size_mb > 5:
            tips.append("压缩图片，使用WebP格式")
            tips.append("启用Gzip/Brotli压缩")
            tips.append("移除未使用的CSS和JavaScript")
        
        if api_requests > 10:
            tips.append("合并多个API请求为批量请求")
            tips.append("实现API响应缓存")
            tips.append("使用GraphQL减少请求数量")
        
        if third_party_requests > 15:
            tips.append("评估第三方脚本的必要性")
            tips.append("使用异步加载第三方资源")
            tips.append("考虑自托管关键第三方资源")
        
        if large_resources_count > 0:
            tips.append("优化大文件，考虑懒加载")
            tips.append("使用CDN加速大文件传输")
        
        if slow_requests_count > 0:
            tips.append("优化慢请求的服务器性能")
            tips.append("使用缓存策略减少重复请求")
        
        if not tips:
            tips = ["页面网络性能良好，继续保持！"]
        
        html = """
        <div class="optimization-tips">
            <h3>💡 性能优化建议</h3>
            <ul>
        """
        
        for tip in tips:
            html += f"<li>{tip}</li>"
        
        html += """
            </ul>
        </div>
        """
        
        return html
    
    def save_html_report(self, network_analysis: Dict[str, Any], url: str, filepath: str):
        """
        保存HTML格式的网络分析报告
        
        Args:
            network_analysis: 网络分析数据
            url: 分析的页面URL
            filepath: 保存路径
        """
        try:
            html_content = self.generate_html_report(network_analysis, url)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML网络分析报告已保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存HTML报告失败: {e}") 