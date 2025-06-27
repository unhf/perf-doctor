#!/usr/bin/env python3
"""
Chrome浏览器管理模块
负责Chrome浏览器的启动、连接和基本管理
"""

import subprocess
import time
import requests
import psutil


class ChromeManager:
    """Chrome浏览器管理器"""
    
    def __init__(self, debug_port=9222):
        """
        初始化Chrome管理器
        
        Args:
            debug_port (int): Chrome调试端口，默认9222
        """
        self.debug_port = debug_port
        self.chrome_process = None
        
    def is_debug_port_available(self):
        """
        检查调试端口是否可用
        
        Returns:
            bool: True如果端口可用，False否则
        """
        try:
            response = requests.get(
                f'http://localhost:{self.debug_port}/json', 
                timeout=3
            )
            return response.status_code == 200
        except:
            return False
    
    def is_chrome_running(self):
        """
        检查是否有Chrome进程在运行
        
        Returns:
            bool: True如果Chrome在运行，False否则
        """
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    return True
            except:
                pass
        return False
    
    def start_chrome_instance(self):
        """
        启动新的Chrome实例用于性能测试
        
        Returns:
            bool: True如果启动成功，False否则
        """
        try:
            # Chrome启动命令
            chrome_cmd = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                f'--remote-debugging-port={self.debug_port}',
                '--user-data-dir=/tmp/chrome-performance-test',  # 独立数据目录
                '--no-first-run',                               # 跳过首次运行
                '--disable-extensions',                         # 禁用扩展
                '--disable-default-browser-check',              # 禁用默认浏览器检查
                '--new-window',                                 # 新窗口模式
            ]
            
            print("启动专用Chrome测试实例...")
            self.chrome_process = subprocess.Popen(
                chrome_cmd,
                stdout=subprocess.DEVNULL,  # 隐藏输出
                stderr=subprocess.DEVNULL
            )
            
            # 等待Chrome启动并验证调试端口
            return self._wait_for_chrome_startup()
            
        except Exception as e:
            print(f"启动Chrome失败: {e}")
            return False
    
    def _wait_for_chrome_startup(self, max_retries=15):
        """
        等待Chrome启动完成
        
        Args:
            max_retries (int): 最大重试次数
            
        Returns:
            bool: True如果启动成功，False否则
        """
        for i in range(max_retries):
            if self.is_debug_port_available():
                print("Chrome测试实例启动成功")
                return True
            
            print(f"等待Chrome启动... ({i+1}/{max_retries})")
            time.sleep(1)
        
        print("Chrome启动超时")
        return False
    
    def connect_or_start(self):
        """
        连接到现有Chrome或启动新实例
        
        Returns:
            bool: True如果连接成功，False否则
        """
        # 首先尝试连接现有的调试端口
        if self.is_debug_port_available():
            print(f"发现Chrome调试端口{self.debug_port}，使用现有实例")
            return True
        
        # 检查Chrome是否在运行但没有调试端口
        if self.is_chrome_running():
            print("检测到Chrome在运行但无调试端口")
            print("将启动独立的测试实例...")
        
        # 启动新的Chrome测试实例
        return self.start_chrome_instance()
    
    def get_tabs(self):
        """
        获取所有标签页信息
        
        Returns:
            list: 标签页信息列表，失败返回空列表
        """
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json')
            return response.json()
        except Exception as e:
            print(f"获取标签页信息失败: {e}")
            return []
    
    def create_new_tab(self, url=None):
        """
        创建新标签页
        
        Args:
            url (str): 可选的初始URL
            
        Returns:
            dict: 新标签页信息，失败返回None
        """
        try:
            endpoint = f'http://localhost:{self.debug_port}/json/new'
            if url:
                endpoint += f'?{url}'
            
            response = requests.get(endpoint)
            if response.status_code == 200:
                tab_info = response.json()
                print(f"创建新标签页: {tab_info.get('id', 'Unknown')}")
                return tab_info
            return None
        except Exception as e:
            print(f"创建标签页失败: {e}")
            return None
    
    def cleanup(self):
        """清理资源，关闭启动的Chrome进程"""
        if self.chrome_process:
            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=3)
                print("测试专用Chrome实例已关闭")
            except:
                try:
                    self.chrome_process.kill()
                    print("强制关闭测试专用Chrome实例")
                except:
                    pass
            self.chrome_process = None
        else:
            print("已断开Chrome连接（用户实例保持运行）")
