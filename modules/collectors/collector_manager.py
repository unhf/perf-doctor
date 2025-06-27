"""
收集器管理器

管理所有性能数据收集器插件的生命周期，协调数据收集过程
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Type
from .base_collector import BaseCollector
from .performance_metrics_collector import PerformanceMetricsCollector
from .paint_collector import PaintCollector
from .navigation_collector import NavigationCollector
from .memory_collector import MemoryCollector
from .network_collector import NetworkCollector


class CollectorManager:
    """收集器管理器"""
    
    def __init__(self, devtools_client):
        """
        初始化收集器管理器
        
        Args:
            devtools_client: DevTools 客户端实例
        """
        self.client = devtools_client
        self.logger = logging.getLogger(__name__)
        self.collectors: Dict[str, BaseCollector] = {}
        self.collected_data: Dict[str, Any] = {}
        
        # 注册默认收集器
        self._register_default_collectors()
    
    def _register_default_collectors(self):
        """注册默认的收集器插件"""
        default_collectors = [
            PerformanceMetricsCollector,
            PaintCollector,
            NavigationCollector,
            MemoryCollector,
            NetworkCollector
        ]
        
        for collector_class in default_collectors:
            self.register_collector(collector_class)
    
    def register_collector(self, collector_class: Type[BaseCollector], name: str = None):
        """
        注册收集器插件
        
        Args:
            collector_class: 收集器类
            name: 收集器名称（可选）
        """
        try:
            collector = collector_class(self.client)
            collector_name = name or collector.get_name()
            
            if collector_name in self.collectors:
                self.logger.warning(f"收集器 {collector_name} 已存在，将被覆盖")
            
            self.collectors[collector_name] = collector
            self.logger.info(f"注册收集器: {collector_name}")
            
        except Exception as e:
            self.logger.error(f"注册收集器失败: {e}")
    
    def unregister_collector(self, name: str) -> bool:
        """
        注销收集器插件
        
        Args:
            name: 收集器名称
            
        Returns:
            是否成功注销
        """
        if name in self.collectors:
            collector = self.collectors.pop(name)
            collector.reset()
            self.logger.info(f"注销收集器: {name}")
            return True
        return False
    
    def get_collector(self, name: str) -> Optional[BaseCollector]:
        """
        获取指定的收集器
        
        Args:
            name: 收集器名称
            
        Returns:
            收集器实例或 None
        """
        return self.collectors.get(name)
    
    def get_all_collectors(self) -> Dict[str, BaseCollector]:
        """获取所有收集器"""
        return self.collectors.copy()
    
    def enable_collector(self, name: str) -> bool:
        """
        启用指定的收集器
        
        Args:
            name: 收集器名称
            
        Returns:
            是否成功启用
        """
        collector = self.get_collector(name)
        if collector:
            collector.enable()
            return True
        return False
    
    def disable_collector(self, name: str) -> bool:
        """
        禁用指定的收集器
        
        Args:
            name: 收集器名称
            
        Returns:
            是否成功禁用
        """
        collector = self.get_collector(name)
        if collector:
            collector.disable()
            return True
        return False
    
    async def setup_all_collectors(self) -> bool:
        """
        设置所有启用的收集器
        
        Returns:
            是否全部设置成功
        """
        self.logger.info("开始设置所有收集器")
        
        # 收集所有需要的域
        required_domains = set()
        for collector in self.collectors.values():
            if collector.is_enabled():
                required_domains.update(collector.get_required_domains())
        
        # 启用所有需要的域
        for domain in required_domains:
            try:
                await self.client.enable_domain(domain)
                self.logger.debug(f"启用域: {domain}")
            except Exception as e:
                self.logger.error(f"启用域 {domain} 失败: {e}")
        
        # 设置所有收集器
        setup_results = []
        for name, collector in self.collectors.items():
            if collector.is_enabled():
                try:
                    success = await collector.setup()
                    setup_results.append((name, success))
                    if success:
                        self.logger.debug(f"收集器 {name} 设置成功")
                    else:
                        self.logger.error(f"收集器 {name} 设置失败")
                except Exception as e:
                    self.logger.error(f"设置收集器 {name} 时发生异常: {e}")
                    setup_results.append((name, False))
        
        # 检查是否所有收集器都设置成功
        all_success = all(success for _, success in setup_results)
        if all_success:
            self.logger.info("所有收集器设置完成")
        else:
            failed_collectors = [name for name, success in setup_results if not success]
            self.logger.warning(f"以下收集器设置失败: {failed_collectors}")
        
        return all_success
    
    async def collect_all_data(self) -> Dict[str, Any]:
        """
        收集所有启用的收集器数据
        
        Returns:
            所有收集器的数据字典
        """
        self.logger.info("开始收集所有数据")
        
        collected_data = {}
        collection_results = []
        
        for name, collector in self.collectors.items():
            if collector.is_enabled():
                try:
                    data = await collector.collect()
                    collected_data[name] = data
                    collection_results.append((name, True))
                    self.logger.debug(f"收集器 {name} 数据收集完成")
                except Exception as e:
                    self.logger.error(f"收集器 {name} 数据收集失败: {e}")
                    collected_data[name] = {"error": str(e)}
                    collection_results.append((name, False))
        
        # 添加汇总信息
        summary = {
            "total_collectors": len(self.collectors),
            "enabled_collectors": len([c for c in self.collectors.values() if c.is_enabled()]),
            "successful_collections": len([r for r in collection_results if r[1]]),
            "failed_collections": len([r for r in collection_results if not r[1]]),
            "collection_time": time.time()
        }
        
        result = {
            "summary": summary,
            "data": collected_data,
            "timestamp": time.time()
        }
        
        self.collected_data = result
        self.logger.info(f"数据收集完成: {summary['successful_collections']}/{summary['enabled_collectors']} 成功")
        
        return result
    
    async def collect_specific_data(self, collector_names: List[str]) -> Dict[str, Any]:
        """
        收集指定收集器的数据
        
        Args:
            collector_names: 收集器名称列表
            
        Returns:
            指定收集器的数据字典
        """
        self.logger.info(f"开始收集指定数据: {collector_names}")
        
        collected_data = {}
        
        for name in collector_names:
            collector = self.get_collector(name)
            if collector and collector.is_enabled():
                try:
                    data = await collector.collect()
                    collected_data[name] = data
                    self.logger.debug(f"收集器 {name} 数据收集完成")
                except Exception as e:
                    self.logger.error(f"收集器 {name} 数据收集失败: {e}")
                    collected_data[name] = {"error": str(e)}
            else:
                self.logger.warning(f"收集器 {name} 不存在或未启用")
                collected_data[name] = {"error": "收集器不存在或未启用"}
        
        return collected_data
    
    def reset_all_collectors(self):
        """重置所有收集器状态"""
        for collector in self.collectors.values():
            collector.reset()
        self.collected_data = {}
        self.logger.info("所有收集器已重置")
    
    def get_collector_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有收集器的状态信息
        
        Returns:
            收集器状态字典
        """
        status = {}
        for name, collector in self.collectors.items():
            status[name] = {
                "enabled": collector.is_enabled(),
                "name": collector.get_name(),
                "description": collector.get_description(),
                "required_domains": collector.get_required_domains()
            }
        return status
    
    def get_last_collected_data(self) -> Dict[str, Any]:
        """获取最后一次收集的数据"""
        return self.collected_data.copy() 