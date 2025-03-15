"""
API处理模块
提供不同API处理器的统一接口
"""

import json
from core.config import Config
from core.api.ollama_api_handler import OllamaAPIHandler
from core.api.remote_api_handler import RemoteAPIHandler

def get_api_handler():
    """根据配置选择合适的API处理器"""
    if Config.MODEL_SOURCE == 'Ollama本地模型':
        return OllamaAPIHandler()
    else:
        return RemoteAPIHandler()