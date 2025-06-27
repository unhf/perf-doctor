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
import os
import platform
from typing import Optional, List, Dict
from pathlib import Path

class ChromeManager:
    """Chrome 进程管理器"""
    
    def __init__(self, chrome_path: Optional[str] = None, debug_port: int = 9222, 
                 inherit_cookies: bool = True, user_data_dir: Optional[str] = None):
        """
        初始化 Chrome 管理器
        
        Args:
            chrome_path: Chrome 可执行文件路径，None 时自动检测
            debug_port: 调试端口号
            inherit_cookies: 是否继承现有 Chrome 的 cookies
            user_data_dir: 用户数据目录，None 时自动检测或创建
        """
        self.debug_port = debug_port
        self.chrome_process = None
        self.inherit_cookies = inherit_cookies
        self.user_data_dir = user_data_dir
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
            self.logger.info("检测到现有 Chrome 调试实例，将复用")
            return True
        
        # 获取要使用的用户数据目录
        user_data_dir = self._get_user_data_dir()
        self.logger.info(f"使用用户数据目录: {user_data_dir}")
        
        # 如果使用默认用户数据目录但主 Chrome 已运行，则复制 cookies 到临时目录
        if (self.inherit_cookies and 
            user_data_dir == self._get_default_user_data_dir() and 
            self._is_main_chrome_running()):
            user_data_dir = self._create_temp_profile_with_cookies(user_data_dir)
            self.logger.info(f"主 Chrome 正在运行，使用临时配置文件: {user_data_dir}")
        
        args = [
            self.chrome_path,
            f'--remote-debugging-port={self.debug_port}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            f'--user-data-dir={user_data_dir}',
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
    
    def _get_default_user_data_dir(self) -> str:
        """
        获取默认的 Chrome 用户数据目录
        
        Returns:
            默认用户数据目录路径
        """
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/Google/Chrome")
        elif system == "Windows":
            return os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
        elif system == "Linux":
            return os.path.expanduser("~/.config/google-chrome")
        else:
            # fallback
            return os.path.expanduser("~/.chrome")
    
    def _find_existing_chrome_process(self) -> Optional[Dict[str, str]]:
        """
        查找现有的 Chrome 进程及其用户数据目录
        
        Returns:
            包含进程信息的字典，如果没找到则返回 None
        """
        try:
            chrome_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info.get('name', '').lower()
                    if proc_name and ('chrome' in proc_name or 'chromium' in proc_name):
                        cmdline = proc.info.get('cmdline') or []
                        
                        # 跳过子进程（通常包含 --type 参数）
                        if any('--type=' in arg for arg in cmdline):
                            continue
                        
                        # 查找用户数据目录参数
                        user_data_dir = None
                        for i, arg in enumerate(cmdline):
                            if arg.startswith('--user-data-dir='):
                                user_data_dir = arg.split('=', 1)[1]
                                break
                            elif arg == '--user-data-dir' and i + 1 < len(cmdline):
                                user_data_dir = cmdline[i + 1]
                                break
                        
                        # 如果没有指定，使用默认目录
                        if not user_data_dir:
                            user_data_dir = self._get_default_user_data_dir()
                        
                        chrome_processes.append({
                            'pid': proc.info['pid'],
                            'user_data_dir': user_data_dir,
                            'cmdline': ' '.join(cmdline)
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 返回第一个找到的主进程
            if chrome_processes:
                # 优先选择有明确用户数据目录参数的进程
                explicit_dir_processes = [p for p in chrome_processes 
                                        if '--user-data-dir' in p['cmdline']]
                if explicit_dir_processes:
                    return explicit_dir_processes[0]
                else:
                    return chrome_processes[0]
                    
        except Exception as e:
            self.logger.debug(f"查找现有 Chrome 进程失败: {e}")
        
        return None
    
    def _get_user_data_dir(self) -> str:
        """
        获取要使用的用户数据目录
        
        Returns:
            用户数据目录路径
        """
        if self.user_data_dir:
            return self.user_data_dir
        
        if self.inherit_cookies:
            # 优先使用默认的用户数据目录（如果存在且有效）
            default_dir = self._get_default_user_data_dir()
            if self._is_valid_user_data_dir(default_dir):
                self.logger.info(f"使用默认用户数据目录: {default_dir}")
                return default_dir
            
            # 如果默认目录无效，尝试查找现有的 Chrome 进程
            existing_chrome = self._find_existing_chrome_process()
            if existing_chrome:
                user_data_dir = existing_chrome['user_data_dir']
                if self._is_valid_user_data_dir(user_data_dir):
                    self.logger.info(f"继承现有 Chrome 的用户数据目录: {user_data_dir}")
                    return user_data_dir
                else:
                    self.logger.warning(f"现有 Chrome 的用户数据目录无效: {user_data_dir}")
            else:
                self.logger.warning("未检测到现有 Chrome 进程")
        
        # 创建独立的测试目录
        test_dir = "/tmp/chrome-performance-test"
        self.logger.info(f"使用独立的测试数据目录: {test_dir}")
        return test_dir
    
    def _is_valid_user_data_dir(self, dir_path: str) -> bool:
        """
        检查用户数据目录是否有效（包含必要的文件）
        
        Args:
            dir_path: 用户数据目录路径
            
        Returns:
            True 如果目录有效
        """
        if not os.path.exists(dir_path):
            return False
        
        # 检查关键文件/目录
        required_items = [
            'Default',                    # 默认配置文件目录
            'Default/Cookies',           # Cookies 文件
            'Default/Preferences',       # 首选项文件
        ]
        
        for item in required_items:
            item_path = os.path.join(dir_path, item)
            if not os.path.exists(item_path):
                self.logger.debug(f"用户数据目录缺少必要文件: {item_path}")
                return False
        
        return True
    
    def _is_main_chrome_running(self) -> bool:
        """
        检查主 Chrome 浏览器是否正在运行
        
        Returns:
            True 如果主 Chrome 正在运行
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info.get('name', '').lower()
                    if proc_name and 'chrome' in proc_name:
                        cmdline = proc.info.get('cmdline') or []
                        
                        # 跳过子进程
                        if any('--type=' in arg for arg in cmdline):
                            continue
                        
                        # 检查是否使用默认用户数据目录（没有显式指定）
                        has_user_data_arg = any('--user-data-dir' in arg for arg in cmdline)
                        if not has_user_data_arg:
                            return True
                        
                        # 检查是否显式使用默认目录
                        default_dir = self._get_default_user_data_dir()
                        for arg in cmdline:
                            if (arg.startswith('--user-data-dir=') and 
                                default_dir in arg):
                                return True
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.debug(f"检查主 Chrome 进程失败: {e}")
        
        return False
    
    def _create_temp_profile_with_cookies(self, source_dir: str) -> str:
        """
        创建临时配置文件并复制 cookies
        
        Args:
            source_dir: 源用户数据目录
            
        Returns:
            临时配置文件目录路径
        """
        import tempfile
        import shutil
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="chrome-perf-", suffix="-profile")
        
        try:
            # 创建 Default 目录
            default_dir = os.path.join(temp_dir, "Default")
            os.makedirs(default_dir, exist_ok=True)
            
            # 复制关键文件
            files_to_copy = [
                'Default/Cookies',
                'Default/Preferences', 
                'Default/Login Data',
                'Default/Web Data',
                'Local State'
            ]
            
            copied_files = []
            for file_path in files_to_copy:
                source_file = os.path.join(source_dir, file_path)
                dest_file = os.path.join(temp_dir, file_path)
                
                if os.path.exists(source_file):
                    try:
                        # 确保目标目录存在
                        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                        shutil.copy2(source_file, dest_file)
                        copied_files.append(file_path)
                    except Exception as e:
                        self.logger.debug(f"复制文件失败 {file_path}: {e}")
            
            if copied_files:
                self.logger.info(f"已复制 {len(copied_files)} 个配置文件到临时目录")
                self.logger.debug(f"复制的文件: {', '.join(copied_files)}")
            else:
                self.logger.warning("未能复制任何配置文件")
            
            return temp_dir
            
        except Exception as e:
            self.logger.error(f"创建临时配置文件失败: {e}")
            # 清理失败的临时目录
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            # 返回独立测试目录作为降级
            return "/tmp/chrome-performance-test"
