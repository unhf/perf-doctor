"""
性能优化建议

根据分析结果生成优化建议
"""

from typing import List, Dict, Any

class PerformanceRecommendations:
    """性能优化建议工具类"""
    @staticmethod
    def generate(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        recs = []
        for issue in analysis.get('issues', []):
            if issue['type'] == 'slow_fcp':
                recs.append({'advice': '优化首屏渲染，减少阻塞资源', 'level': 'high'})
            if issue['type'] == 'slow_lcp':
                recs.append({'advice': '优化主内容加载，压缩图片/字体', 'level': 'high'})
            if issue['type'] == 'slow_load':
                recs.append({'advice': '减少页面依赖，优化加载链路', 'level': 'medium'})
            if issue['type'] == 'high_memory':
                recs.append({'advice': '检查内存泄漏，优化JS对象生命周期', 'level': 'medium'})
        for rec in analysis.get('recommendations', []):
            if rec['type'] == 'reduce_requests':
                recs.append({'advice': '合并请求，使用CDN，开启缓存', 'level': 'medium'})
            if rec['type'] == 'reduce_size':
                recs.append({'advice': '压缩资源，开启Gzip/Brotli', 'level': 'high'})
        return recs 