"""
Chrome 进程管理模块

负责检测现有 Chrome 进程、启动新的 Chrome 实例、获取调试端口等功能
"""

import subprocess
import psutil
import requests
import time
import json
import logging
from typing import Optional, List, Dict

class ChromeManager:
    """Chrome 进程管理器"""
    
    def __init__(self, chrome_path: Optional[str] = None, debug_port: int = 9222):
        """
        初始化 Chrome 管理器
        
        Args:
            chrome_path: Chrome 可执行文件路径，None 时自动检测
            debug_port: 调试端口号
        """
        self.debug_port = debug_port
        self.chrome_process = None
        self.logger = logging.getLogger(__name__)
        self.chrome_path = chrome_path or self._find_chrome_path()
    
    def _find_chrome_path(self) -> str:
        """
        自动检测 Chrome 可执行文件路径
        
        Returns:
            Chrome 可执行文件路径
            
        Raises:
            FileNotFoundError: 找不到 Chrome 时抛出
        """
        common_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            'google-chrome',
            'chromium'
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.logger.info(f"找到 Chrome: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        raise FileNotFoundError("未找到 Chrome 可执行文件")
    
    def is_chrome_running_with_debug(self) -> bool:
        """
        检查是否已有 Chrome 实例在指定端口运行调试模式
        
        Returns:
            True 如果已有实例在运行
        """
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json/version', 
                                  timeout=2)
            if response.status_code == 200:
                self.logger.info(f"检测到现有 Chrome 调试实例 (端口 {self.debug_port})")
                return True
        except requests.RequestException:
            pass
        return False
    
    def start_chrome(self, headless: bool = False, extra_args: List[str] = None) -> bool:
        """
        启动新的 Chrome 实例（如果需要）
        
        Args:
            headless: 是否以无头模式启动
            extra_args: 额外的启动参数
            
        Returns:
            True 如果成功启动或已有实例运行
        """
        if self.is_chrome_running_with_debug():
            return True
        
        args = [
            self.chrome_path,
            f'--remote-debugging-port={self.debug_port}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--user-data-dir=/tmp/chrome-performance-test',  # 使用独立的数据目录
            '--disable-extensions',
            '--disable-default-apps',
        ]
        
        if headless:
            args.append('--headless')
        
        if extra_args:
            args.extend(extra_args)
        
        try:
            self.logger.info(f"启动 Chrome: {' '.join(args)}")
            self.chrome_process = subprocess.Popen(args, 
                                                 stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
            
            # 等待 Chrome 启动
            for _ in range(30):  # 最多等待 30 秒
                time.sleep(1)
                if self.is_chrome_running_with_debug():
                    self.logger.info("Chrome 启动成功")
                    return True
            
            self.logger.error("Chrome 启动超时")
            return False
            
        except Exception as e:
            self.logger.error(f"启动 Chrome 失败: {e}")
            return False
    
    def get_tabs(self) -> List[Dict]:
        """
        获取所有标签页信息
        
        Returns:
            标签页信息列表
        """
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException as e:
            self.logger.error(f"获取标签页信息失败: {e}")
        return []
    
    def create_new_tab(self, url: str = "about:blank") -> Optional[Dict]:
        """
        创建新标签页
        
        Args:
            url: 新标签页要打开的URL
            
        Returns:
            新标签页信息，失败时返回 None
        """
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
        """
        关闭指定标签页
        
        Args:
            tab_id: 标签页ID
            
        Returns:
            True 如果成功关闭
        """
        try:
            response = requests.delete(
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
        """清理资源，关闭启动的 Chrome 进程"""
        if self.chrome_process:
            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=5)
                self.logger.info("Chrome 进程已关闭")
            except subprocess.TimeoutExpired:
                self.chrome_process.kill()
                self.logger.warning("强制关闭 Chrome 进程")
            except Exception as e:
                self.logger.error(f"关闭 Chrome 进程失败: {e}")
            finally:
                self.chrome_process = None
