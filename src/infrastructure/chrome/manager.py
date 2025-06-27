"""
Chrome管理器模块

管理Chrome实例、标签页和用户数据目录
"""

import requests
import time
import json
import logging
import os
import shutil
import tempfile
from typing import Optional, List, Dict
from pathlib import Path

from .process import ChromeProcess
from ...core.exceptions import ChromeException


class ChromeManager:
    """Chrome管理器"""
    
    def __init__(self, chrome_path: Optional[str] = None, debug_port: int = 9222,
                 inherit_cookies: bool = True, user_data_dir: Optional[str] = None):
        self.debug_port = debug_port
        self.inherit_cookies = inherit_cookies
        self.user_data_dir = user_data_dir
        self.logger = logging.getLogger(__name__)
        
        # 创建Chrome进程管理器
        if chrome_path is None:
            chrome_process = ChromeProcess("", debug_port)
            chrome_path = chrome_process.find_chrome_path()
        
        self.chrome_process = ChromeProcess(chrome_path, debug_port)
    
    def start_chrome(self, headless: bool = False, extra_args: List[str] = None) -> bool:
        """启动Chrome"""
        if self.is_chrome_running_with_debug():
            self.logger.info("检测到现有Chrome调试实例，将复用")
            return True
        
        user_data_dir = self._get_user_data_dir()
        self.logger.info(f"使用用户数据目录: {user_data_dir}")
        
        # 如果使用默认用户数据目录但主Chrome已运行，则复制cookies到临时目录
        if (self.inherit_cookies and 
            user_data_dir == self._get_default_user_data_dir() and 
            self._is_main_chrome_running()):
            user_data_dir = self._create_temp_profile_with_cookies(user_data_dir)
            self.logger.info(f"主Chrome正在运行，使用临时配置文件: {user_data_dir}")
        
        return self.chrome_process.start(headless, user_data_dir, extra_args)
    
    def is_chrome_running_with_debug(self) -> bool:
        """检查是否已有Chrome实例在指定端口运行调试模式"""
        try:
            response = requests.get(
                f'http://localhost:{self.debug_port}/json/version',
                timeout=2
            )
            if response.status_code == 200:
                self.logger.info(f"检测到现有Chrome调试实例 (端口 {self.debug_port})")
                return True
        except requests.RequestException:
            pass
        return False
    
    def get_tabs(self) -> List[Dict]:
        """获取所有标签页信息"""
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException as e:
            self.logger.error(f"获取标签页信息失败: {e}")
        return []
    
    def create_new_tab(self, url: str = "about:blank") -> Optional[Dict]:
        """创建新标签页"""
        try:
            response = requests.put(
                f'http://localhost:{self.debug_port}/json/new?{url}',
                timeout=5
            )
            if response.status_code == 200:
                tab_info = response.json()
                self.logger.info(f"创建新标签页: {tab_info.get('id', 'unknown')}")
                return tab_info
        except requests.RequestException as e:
            self.logger.error(f"创建标签页失败: {e}")
        return None
    
    def close_tab(self, tab_id: str) -> bool:
        """关闭指定标签页"""
        try:
            response = requests.put(
                f'http://localhost:{self.debug_port}/json/close/{tab_id}',
                timeout=5
            )
            if response.status_code == 200:
                self.logger.info(f"关闭标签页: {tab_id}")
                return True
        except requests.RequestException as e:
            self.logger.error(f"关闭标签页失败: {e}")
        return False
    
    def cleanup(self):
        """清理资源"""
        if self.chrome_process:
            self.chrome_process.stop()
    
    def _get_default_user_data_dir(self) -> str:
        """获取默认用户数据目录"""
        if os.name == 'nt':  # Windows
            return os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data')
        elif os.name == 'posix':  # macOS/Linux
            if os.path.exists('/Applications'):  # macOS
                return os.path.expanduser('~/Library/Application Support/Google/Chrome')
            else:  # Linux
                return os.path.expanduser('~/.config/google-chrome')
        else:
            return os.path.expanduser('~/.chrome')
    
    def _get_user_data_dir(self) -> str:
        """获取用户数据目录"""
        if self.user_data_dir:
            return self.user_data_dir
        return self._get_default_user_data_dir()
    
    def _is_main_chrome_running(self) -> bool:
        """检查主Chrome是否运行"""
        existing_process = self.chrome_process.find_existing_process()
        return existing_process is not None
    
    def _create_temp_profile_with_cookies(self, source_dir: str) -> str:
        """创建临时配置文件并复制cookies"""
        temp_dir = tempfile.mkdtemp(prefix='chrome_profile_')
        
        try:
            # 复制cookies文件
            cookies_file = os.path.join(source_dir, 'Default', 'Cookies')
            if os.path.exists(cookies_file):
                temp_cookies_dir = os.path.join(temp_dir, 'Default')
                os.makedirs(temp_cookies_dir, exist_ok=True)
                shutil.copy2(cookies_file, temp_cookies_dir)
                self.logger.info(f"复制cookies到临时目录: {temp_dir}")
        except Exception as e:
            self.logger.warning(f"复制cookies失败: {e}")
        
        return temp_dir 