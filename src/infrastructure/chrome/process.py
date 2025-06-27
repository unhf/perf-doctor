"""
Chrome进程管理模块

管理Chrome进程的启动、停止和状态检查
"""

import subprocess
import psutil
import time
import logging
import os
import platform
from typing import Optional, List, Dict
from pathlib import Path

from ...core.exceptions import ChromeException


class ChromeProcess:
    """Chrome进程管理器"""
    
    def __init__(self, chrome_path: str, debug_port: int = 9222):
        self.chrome_path = chrome_path
        self.debug_port = debug_port
        self.process = None
        self.logger = logging.getLogger(__name__)
    
    def start(self, headless: bool = False, user_data_dir: str = None, 
              extra_args: List[str] = None) -> bool:
        """启动Chrome进程"""
        if self.is_running():
            self.logger.info("Chrome进程已在运行")
            return True
        
        args = [
            self.chrome_path,
            f'--remote-debugging-port={self.debug_port}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-extensions',
            '--disable-default-apps',
        ]
        
        if user_data_dir:
            args.append(f'--user-data-dir={user_data_dir}')
        
        if headless:
            args.append('--headless')
        
        if extra_args:
            args.extend(extra_args)
        
        try:
            self.logger.info(f"启动Chrome: {' '.join(args)}")
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 等待启动
            for _ in range(30):
                time.sleep(1)
                if self.is_running():
                    self.logger.info("Chrome启动成功")
                    return True
            
            self.logger.error("Chrome启动超时")
            return False
            
        except Exception as e:
            self.logger.error(f"启动Chrome失败: {e}")
            raise ChromeException(f"启动Chrome失败: {e}")
    
    def stop(self) -> bool:
        """停止Chrome进程"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                self.logger.info("Chrome进程已停止")
                return True
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.logger.warning("强制终止Chrome进程")
                return True
            except Exception as e:
                self.logger.error(f"停止Chrome进程失败: {e}")
                return False
        return True
    
    def is_running(self) -> bool:
        """检查Chrome进程是否运行"""
        if self.process:
            return self.process.poll() is None
        return False
    
    def get_pid(self) -> Optional[int]:
        """获取进程ID"""
        if self.process:
            return self.process.pid
        return None
    
    def find_chrome_path(self) -> str:
        """自动检测Chrome路径"""
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
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.logger.info(f"找到Chrome: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        raise ChromeException("未找到Chrome可执行文件")
    
    def find_existing_process(self) -> Optional[Dict[str, str]]:
        """查找现有的Chrome进程"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('--remote-debugging-port' in arg for arg in cmdline):
                        return {
                            'pid': str(proc.info['pid']),
                            'name': proc.info['name'],
                            'cmdline': ' '.join(cmdline) if cmdline else ''
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None 