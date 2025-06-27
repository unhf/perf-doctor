"""
网络报告

生成网络分析报告内容
"""

from typing import Dict, Any

class NetworkReporter:
    """网络报告生成器"""
    @staticmethod
    def generate_report(analysis: Dict[str, Any]) -> str:
        lines = ["网络分析报告:"]
        for issue in analysis.get('issues', []):
            lines.append(f"- 问题: {issue['message']}")
        for rec in analysis.get('recommendations', []):
            lines.append(f"- 建议: {rec['message']}")
        return '\n'.join(lines) 