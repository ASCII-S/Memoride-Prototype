"""
标签页模块
包含应用程序的各个功能标签页
"""

from ui.tabs.base import BaseTab
from ui.tabs.file import FileProcessingTab
from ui.tabs.chat import ChatTab
from ui.tabs.sup import SupportTab
# 导入其他标签页...

__all__ = [
    'BaseTab',
    'ModelManagerTab',
    'FileProcessingTab',
    'ChatTab',
    'SupportTab',
    # 其他标签页...
]