"""
基础收集器类

所有收集器的基类
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from ...core.types import CollectorResult
from ...core.exceptions import CollectorException


class BaseCollector(ABC):
    """基础收集器类"""
    
    def __init__(self, client, name: str, description: str = ""):
        self.client = client
        self.name = name
        self.description = description
        self.enabled = False
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def get_required_domains(self) -> List[str]:
        """获取需要的DevTools域"""
        pass
    
    @abstractmethod
    async def setup(self) -> bool:
        """设置收集器"""
        pass
    
    @abstractmethod
    async def collect(self) -> CollectorResult:
        """收集数据"""
        pass
    
    def reset(self):
        """重置收集器状态"""
        self.enabled = False
        self.logger.debug(f"收集器 {self.name} 已重置")
    
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
    
    def get_status(self) -> Dict[str, Any]:
        """获取收集器状态"""
        return {
            "enabled": self.enabled,
            "name": self.name,
            "description": self.description,
            "required_domains": self.get_required_domains()
        }
    
    async def _enable_required_domains(self) -> bool:
        """启用所需的域"""
        for domain in self.get_required_domains():
            if not await self.client.enable_domain(domain):
                self.logger.error(f"启用域失败: {domain}")
                return False
        return True
    
    def _create_result(self, data: Dict[str, Any], error: str = None) -> CollectorResult:
        """创建收集结果"""
        return CollectorResult(
            type=f"{self.name.lower()}_data",
            data=data,
            timestamp=time.time(),
            error=error
        ) 