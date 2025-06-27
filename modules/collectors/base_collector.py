"""
基础收集器接口

定义所有性能数据收集器插件必须实现的接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..devtools_client import DevToolsClient


class BaseCollector(ABC):
    """性能数据收集器基础接口"""
    
    def __init__(self, devtools_client: DevToolsClient, name: str = None):
        """
        初始化收集器
        
        Args:
            devtools_client: DevTools 客户端实例
            name: 收集器名称
        """
        self.client = devtools_client
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        self.enabled = True
        self.data = {}
        
    @abstractmethod
    async def setup(self) -> bool:
        """
        设置收集器，启用必要的域和事件监听
        
        Returns:
            设置是否成功
        """
        pass
    
    @abstractmethod
    async def collect(self) -> Dict[str, Any]:
        """
        收集性能数据
        
        Returns:
            收集到的数据字典
        """
        pass
    
    @abstractmethod
    def get_required_domains(self) -> list:
        """
        获取此收集器需要的 DevTools 域列表
        
        Returns:
            域名称列表
        """
        pass
    
    def enable(self):
        """启用收集器"""
        self.enabled = True
        self.logger.debug(f"收集器 {self.name} 已启用")
    
    def disable(self):
        """禁用收集器"""
        self.enabled = False
        self.logger.debug(f"收集器 {self.name} 已禁用")
    
    def is_enabled(self) -> bool:
        """检查收集器是否启用"""
        return self.enabled
    
    def reset(self):
        """重置收集器状态"""
        self.data = {}
        self.logger.debug(f"收集器 {self.name} 已重置")
    
    def get_name(self) -> str:
        """获取收集器名称"""
        return self.name
    
    def get_description(self) -> str:
        """获取收集器描述"""
        return getattr(self, '__doc__', f"{self.name} 收集器") 