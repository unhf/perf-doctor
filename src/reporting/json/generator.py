"""
JSON报告生成器

生成JSON格式的性能报告
"""

from ..base.generator import BaseReportGenerator
from ..base.formatter import ReportFormatter

class JSONReportGenerator(BaseReportGenerator):
    """JSON报告生成器"""
    def generate(self) -> str:
        return ReportFormatter.format_json(self.data) 