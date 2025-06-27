"""
基础报告生成器

定义报告生成的基础接口
"""

from typing import Any

class BaseReportGenerator:
    """基础报告生成器"""
    def __init__(self, data: Any):
        self.data = data

    def generate(self) -> str:
        """生成报告，返回报告内容字符串"""
        raise NotImplementedError("子类需实现generate方法") 