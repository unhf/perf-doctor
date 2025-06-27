"""
报告格式化器

提供报告内容的格式化方法
"""

from typing import Any

class ReportFormatter:
    """报告格式化工具类"""
    @staticmethod
    def format_json(data: Any) -> str:
        import json
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def format_text(data: Any) -> str:
        return str(data) 