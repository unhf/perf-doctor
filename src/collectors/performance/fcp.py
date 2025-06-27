"""
First Contentful Paint (FCP) 辅助类

负责收集FCP相关指标
"""

import asyncio
from typing import Dict, Any, Optional
from ...core.types import CollectorResult


class FCPHelper:
    """FCP辅助类"""
    
    def __init__(self, client):
        self.client = client
        self.logger = client.logger if hasattr(client, 'logger') else None
        self.fcp_data = {}
    
    async def collect_fcp(self) -> Optional[Dict[str, Any]]:
        """收集FCP数据"""
        try:
            # 获取性能指标
            metrics = await self.client.get_metrics()
            
            if not metrics:
                return None
            
            # 提取FCP相关指标
            fcp_data = {}
            
            for metric in metrics:
                if metric.get('name') == 'FirstContentfulPaint':
                    fcp_data['fcp'] = {
                        'value': metric.get('value', 0),
                        'unit': 'ms'
                    }
                elif metric.get('name') == 'FirstPaint':
                    fcp_data['fp'] = {
                        'value': metric.get('value', 0),
                        'unit': 'ms'
                    }
            
            # 如果没有找到FCP，尝试从性能时间线获取
            if 'fcp' not in fcp_data:
                timeline = await self._get_performance_timeline()
                if timeline:
                    fcp_data.update(self._extract_fcp_from_timeline(timeline))
            
            return fcp_data if fcp_data else None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"收集FCP数据失败: {e}")
            return None
    
    async def _get_performance_timeline(self) -> Optional[Dict[str, Any]]:
        """获取性能时间线"""
        try:
            # 获取性能时间线
            result = await self.client.send_command('Performance.getMetrics')
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"获取性能时间线失败: {e}")
            return None
    
    def _extract_fcp_from_timeline(self, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """从时间线中提取FCP数据"""
        fcp_data = {}
        
        try:
            # 这里可以根据实际的时间线数据结构进行解析
            # 暂时返回空字典，实际实现时需要根据DevTools API的具体返回格式
            pass
        except Exception as e:
            if self.logger:
                self.logger.error(f"从时间线提取FCP失败: {e}")
        
        return fcp_data 