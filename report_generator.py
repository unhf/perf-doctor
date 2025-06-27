#!/usr/bin/env python3
"""
性能报告生成模块
负责生成和保存性能分析报告
"""

import time
from performance_collector import PerformanceAnalyzer


class ReportGenerator:
    """性能报告生成器"""
    
    @staticmethod
    def format_rating_symbol(rating):
        """
        根据评级返回对应的符号
        
        Args:
            rating (str): 评级 ('excellent', 'good', 'poor')
            
        Returns:
            str: 对应的符号
        """
        symbols = {
            'excellent': '✅',
            'good': '⚠️ ',
            'poor': '❌',
            'unknown': '❓'
        }
        return symbols.get(rating, '❓')
    
    @staticmethod
    def format_rating_text(rating):
        """
        根据评级返回对应的文本描述
        
        Args:
            rating (str): 评级
            
        Returns:
            str: 文本描述
        """
        texts = {
            'excellent': '优秀',
            'good': '良好',
            'poor': '需要优化',
            'unknown': '未知'
        }
        return texts.get(rating, '未知')
    
    @staticmethod
    def generate_report(performance_data):
        """
        生成完整的性能报告
        
        Args:
            performance_data (dict): 性能数据
            
        Returns:
            str: 格式化的报告文本
        """
        if not performance_data:
            return "无法生成报告 - 没有性能数据"
        
        # 生成报告头部
        report = ReportGenerator._generate_header(performance_data)
        
        # 生成核心指标部分
        report += ReportGenerator._generate_metrics_section(performance_data)
        
        # 生成性能评估部分
        report += ReportGenerator._generate_assessment_section(performance_data)
        
        # 生成建议部分
        report += ReportGenerator._generate_suggestions_section(performance_data)
        
        return report
    
    @staticmethod
    def _generate_header(data):
        """生成报告头部"""
        return f"""
=== Chrome页面性能分析报告 ===
页面标题: {data.get('title', 'Unknown')}
页面URL: {data.get('href', 'Unknown')}
分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    @staticmethod
    def _generate_metrics_section(data):
        """生成核心指标部分"""
        section = "\n=== 核心性能指标 ===\n"
        
        # 基本计时指标
        metrics = [
            ('loadTime', '页面加载时间'),
            ('domReady', 'DOM就绪时间'),
            ('ttfb', '首字节时间(TTFB)'),
            ('dns', 'DNS查询时间'),
            ('tcp', 'TCP连接时间'),
        ]
        
        for key, label in metrics:
            value = data.get(key, 0)
            if value > 0:
                section += f"{label}: {value:.0f}ms\n"
        
        # Paint Timing指标
        paint_data = data.get('paint', [])
        for paint in paint_data:
            section += f"{paint['name']}: {paint['time']:.0f}ms\n"
        
        # 内存使用情况
        memory = data.get('memory', {})
        if memory and memory.get('usedJSHeapSize'):
            memory_mb = memory['usedJSHeapSize'] / 1024 / 1024
            section += f"JS堆内存使用: {memory_mb:.1f}MB\n"
            
            if memory.get('totalJSHeapSize'):
                total_mb = memory['totalJSHeapSize'] / 1024 / 1024
                section += f"JS堆内存总计: {total_mb:.1f}MB\n"
        
        return section
    
    @staticmethod
    def _generate_assessment_section(data):
        """生成性能评估部分"""
        section = "\n=== 性能评估 ===\n"
        
        # 获取评估结果
        assessment = PerformanceAnalyzer.generate_assessment(data)
        
        # 评估映射
        assessment_labels = {
            'load_time': '页面加载速度',
            'ttfb': '首字节时间',
            'first_paint': '首次绘制时间',
            'first_contentful_paint': '首次内容绘制'
        }
        
        for metric, label in assessment_labels.items():
            if metric in assessment:
                metric_data = assessment[metric]
                value = metric_data['value']
                rating = metric_data['rating']
                symbol = ReportGenerator.format_rating_symbol(rating)
                text = ReportGenerator.format_rating_text(rating)
                
                section += f"{symbol} {label}: {text} ({value:.0f}ms)\n"
        
        return section
    
    @staticmethod
    def _generate_suggestions_section(data):
        """生成优化建议部分"""
        section = "\n=== 优化建议 ===\n"
        
        # 获取评估结果
        assessment = PerformanceAnalyzer.generate_assessment(data)
        
        suggestions = []
        
        # 根据评估结果生成建议
        for metric, metric_data in assessment.items():
            if metric_data['rating'] == 'poor':
                if metric == 'load_time':
                    suggestions.append("• 优化页面加载速度：压缩资源、优化图片、使用CDN")
                elif metric == 'ttfb':
                    suggestions.append("• 优化服务器响应时间：检查服务器性能、数据库查询优化")
                elif metric in ['first_paint', 'first_contentful_paint']:
                    suggestions.append("• 优化首屏渲染：减少阻塞资源、内联关键CSS")
        
        # 通用建议
        load_time = data.get('loadTime', 0)
        if load_time > 5000:
            suggestions.append("• 页面加载时间过长，建议进行全面性能优化")
        
        memory = data.get('memory', {})
        if memory.get('usedJSHeapSize', 0) > 50 * 1024 * 1024:  # 50MB
            suggestions.append("• JavaScript内存使用较高，检查是否存在内存泄漏")
        
        if suggestions:
            section += "\n".join(suggestions) + "\n"
        else:
            section += "🎉 页面性能表现良好，无需特别优化\n"
        
        return section
    
    @staticmethod
    def save_report(report_content, filename=None):
        """
        保存报告到文件
        
        Args:
            report_content (str): 报告内容
            filename (str): 文件名，可选
            
        Returns:
            str: 保存的文件名
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"performance_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ 报告已保存到: {filename}")
            return filename
        except Exception as e:
            print(f"保存报告失败: {e}")
            return None
