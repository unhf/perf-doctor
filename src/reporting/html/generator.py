"""
HTML报告生成器

生成美观的HTML性能报告
"""

from ..base.generator import BaseReportGenerator
from .templates import HTMLReportTemplate

class HTMLReportGenerator(BaseReportGenerator):
    """HTML报告生成器"""
    def generate(self) -> str:
        # 这里用简单模板，实际可用Jinja2等
        return HTMLReportTemplate.render(self.data) 