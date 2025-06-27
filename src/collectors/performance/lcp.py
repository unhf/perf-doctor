"""
Largest Contentful Paint (LCP) 辅助类

负责收集LCP相关指标
"""

import asyncio
from typing import Dict, Any, Optional
from ...core.types import CollectorResult


class LCPHelper:
    """LCP辅助类"""
    
    def __init__(self, client):
        self.client = client
        self.logger = client.logger if hasattr(client, 'logger') else None
        self.lcp_data = {}
        self.lcp_observer = None
    
    async def setup_lcp_observer(self) -> bool:
        """设置LCP观察器"""
        try:
            # 启用Performance域
            await self.client.send_command('Performance.enable')
            
            # 设置LCP观察器
            await self.client.send_command('Performance.setLCPObserver', {
                'enabled': True
            })
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"设置LCP观察器失败: {e}")
            return False
    
    async def collect_lcp(self) -> Optional[Dict[str, Any]]:
        """收集LCP数据"""
        try:
            # 获取性能指标
            metrics = await self.client.get_metrics()
            
            if not metrics:
                return None
            
            # 提取LCP相关指标
            lcp_data = {}
            
            for metric in metrics:
                if metric.get('name') == 'LargestContentfulPaint':
                    lcp_data['lcp'] = {
                        'value': metric.get('value', 0),
                        'unit': 'ms'
                    }
                elif metric.get('name') == 'LCPElement':
                    lcp_data['lcp_element'] = metric.get('value', '')
            
            # 如果没有找到LCP，尝试从性能时间线获取
            if 'lcp' not in lcp_data:
                timeline = await self._get_performance_timeline()
                if timeline:
                    lcp_data.update(self._extract_lcp_from_timeline(timeline))
            
            return lcp_data if lcp_data else None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"收集LCP数据失败: {e}")
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
    
    def _extract_lcp_from_timeline(self, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """从时间线中提取LCP数据"""
        lcp_data = {}
        
        try:
            # 这里可以根据实际的时间线数据结构进行解析
            # 暂时返回空字典，实际实现时需要根据DevTools API的具体返回格式
            pass
        except Exception as e:
            if self.logger:
                self.logger.error(f"从时间线提取LCP失败: {e}")
        
        return lcp_data 