"""
核心功能模块，提供日志、配置和错误处理等基础服务。
"""

# 导出主要类，使其可以通过 from core import X 直接导入
from core.error_handler import ErrorHandler
from core.api import get_api_handler
from core.config import Config
from core.config_manager import ConfigManager
from core.logging import Logger
from core.models import OllamaModelManager, RemoteApiManager, ModelLoader, ModelManager

# 版本信息
__all__ = ['Logger', 'Config', 'ConfigManager', 'ErrorHandler', 'get_api_handler', 'OllamaModelManager', 'RemoteApiManager', 'ModelLoader', 'ModelManager']