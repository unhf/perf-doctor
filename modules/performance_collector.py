"""
性能数据收集模块

负责收集页面性能指标，使用插件化的收集器架构
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from .devtools_client import DevToolsClient
from .collectors import CollectorManager


class PerformanceCollector:
    """性能数据收集器 - 使用插件化架构"""
    
    def __init__(self, devtools_client: DevToolsClient):
        """
        初始化性能收集器
        
        Args:
            devtools_client: DevTools 客户端实例
        """
        self.client = devtools_client
        self.logger = logging.getLogger(__name__)
        
        # 使用收集器管理器
        self.collector_manager = CollectorManager(devtools_client)
        
    async def collect_performance_data(self, url: str, wait_time: int = 5, 
                                     enabled_collectors: List[str] = None) -> Dict[str, Any]:
        """
        收集指定页面的性能数据
        
        Args:
            url: 目标页面URL
            wait_time: 等待时间（秒）
            enabled_collectors: 要启用的收集器列表，None表示使用所有收集器
            
        Returns:
            性能数据字典
        """
        self.logger.info(f"开始收集性能数据: {url}")
        
        try:
            # 重置所有收集器
            self.collector_manager.reset_all_collectors()
            
            # 如果指定了收集器，则只启用指定的收集器
            if enabled_collectors:
                # 先禁用所有收集器
                for name in self.collector_manager.get_all_collectors():
                    self.collector_manager.disable_collector(name)
                
                # 启用指定的收集器
                for name in enabled_collectors:
                    self.collector_manager.enable_collector(name)
            
            # 设置所有收集器
            if not await self.collector_manager.setup_all_collectors():
                self.logger.warning("部分收集器设置失败，继续收集数据")
            
            # 导航到目标页面
            if not await self.client.navigate_to(url):
                raise Exception(f"导航失败: {url}")
            
            # 等待页面加载
            await asyncio.sleep(wait_time)
            
            # 收集所有数据
            collected_data = await self.collector_manager.collect_all_data()
            
            # 构建结果
            result = {
                "url": url,
                "timestamp": time.time(),
                "load_time": wait_time,
                "collector_status": self.collector_manager.get_collector_status(),
                "performance_data": collected_data
            }
            
            self.logger.info(f"性能数据收集完成: {url}")
            return result
            
        except Exception as e:
            self.logger.error(f"收集性能数据失败: {e}")
            return {"url": url, "error": str(e)}
    
    async def collect_specific_metrics(self, url: str, collector_names: List[str], 
                                     wait_time: int = 5) -> Dict[str, Any]:
        """
        收集指定的性能指标
        
        Args:
            url: 目标页面URL
            collector_names: 要使用的收集器名称列表
            wait_time: 等待时间（秒）
            
        Returns:
            指定指标的数据字典
        """
        self.logger.info(f"开始收集指定指标: {url} - {collector_names}")
        
        try:
            # 重置所有收集器
            self.collector_manager.reset_all_collectors()
            
            # 设置所有收集器
            await self.collector_manager.setup_all_collectors()
            
            # 导航到目标页面
            if not await self.client.navigate_to(url):
                raise Exception(f"导航失败: {url}")
            
            # 等待页面加载
            await asyncio.sleep(wait_time)
            
            # 收集指定数据
            collected_data = await self.collector_manager.collect_specific_data(collector_names)
            
            result = {
                "url": url,
                "timestamp": time.time(),
                "collectors": collector_names,
                "data": collected_data
            }
            
            self.logger.info(f"指定指标收集完成: {url}")
            return result
            
        except Exception as e:
            self.logger.error(f"收集指定指标失败: {e}")
            return {"url": url, "error": str(e)}
    
    def register_custom_collector(self, collector_class, name: str = None):
        """
        注册自定义收集器
        
        Args:
            collector_class: 自定义收集器类
            name: 收集器名称（可选）
        """
        self.collector_manager.register_collector(collector_class, name)
    
    def unregister_collector(self, name: str) -> bool:
        """
        注销收集器
        
        Args:
            name: 收集器名称
            
        Returns:
            是否成功注销
        """
        return self.collector_manager.unregister_collector(name)
    
    def enable_collector(self, name: str) -> bool:
        """
        启用收集器
        
        Args:
            name: 收集器名称
            
        Returns:
            是否成功启用
        """
        return self.collector_manager.enable_collector(name)
    
    def disable_collector(self, name: str) -> bool:
        """
        禁用收集器
        
        Args:
            name: 收集器名称
            
        Returns:
            是否成功禁用
        """
        return self.collector_manager.disable_collector(name)
    
    def get_collector_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有收集器的状态
        
        Returns:
            收集器状态字典
        """
        return self.collector_manager.get_collector_status()
    
    def get_available_collectors(self) -> List[str]:
        """
        获取可用的收集器列表
        
        Returns:
            收集器名称列表
        """
        return list(self.collector_manager.get_all_collectors().keys())
    
    def get_enabled_collectors(self) -> List[str]:
        """
        获取已启用的收集器列表
        
        Returns:
            已启用的收集器名称列表
        """
        enabled = []
        for name, collector in self.collector_manager.get_all_collectors().items():
            if collector.is_enabled():
                enabled.append(name)
        return enabled
    
    def reset(self):
        """重置收集器状态"""
        self.collector_manager.reset_all_collectors()
        self.logger.debug("重置性能收集器")
