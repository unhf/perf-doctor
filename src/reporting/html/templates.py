"""
HTML报告模板

提供HTML报告的渲染方法
"""

class HTMLReportTemplate:
    @staticmethod
    def render(data) -> str:
        # 简单字符串拼接，实际可用Jinja2
        html = f"""
        <html>
        <head><title>性能分析报告</title></head>
        <body>
            <h1>性能分析报告</h1>
            <pre>{data}</pre>
        </body>
        </html>
        """
        return html 