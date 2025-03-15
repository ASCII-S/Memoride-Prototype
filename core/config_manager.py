"""
心动记忆 - 主程序入口

一个基于PyQt5的大语言模型交互应用
"""

from core.config import Config

# 配置管理器类
class ConfigManager:
    """处理应用程序配置的管理器类"""
    
    @staticmethod
    def get_current_remote_config():
        """获取当前远程API配置"""
        if 0 <= Config.CURRENT_REMOTE_CONFIG_INDEX < len(Config.REMOTE_API_CONFIGS):
            return Config.REMOTE_API_CONFIGS[Config.CURRENT_REMOTE_CONFIG_INDEX]
        return None
    
    @staticmethod
    def save_remote_config(name, url, key, models, update_index=None):
        """保存远程API配置"""
        if update_index is not None and 0 <= update_index < len(Config.REMOTE_API_CONFIGS):
            # 更新现有配置
            Config.REMOTE_API_CONFIGS[update_index] = {
                "name": name,
                "url": url,
                "key": key,
                "models": models
            }
            # 保持当前选择的配置索引不变
            result_index = update_index
        else:
            # 添加新配置
            Config.REMOTE_API_CONFIGS.append({
                "name": name,
                "url": url,
                "key": key,
                "models": models
            })
            # 新配置的索引是列表末尾
            result_index = len(Config.REMOTE_API_CONFIGS) - 1
        
        # 保存配置
        Config.CURRENT_REMOTE_CONFIG_INDEX = result_index
        Config.REMOTE_API_URL = url
        Config.REMOTE_API_KEY = key
        Config.REMOTE_API_MODELS = models
        Config.save_config()
        
        return result_index
    
    @staticmethod
    def switch_model_source(source):
        """切换模型来源"""
        Config.MODEL_SOURCE = source
        Config.save_config()
    
    @staticmethod
    def select_model(model_name):
        """选择模型"""
        Config.update_selected_model(model_name)
    
    @staticmethod
    def is_valid_remote_config(config_data):
        """验证远程配置数据是否有效"""
        return (
            isinstance(config_data, dict) and
            'name' in config_data and 
            'url' in config_data and 
            config_data['name'] and 
            config_data['url']
        )