"""
标签页基类模块
为所有标签页提供通用功能
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox
from core import Config

class BaseTab(QWidget):
    def __init__(self, api_handler):
        super().__init__()
        self.api_handler = api_handler
        self.model_selector = QComboBox()  # 保留引用但不显示在UI中
        self.init_ui()
        self.model_selector.currentTextChanged.connect(Config.update_selected_model)
        self.model_selector.setCurrentText(Config.SELECTED_MODEL)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        # 不再添加model_selector到布局中

    def update_model_list(self, models):
        self.model_selector.clear()
        self.model_selector.addItems([model['name'] for model in models])