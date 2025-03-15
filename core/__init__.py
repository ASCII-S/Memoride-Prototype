"""
核心功能模块，提供日志、配置和错误处理等基础服务。
"""

# 导出主要类，使其可以通过 from core import X 直接导入
from .error_handler import ErrorHandler
from .api import get_api_handler
from .config import Config
from .config_manager import ConfigManager
from .logging import Logger
from .models import OllamaModelManager, RemoteApiManager, ModelLoader, ModelManager

# 版本信息
__all__ = ['Logger', 'Config', 'ConfigManager', 'ErrorHandler', 'get_api_handler', 'OllamaModelManager', 'RemoteApiManager', 'ModelLoader', 'ModelManager']