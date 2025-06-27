"""
性能服务

提供性能分析的高层服务
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import asdict, is_dataclass

from ..core import Config
from ..collectors import CollectorManager
from ..core.types import ReportData


class PerformanceService:
    """性能服务"""
    
    def __init__(self, collector_manager: CollectorManager, config: Config):
        self.collector_manager = collector_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def collect_performance_data(self, url: str) -> Dict[str, Any]:
        """收集性能数据"""
        self.logger.info(f"开始收集性能数据: {url}")
        
        try:
            # 设置所有收集器
            if not await self.collector_manager.setup_all_collectors():
                raise Exception("设置收集器失败")
            
            # 收集所有数据
            collection_result = await self.collector_manager.collect_all_data()
            
            # 添加URL和时间戳信息
            collection_result['url'] = url
            collection_result['timestamp'] = datetime.now().timestamp()
            
            self.logger.info("性能数据收集完成")
            return collection_result
            
        except Exception as e:
            self.logger.error(f"收集性能数据失败: {e}")
            raise
    
    async def generate_report(self, performance_data: Dict[str, Any]) -> str:
        """生成JSON报告"""
        self.logger.info("开始生成JSON报告")
        
        try:
            # 确保输出目录存在
            os.makedirs(self.config.report.output_dir, exist_ok=True)
            
            # 生成JSON报告
            json_report_path = f"{self.config.report.output_dir}/performance_report.json"
            serializable_data = self._convert_to_serializable(performance_data)
            
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON报告已生成: {json_report_path}")
            return json_report_path
            
        except Exception as e:
            self.logger.error(f"生成JSON报告失败: {e}")
            raise
    
    def _convert_to_serializable(self, data: Any) -> Any:
        """转换数据为可JSON序列化的格式"""
        if is_dataclass(data):
            return asdict(data)
        elif isinstance(data, dict):
            return {k: self._convert_to_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_serializable(item) for item in data]
        elif isinstance(data, (int, float, str, bool, type(None))):
            return data
        else:
            # 对于其他类型，尝试转换为字符串
            return str(data) 