import os
import json
OLLAMA_API_URL = 'http://localhost:11434'

class Config:
    # 默认模型配置
    DEFAULT_MODEL = 'llama3'
    SELECTED_MODEL = DEFAULT_MODEL
    
    # 模型来源配置（'Ollama本地模型' 或 '远程API模型'）
    MODEL_SOURCE = 'Ollama本地模型'
    
    # 远程API配置
    REMOTE_API_URL = ''
    REMOTE_API_KEY = ''
    REMOTE_API_MODELS = []
    
    # 远程API配置列表
    REMOTE_API_CONFIGS = [
        {
            "name": "DeepSeek Reasoner", 
            "url": "https://api.deepseek.com",
            "key": "",  # 用户需要填写自己的API Key
            "models": ["deepseek-reasoner"]
        }
    ]
    
    # 当前选择的远程API配置索引
    CURRENT_REMOTE_CONFIG_INDEX = 0

    # 配置文件路径
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".ollm_note_flow_config.json")

    @classmethod
    def update_selected_model(cls, model_name):
        cls.SELECTED_MODEL = model_name
        cls.save_config()  # 更新模型后保存配置
        
    REQUEST_TIMEOUT = 30
    
    @classmethod
    def get_model_list_url(cls):
        return f'{cls.OLLAMA_API_URL}/api/tags'

    @classmethod
    def get_chat_completion_url(cls):
        return f'{cls.OLLAMA_API_URL}/api/chat'
        
    @classmethod
    def save_config(cls):
        """保存配置到文件"""
        config_data = {
            "SELECTED_MODEL": cls.SELECTED_MODEL,
            "MODEL_SOURCE": cls.MODEL_SOURCE,
            "REMOTE_API_URL": cls.REMOTE_API_URL,
            "REMOTE_API_KEY": cls.REMOTE_API_KEY,
            "REMOTE_API_MODELS": cls.REMOTE_API_MODELS,
            "REMOTE_API_CONFIGS": cls.REMOTE_API_CONFIGS,
            "CURRENT_REMOTE_CONFIG_INDEX": cls.CURRENT_REMOTE_CONFIG_INDEX
        }
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    @classmethod
    def load_config(cls):
        """从文件加载配置"""
        print(f"尝试从 {cls.CONFIG_FILE} 加载配置...")
        if not os.path.exists(cls.CONFIG_FILE):
            print("配置文件不存在，使用默认配置")
            # 配置文件不存在，使用默认配置
            # 但设置默认的远程API配置
            if cls.REMOTE_API_CONFIGS and cls.CURRENT_REMOTE_CONFIG_INDEX < len(cls.REMOTE_API_CONFIGS):
                config = cls.REMOTE_API_CONFIGS[cls.CURRENT_REMOTE_CONFIG_INDEX]
                cls.REMOTE_API_URL = config.get("url", "")
                cls.REMOTE_API_KEY = config.get("key", "")
                cls.REMOTE_API_MODELS = config.get("models", [])
                print(f"使用默认远程API配置: {config.get('name', '未命名')}")
            return
            
        try:
            with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            print("成功读取配置文件")    
            # 更新配置
            cls.SELECTED_MODEL = config_data.get("SELECTED_MODEL", cls.DEFAULT_MODEL)
            cls.MODEL_SOURCE = config_data.get("MODEL_SOURCE", "Ollama本地模型")
            cls.REMOTE_API_URL = config_data.get("REMOTE_API_URL", "")
            cls.REMOTE_API_KEY = config_data.get("REMOTE_API_KEY", "")
            cls.REMOTE_API_MODELS = config_data.get("REMOTE_API_MODELS", [])
            # 加载多配置支持
            cls.REMOTE_API_CONFIGS = config_data.get("REMOTE_API_CONFIGS", cls.REMOTE_API_CONFIGS)
            cls.CURRENT_REMOTE_CONFIG_INDEX = config_data.get("CURRENT_REMOTE_CONFIG_INDEX", 0)
            
            print(f"已加载配置: MODEL_SOURCE={cls.MODEL_SOURCE}, SELECTED_MODEL={cls.SELECTED_MODEL}")
            print(f"远程API配置数量: {len(cls.REMOTE_API_CONFIGS)}, 当前索引: {cls.CURRENT_REMOTE_CONFIG_INDEX}")
            
            # 确保当前选择的配置是有效的
            if cls.MODEL_SOURCE == "远程API模型" and not cls.REMOTE_API_URL and cls.REMOTE_API_CONFIGS:
                print("远程API模式但URL为空，尝试从配置列表中加载")
                # 如果URL为空但有配置列表，应用第一个配置
                if cls.CURRENT_REMOTE_CONFIG_INDEX < len(cls.REMOTE_API_CONFIGS):
                    config = cls.REMOTE_API_CONFIGS[cls.CURRENT_REMOTE_CONFIG_INDEX]
                    cls.REMOTE_API_URL = config.get("url", "")
                    cls.REMOTE_API_KEY = config.get("key", "")
                    cls.REMOTE_API_MODELS = config.get("models", [])
                    print(f"已从配置列表加载: {config.get('name', '未命名')}")
                
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            
    @classmethod
    def add_remote_config(cls, name, url, key, models):
        """添加新的远程API配置"""
        # 检查是否已存在同名配置
        for i, config in enumerate(cls.REMOTE_API_CONFIGS):
            if config.get("name") == name:
                # 更新现有配置
                cls.REMOTE_API_CONFIGS[i] = {
                    "name": name,
                    "url": url,
                    "key": key,
                    "models": models
                }
                cls.save_config()
                return i  # 返回更新的配置索引
        
        # 添加新配置
        new_config = {
            "name": name,
            "url": url,
            "key": key,
            "models": models
        }
        cls.REMOTE_API_CONFIGS.append(new_config)
        new_index = len(cls.REMOTE_API_CONFIGS) - 1
        cls.save_config()
        return new_index  # 返回新配置的索引
        
    @classmethod
    def switch_remote_config(cls, index):
        """切换远程API配置"""
        print(f"切换远程API配置，请求索引: {index}, 可用配置数量: {len(cls.REMOTE_API_CONFIGS)}")
        if 0 <= index < len(cls.REMOTE_API_CONFIGS):
            cls.CURRENT_REMOTE_CONFIG_INDEX = index
            config = cls.REMOTE_API_CONFIGS[index]
            cls.REMOTE_API_URL = config.get("url", "")
            cls.REMOTE_API_KEY = config.get("key", "")
            cls.REMOTE_API_MODELS = config.get("models", [])
            config_name = config.get("name", "未命名配置")
            print(f"已切换到配置 '{config_name}', API URL: {cls.REMOTE_API_URL}, 模型数量: {len(cls.REMOTE_API_MODELS)}")
            cls.save_config()
            return True
        print(f"切换远程API配置失败: 索引 {index} 超出范围")
        return False

# 启动时加载配置
Config.load_config()
