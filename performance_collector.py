#!/usr/bin/env python3
"""
性能数据收集模块
负责收集和解析网页性能指标
"""

import json
import time


class PerformanceCollector:
    """网页性能数据收集器"""
    
    def __init__(self, devtools_client):
        """
        初始化性能收集器
        
        Args:
            devtools_client: DevTools客户端实例
        """
        self.devtools = devtools_client
    
    async def collect_page_info(self):
        """
        收集基本页面信息
        
        Returns:
            dict: 包含页面标题和URL的字典
        """
        print("获取页面基本信息...")
        
        result = await self.devtools.evaluate_javascript(
            'JSON.stringify({href: location.href, title: document.title})'
        )
        
        if result and 'result' in result and 'value' in result['result']:
            info = json.loads(result['result']['value'])
            print(f"页面标题: {info.get('title', 'Unknown')}")
            print(f"页面URL: {info.get('href', 'Unknown')}")
            return info
        
        print("获取页面信息失败")
        return {'title': 'Unknown', 'href': 'Unknown'}
    
    async def collect_performance_metrics(self):
        """
        收集详细的性能指标
        
        Returns:
            dict: 性能数据字典，失败返回None
        """
        print("收集性能指标...")
        
        # JavaScript代码用于收集性能数据
        performance_script = '''
        JSON.stringify({
            // 基本计时数据
            loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
            domReady: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
            ttfb: performance.timing.responseStart - performance.timing.navigationStart,
            dns: performance.timing.domainLookupEnd - performance.timing.domainLookupStart,
            tcp: performance.timing.connectEnd - performance.timing.connectStart,
            
            // Paint Timing API数据
            paint: performance.getEntriesByType('paint').map(p => ({
                name: p.name, 
                time: p.startTime
            })),
            
            // 内存使用情况
            memory: performance.memory || {},
            
            // 页面信息
            href: location.href,
            title: document.title,
            
            // 收集时间戳
            timestamp: Date.now()
        })
        '''
        
        result = await self.devtools.evaluate_javascript(performance_script)
        
        if result and 'result' in result and 'value' in result['result']:
            try:
                perf_data = json.loads(result['result']['value'])
                print("性能数据收集成功")
                return perf_data
            except json.JSONDecodeError as e:
                print(f"解析性能数据失败: {e}")
        
        print("性能数据收集失败")
        return None
    
    async def collect_all_data(self):
        """
        收集所有性能数据
        
        Returns:
            dict: 完整的性能数据，失败返回None
        """
        try:
            # 收集基本页面信息
            page_info = await self.collect_page_info()
            
            # 收集性能指标
            perf_metrics = await self.collect_performance_metrics()
            
            if perf_metrics:
                # 合并数据
                perf_metrics.update(page_info)
                return perf_metrics
            
            return None
            
        except Exception as e:
            print(f"收集性能数据时出错: {e}")
            return None


class PerformanceAnalyzer:
    """性能数据分析器"""
    
    # 性能阈值配置
    THRESHOLDS = {
        'load_time': {'excellent': 1000, 'good': 3000},
        'ttfb': {'excellent': 200, 'good': 500},
        'first_paint': {'excellent': 1000, 'good': 2000},
        'first_contentful_paint': {'excellent': 1500, 'good': 2500}
    }
    
    @staticmethod
    def analyze_metric(value, metric_type):
        """
        分析单个性能指标
        
        Args:
            value (float): 指标值
            metric_type (str): 指标类型
            
        Returns:
            str: 评估结果 ('excellent', 'good', 'poor')
        """
        if metric_type not in PerformanceAnalyzer.THRESHOLDS:
            return 'unknown'
        
        thresholds = PerformanceAnalyzer.THRESHOLDS[metric_type]
        
        if value < thresholds['excellent']:
            return 'excellent'
        elif value < thresholds['good']:
            return 'good'
        else:
            return 'poor'
    
    @staticmethod
    def generate_assessment(data):
        """
        生成性能评估
        
        Args:
            data (dict): 性能数据
            
        Returns:
            dict: 评估结果
        """
        assessment = {}
        
        # 分析页面加载时间
        load_time = data.get('loadTime', 0)
        if load_time > 0:
            assessment['load_time'] = {
                'value': load_time,
                'rating': PerformanceAnalyzer.analyze_metric(load_time, 'load_time')
            }
        
        # 分析首字节时间
        ttfb = data.get('ttfb', 0)
        if ttfb > 0:
            assessment['ttfb'] = {
                'value': ttfb,
                'rating': PerformanceAnalyzer.analyze_metric(ttfb, 'ttfb')
            }
        
        # 分析Paint Timing
        paint_data = data.get('paint', [])
        for paint in paint_data:
            paint_name = paint['name'].replace('-', '_')
            paint_time = paint['time']
            
            if paint_name in ['first_paint', 'first_contentful_paint']:
                assessment[paint_name] = {
                    'value': paint_time,
                    'rating': PerformanceAnalyzer.analyze_metric(paint_time, paint_name)
                }
        
        return assessment
