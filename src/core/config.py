"""
配置管理模块

管理项目的所有配置项
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ChromeConfig:
    """Chrome浏览器配置"""
    chrome_path: str = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    debug_port: int = 9222
    headless: bool = False
    disable_gpu: bool = True
    no_sandbox: bool = True
    disable_dev_shm_usage: bool = True
    inherit_cookies: bool = True


@dataclass
class CollectionConfig:
    """数据收集配置"""
    wait_time: int = 10
    timeout: int = 30
    max_retries: int = 3
    enable_network: bool = True
    enable_performance: bool = True
    enable_memory: bool = True


@dataclass
class AnalysisConfig:
    """分析配置"""
    large_resource_threshold: int = 1024 * 1024  # 1MB
    slow_request_threshold: float = 1000  # 1秒
    api_patterns: list = field(default_factory=lambda: [
        r'/api/', r'/rest/', r'/graphql', r'/v1/', r'/v2/'
    ])


@dataclass
class ReportConfig:
    """报告配置"""
    output_dir: str = "reports"
    template_dir: str = "templates"
    max_response_size: int = 1024 * 1024  # 1MB
    include_response_body: bool = True


class Config:
    """主配置类"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.chrome = ChromeConfig()
        self.collection = CollectionConfig()
        self.analysis = AnalysisConfig()
        self.report = ReportConfig()
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """从文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'chrome' in data:
                self._update_chrome_config(data['chrome'])
            if 'collection' in data:
                self._update_collection_config(data['collection'])
            if 'analysis' in data:
                self._update_analysis_config(data['analysis'])
            if 'report' in data:
                self._update_report_config(data['report'])
                
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {e}")
    
    def _update_chrome_config(self, data: Dict[str, Any]):
        """更新Chrome配置"""
        for key, value in data.items():
            if hasattr(self.chrome, key):
                setattr(self.chrome, key, value)
    
    def _update_collection_config(self, data: Dict[str, Any]):
        """更新收集配置"""
        for key, value in data.items():
            if hasattr(self.collection, key):
                setattr(self.collection, key, value)
    
    def _update_analysis_config(self, data: Dict[str, Any]):
        """更新分析配置"""
        for key, value in data.items():
            if hasattr(self.analysis, key):
                setattr(self.analysis, key, value)
    
    def _update_report_config(self, data: Dict[str, Any]):
        """更新报告配置"""
        for key, value in data.items():
            if hasattr(self.report, key):
                setattr(self.report, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'chrome': self.chrome.__dict__,
            'collection': self.collection.__dict__,
            'analysis': self.analysis.__dict__,
            'report': self.report.__dict__
        }
    
    def save_to_file(self, config_file: str):
        """保存到文件"""
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False) 