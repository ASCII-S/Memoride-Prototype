"""
远程API管理器模块
处理远程API配置的选择和更新
"""

from core import Config, ConfigManager
from PyQt5.QtWidgets import QComboBox

class RemoteApiManager:
    def __init__(self, model_selector: QComboBox):
        self.model_selector = model_selector

    def update_remote_config_selector(self):
        """更新远程API配置选择器的内容"""
        if Config.MODEL_SOURCE != '远程API模型':
            # 如果不是远程API模式，不更新配置选择器
            print("不是远程API模式，跳过更新配置选择器")
            return
            
        print(f"更新远程API配置选择器，当前有{len(Config.REMOTE_API_CONFIGS)}个配置")
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        
        # 添加现有配置
        for config in Config.REMOTE_API_CONFIGS:
            config_name = config.get('name', '未命名配置')
            print(f"添加配置项：{config_name}")
            self.model_selector.addItem(config_name)
            
        # 添加"新增配置"选项
        self.model_selector.addItem('+ 新增配置')
        
        # 设置当前选中的配置
        if 0 <= Config.CURRENT_REMOTE_CONFIG_INDEX < len(Config.REMOTE_API_CONFIGS):
            self.model_selector.setCurrentIndex(Config.CURRENT_REMOTE_CONFIG_INDEX)
            print(f"选择配置索引：{Config.CURRENT_REMOTE_CONFIG_INDEX}")
        elif Config.REMOTE_API_CONFIGS:
            # 如果有配置但没有设置当前配置索引，选择第一个
            self.model_selector.setCurrentIndex(0)
            print("选择第一个配置")
        else:
            # 没有配置，默认选择"新增配置"选项
            new_config_index = self.model_selector.count() - 1  # "新增配置"选项的索引
            self.model_selector.setCurrentIndex(new_config_index)
            print("没有配置，选择新增配置选项")
            
        # 确保选择器被启用
        self.model_selector.setEnabled(True)
            
        self.model_selector.blockSignals(False)
        print("远程API配置选择器更新完成")
    
    def open_new_config_dialog(self):
        """打开新增远程API配置对话框 - 现在直接调用open_api_config_dialog方法"""
        # 保存当前模型选择器状态，以便在对话框被取消时恢复
        current_index = self.model_selector.currentIndex()
        current_text = self.model_selector.currentText()
        
        # 用新的统一界面替代原来的新增配置对话框，确保传递is_new_config=True
        self.open_api_config_dialog(is_new_config=True)
        
        # 注意: 以下代码不再需要，因为已经在open_api_config_dialog中处理了所有逻辑
        # 这里只需调用其他方法并确保返回即可
        return
    
    def populate_model_selector_from_cache(self):
        """使用缓存填充模型选择器"""
        self.model_selector.clear()
        self.model_selector.setEnabled(True)
        
        if self.local_models_cache:
            self.model_selector.addItems(self.local_models_cache)
            
            # 如果有默认模型，选择它
            if Config.SELECTED_MODEL in self.local_models_cache:
                self.model_selector.setCurrentText(Config.SELECTED_MODEL)
            else:
                # 否则选择第一个模型并更新配置
                first_model = self.local_models_cache[0]
                self.model_selector.setCurrentText(first_model)
                ConfigManager.select_model(first_model)
        else:
            # 缓存为空（不应该发生，但以防万一）
            self.model_selector.addItem('模型加载失败')
            
    def on_model_selector_activated(self, index):
        """当用户点击模型选择器时触发，即使选择的项没有变化"""
        # 获取当前选择的文本
        current_text = self.model_selector.currentText()
        
        # 如果是远程API模型模式且当前选择是新增配置
        if Config.MODEL_SOURCE == '远程API模型' and current_text == '+ 新增配置':
            # 直接打开新增配置对话框
            self.open_api_config_dialog(is_new_config=True)
