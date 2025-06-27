"""
性能指标收集器

收集 Performance API 相关的性能指标
"""

import time
import logging
from typing import Dict, Any
from .base_collector import BaseCollector


class PerformanceCollector(BaseCollector):
    """Performance API 指标收集器"""
    
    def __init__(self, devtools_client):
        super().__init__(devtools_client, "PerformanceCollector")
        self.performance_data = {}
    
    def get_required_domains(self) -> list:
        """获取需要的 DevTools 域"""
        return ["Performance"]
    
    async def setup(self) -> bool:
        """设置性能指标收集器"""
        try:
            await self.client.enable_domain("Performance")
            await self.client.send_command("Performance.enable")
            
            # 设置事件处理器
            self.client.add_event_handler("Performance.metrics", self._on_performance_metrics)
            
            self.logger.debug("性能指标收集器设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置性能指标收集器失败: {e}")
            return False
    
    async def collect(self) -> Dict[str, Any]:
        """收集性能指标数据"""
        if not self.enabled:
            return {}
        
        try:
            # 获取 Performance API 指标
            response = await self.client.send_command("Performance.getMetrics")
            if not response or "metrics" not in response:
                return {}
            
            metrics = {}
            for metric in response["metrics"]:
                name = metric.get("name")
                value = metric.get("value")
                if name and value is not None:
                    metrics[name] = value
            
            self.performance_data = metrics
            self.logger.debug(f"收集到 {len(metrics)} 个性能指标")
            
            return {
                "type": "performance_metrics",
                "data": metrics,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"收集性能指标失败: {e}")
            return {"type": "performance_metrics", "error": str(e)}
    
    def _on_performance_metrics(self, params: Dict[str, Any]):
        """处理性能指标事件"""
        metrics = params.get("metrics", [])
        for metric in metrics:
            name = metric.get("name")
            value = metric.get("value")
            if name and value is not None:
                self.performance_data[name] = value
        self.logger.debug(f"收到性能指标事件: {len(metrics)} 项")
    
    def reset(self):
        """重置收集器状态"""
        super().reset()
        self.performance_data = {} 