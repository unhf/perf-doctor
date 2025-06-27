"""
DevTools事件处理模块

处理DevTools的各种事件
"""

import logging
from typing import Dict, Any, Callable, List
from dataclasses import dataclass, field


@dataclass
class DevToolsEvent:
    """DevTools事件"""
    method: str
    params: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: __import__('time').time())


class DevToolsEvents:
    """DevTools事件处理器"""
    
    def __init__(self):
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_handler(self, event_name: str, handler: Callable[[Dict[str, Any]], None]):
        """添加事件处理器"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
        self.logger.debug(f"添加事件处理器: {event_name}")
    
    def remove_handler(self, event_name: str, handler: Callable[[Dict[str, Any]], None]):
        """移除事件处理器"""
        if event_name in self.event_handlers:
            try:
                self.event_handlers[event_name].remove(handler)
                self.logger.debug(f"移除事件处理器: {event_name}")
            except ValueError:
                pass
    
    def handle_event(self, event: DevToolsEvent):
        """处理事件"""
        method = event.method
        params = event.params
        
        if method in self.event_handlers:
            for handler in self.event_handlers[method]:
                try:
                    handler(params)
                except Exception as e:
                    self.logger.error(f"事件处理器错误 {method}: {e}")
        
        self.logger.debug(f"收到事件: {method}")
    
    def get_handler_count(self, event_name: str) -> int:
        """获取事件处理器数量"""
        return len(self.event_handlers.get(event_name, []))
    
    def clear_handlers(self, event_name: str = None):
        """清除事件处理器"""
        if event_name:
            self.event_handlers.pop(event_name, None)
        else:
            self.event_handlers.clear()
        self.logger.debug(f"清除事件处理器: {event_name or 'all'}")


# 常用事件名称常量
class EventNames:
    """事件名称常量"""
    
    # 网络事件
    NETWORK_REQUEST_WILL_BE_SENT = "Network.requestWillBeSent"
    NETWORK_RESPONSE_RECEIVED = "Network.responseReceived"
    NETWORK_LOADING_FINISHED = "Network.loadingFinished"
    NETWORK_LOADING_FAILED = "Network.loadingFailed"
    NETWORK_DATA_RECEIVED = "Network.dataReceived"
    
    # 页面事件
    PAGE_LOAD_EVENT_FIRED = "Page.loadEventFired"
    PAGE_DOM_CONTENT_EVENT_FIRED = "Page.domContentEventFired"
    PAGE_FRAME_NAVIGATED = "Page.frameNavigated"
    PAGE_FRAME_STARTED_LOADING = "Page.frameStartedLoading"
    PAGE_FRAME_STOPPED_LOADING = "Page.frameStoppedLoading"
    
    # 运行时事件
    RUNTIME_EXECUTION_CONTEXT_CREATED = "Runtime.executionContextCreated"
    RUNTIME_EXECUTION_CONTEXTS_CLEARED = "Runtime.executionContextsCleared"
    
    # 性能事件
    PERFORMANCE_METRICS = "Performance.metrics" 