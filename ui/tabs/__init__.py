"""
标签页模块
包含应用程序的各个功能标签页
"""

from .base import BaseTab
from .file import FileProcessingTab
from .chat import ChatTab
from .sup import SupportTab
# 导入其他标签页...

__all__ = [
    'BaseTab',
    'ModelManagerTab',
    'FileProcessingTab',
    'ChatTab',
    'SupportTab',
    # 其他标签页...
]