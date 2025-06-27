"""
收集器管理器模块

管理所有数据收集器的生命周期
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional

from .collector import BaseCollector
from ...core.exceptions import CollectorException


class CollectorManager:
    """收集器管理器"""
    
    def __init__(self, client):
        self.client = client
        self.collectors: Dict[str, BaseCollector] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_collector(self, collector: BaseCollector):
        """注册收集器"""
        self.collectors[collector.name] = collector
        self.logger.info(f"注册收集器: {collector.name}")
    
    def get_collector(self, name: str) -> Optional[BaseCollector]:
        """获取收集器"""
        return self.collectors.get(name)
    
    def get_all_collectors(self) -> List[BaseCollector]:
        """获取所有收集器"""
        return list(self.collectors.values())
    
    def get_enabled_collectors(self) -> List[BaseCollector]:
        """获取已启用的收集器"""
        return [c for c in self.collectors.values() if c.is_enabled()]
    
    async def setup_all_collectors(self) -> bool:
        """设置所有收集器"""
        self.logger.info("开始设置所有收集器")
        
        for collector in self.collectors.values():
            try:
                success = await collector.setup()
                if success:
                    collector.enable()
                    self.logger.debug(f"收集器 {collector.name} 设置成功")
                else:
                    self.logger.error(f"收集器 {collector.name} 设置失败")
                    return False
            except Exception as e:
                self.logger.error(f"设置收集器 {collector.name} 异常: {e}")
                return False
        
        self.logger.info("所有收集器设置完成")
        return True
    
    async def collect_all_data(self) -> Dict[str, Any]:
        """收集所有数据"""
        self.logger.info("开始收集所有数据")
        
        results = {}
        successful_collections = 0
        failed_collections = 0
        
        for collector in self.collectors.values():
            if not collector.is_enabled():
                continue
            
            try:
                result = await collector.collect()
                results[collector.name] = result
                successful_collections += 1
                self.logger.debug(f"收集器 {collector.name} 数据收集完成")
            except Exception as e:
                self.logger.error(f"收集器 {collector.name} 数据收集失败: {e}")
                failed_collections += 1
                results[collector.name] = collector._create_result({}, str(e))
        
        self.logger.info(f"数据收集完成: {successful_collections}/{len(self.collectors)} 成功")
        
        return {
            "summary": {
                "total_collectors": len(self.collectors),
                "enabled_collectors": len(self.get_enabled_collectors()),
                "successful_collections": successful_collections,
                "failed_collections": failed_collections,
                "collection_time": asyncio.get_event_loop().time()
            },
            "data": results
        }
    
    def reset_all_collectors(self):
        """重置所有收集器"""
        for collector in self.collectors.values():
            collector.reset()
        self.logger.info("所有收集器已重置")
    
    def get_collector_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有收集器状态"""
        return {
            name: collector.get_status()
            for name, collector in self.collectors.items()
        }
    
    def enable_collector(self, name: str) -> bool:
        """启用指定收集器"""
        collector = self.collectors.get(name)
        if collector:
            collector.enable()
            return True
        return False
    
    def disable_collector(self, name: str) -> bool:
        """禁用指定收集器"""
        collector = self.collectors.get(name)
        if collector:
            collector.disable()
            return True
        return False 