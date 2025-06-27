"""
DevTools通信模块

提供与Chrome DevTools的WebSocket通信功能
"""

from .client import DevToolsClient
from .commands import DevToolsCommands
from .events import DevToolsEvents

__all__ = [
    'DevToolsClient',
    'DevToolsCommands',
    'DevToolsEvents'
] 