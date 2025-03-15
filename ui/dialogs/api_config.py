from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt

from core import Config

class ApiConfigDialog(QDialog):
    """API配置对话框"""
    
    def __init__(self, parent=None, config_name="", config_index=-1):
        super().__init__(parent)
        self.is_editing = config_index >= 0
        self.config_index = config_index
        self.config_name = config_name
        
        if self.is_editing:
            self.setWindowTitle(f"编辑配置 - {config_name}")
        else:
            self.setWindowTitle("新增远程API配置")
            # 新建配置时使用空白值
            self.config_name = ""
            
        self.setMinimumWidth(450)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 添加说明文本
        description = QLabel("配置连接到远程大语言模型API的参数。请确保您有有效的API密钥和访问权限。")
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description)
        
        # 配置名称
        self.name_input = QLineEdit(self.config_name)
        self.name_input.setPlaceholderText("例如: deepseek")
        self.name_input.textChanged.connect(self.validate_name)  # 添加文本变化监听
        layout.addWidget(QLabel("配置名称:"))
        layout.addWidget(self.name_input)
        
        # 添加名称验证提示标签
        self.name_validation_label = QLabel("")
        self.name_validation_label.setStyleSheet("color: red; font-size: 10px;")
        layout.addWidget(self.name_validation_label)
        
        # 连接信息分组
        connection_group = QGroupBox("API连接信息")
        connection_layout = QFormLayout(connection_group)
        
        # API URL
        api_url = ""
        if self.is_editing:
            api_url = Config.REMOTE_API_URL
        # 新建模式不设置默认URL
        
        self.api_url_input = QLineEdit(api_url)
        self.api_url_input.setPlaceholderText("例如: https://api.deepseek.com")
        connection_layout.addRow("API基础URL:", self.api_url_input)
        
        # API Key
        api_key = Config.REMOTE_API_KEY if self.is_editing else ""
        self.api_key_input = QLineEdit(api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("输入您的API密钥")
        connection_layout.addRow("API密钥:", self.api_key_input)
        
        # 添加帮助链接
        help_link = QLabel("需要API密钥？<a href='https://platform.deepseek.com'>点击此处</a>前往DeepSeek平台注册获取")
        help_link.setOpenExternalLinks(True)  # 允许打开外部链接
        help_link.setTextFormat(Qt.RichText)
        help_link.setStyleSheet("font-size: 12px; color: #666;")
        connection_layout.addRow("", help_link)
        # 也可以通过联系作者邮箱获取密钥
        help_link2 = QLabel("也可以通过联系作者QQ或邮箱获取密钥：<a href='mailto:1600014464@qq.com'>1600014464@qq.com</a>")
        help_link2.setOpenExternalLinks(True)  # 允许打开外部链接
        help_link2.setTextFormat(Qt.RichText)
        help_link2.setStyleSheet("font-size: 12px; color: #666;")
        connection_layout.addRow("", help_link2)


        # 测试连接按钮和状态标签
        test_button_layout = QHBoxLayout()
        test_connection_btn = QPushButton("测试连接")
        test_connection_btn.clicked.connect(self.test_api_connection)
        test_button_layout.addWidget(test_connection_btn)
        
        self.connection_status = QLabel("")
        self.connection_status.setStyleSheet("color: #666;")
        test_button_layout.addWidget(self.connection_status)
        test_button_layout.addStretch()
        
        connection_layout.addRow("", test_button_layout)
        
        layout.addWidget(connection_group)
        
        # 模型配置分组
        model_group = QGroupBox("模型设置")
        model_layout = QFormLayout(model_group)
        
        # 模型名称
        if self.is_editing and Config.REMOTE_API_MODELS:
            # 如果在编辑模式且有模型列表，使用第一个模型作为默认值
            model_name = Config.REMOTE_API_MODELS[0] if Config.REMOTE_API_MODELS else ""
        else:
            # 新建模式使用空白值
            model_name = ""
            
        self.model_input = QLineEdit(model_name)
        self.model_input.setPlaceholderText("例如：deepseek-chat 或 deepseek-reasoner")
        self.model_info = QLabel("请输入要使用的模型名称。deepseek建议使用deepseek-chat。")
        self.model_info.setWordWrap(True)
        self.model_info.setStyleSheet("color: #666; font-size: 12px;")
        
        model_layout.addRow("模型名称:", self.model_input)
        model_layout.addRow("", self.model_info)
        
        layout.addWidget(model_group)
        
        # 按钮区域
        button_box = QDialogButtonBox()
        
        # 添加标准按钮
        self.ok_button = button_box.addButton(QDialogButtonBox.Ok)
        self.ok_button.clicked.connect(self.validate_and_accept)
        button_box.addButton(QDialogButtonBox.Cancel)
        
        # 如果是编辑模式，添加删除按钮
        if self.is_editing:
            delete_button = button_box.addButton("删除配置", QDialogButtonBox.DestructiveRole)
            delete_button.clicked.connect(self.delete_config)
            delete_button.setStyleSheet("background-color: #f44336; color: white;")
        
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 初始验证名称
        self.validate_name()
    
    def validate_name(self):
        """验证配置名称是否有效"""
        name = self.name_input.text().strip()
        self.name_validation_label.setText("")
        self.ok_button.setEnabled(True)
        
        if not name:
            self.name_validation_label.setText("配置名称不能为空")
            self.ok_button.setEnabled(False)
            return
            
        # 检查是否重复（排除当前编辑的配置）
        for i, config in enumerate(Config.REMOTE_API_CONFIGS):
            if i != self.config_index and config.get('name', '').strip() == name:
                self.name_validation_label.setText("配置名称已存在，请使用其他名称")
                self.ok_button.setEnabled(False)
                return
    
    def validate_and_accept(self):
        """验证所有输入并接受对话框"""
        # 验证名称
        name = self.name_input.text().strip()
        if not name:
            self.name_validation_label.setText("配置名称不能为空")
            return
            
        # 检查是否重复
        for i, config in enumerate(Config.REMOTE_API_CONFIGS):
            if i != self.config_index and config.get('name', '').strip() == name:
                self.name_validation_label.setText("配置名称已存在，请使用其他名称")
                return
        
        # 验证URL
        url = self.api_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "验证失败", "API基础URL不能为空")
            return
            
        # 验证API密钥
        key = self.api_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "验证失败", "API密钥不能为空")
            return
            
        # 验证模型名称
        model = self.model_input.text().strip()
        if not model:
            QMessageBox.warning(self, "验证失败", "模型名称不能为空")
            return
        
        # 所有验证通过，接受对话框
        self.accept()
    
    def test_api_connection(self):
        """测试API连接功能"""
        url = self.api_url_input.text().strip()
        key = self.api_key_input.text().strip()
        
        if not url:
            self.connection_status.setText("错误: URL不能为空")
            self.connection_status.setStyleSheet("color: red;")
            return
            
        if not key:
            self.connection_status.setText("错误: API密钥不能为空")
            self.connection_status.setStyleSheet("color: red;")
            return
            
        self.connection_status.setText("正在测试连接...")
        self.connection_status.setStyleSheet("color: #666;")
        QApplication.processEvents()  # 刷新UI
        
        # 创建临时API处理器进行测试
        from core.api import RemoteAPIHandler
        import json
        
        # 保存当前配置
        old_url = Config.REMOTE_API_URL
        old_key = Config.REMOTE_API_KEY
        
        # 设置临时配置
        Config.REMOTE_API_URL = url
        Config.REMOTE_API_KEY = key
        
        try:
            handler = RemoteAPIHandler()
            # 测试模型列表API是否可访问
            if "deepseek.com" in url.lower():
                response = handler._get_request("/v1/models")
            else:
                response = handler._get_request("/models")
            
            # 恢复旧配置
            Config.REMOTE_API_URL = old_url
            Config.REMOTE_API_KEY = old_key
            
            if "error" in response:
                self.connection_status.setText(f"连接失败: {response.get('error')}")
                self.connection_status.setStyleSheet("color: red;")
            else:
                self.connection_status.setText("连接成功! API可访问")
                self.connection_status.setStyleSheet("color: green;")
                
                # 如果能解析出模型列表，自动填充第一个模型
                available_models = []
                if "data" in response and isinstance(response["data"], list):
                    # OpenAI格式
                    available_models = [m.get("id") for m in response["data"] if m.get("id")]
                elif "models" in response and isinstance(response["models"], list):
                    # 通用格式
                    available_models = [m.get("name") for m in response["models"] if m.get("name")]
                    
                if available_models:
                    # 只填充第一个模型
                    self.model_input.setText(available_models[0])
                    self.model_info.setText(f"自动选择首个可用模型，共检测到{len(available_models)}个模型")
                    self.model_info.setStyleSheet("color: green; font-size: 10px;")
                
        except Exception as e:
            # 恢复旧配置
            Config.REMOTE_API_URL = old_url
            Config.REMOTE_API_KEY = old_key
            
            self.connection_status.setText(f"测试出错: {str(e)}")
            self.connection_status.setStyleSheet("color: red;")
    
    def delete_config(self):
        """删除当前配置"""
        if self.config_index < 0 or self.config_index >= len(Config.REMOTE_API_CONFIGS):
            return
            
        confirm = QMessageBox.question(
            self, 
            "删除确认", 
            f"确定要删除配置 '{self.config_name}' 吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # 删除配置
            Config.REMOTE_API_CONFIGS.pop(self.config_index)
            
            # 调整当前选中的配置索引
            if Config.CURRENT_REMOTE_CONFIG_INDEX >= len(Config.REMOTE_API_CONFIGS):
                Config.CURRENT_REMOTE_CONFIG_INDEX = len(Config.REMOTE_API_CONFIGS) - 1 if Config.REMOTE_API_CONFIGS else -1
            
            # 更新当前活动的配置参数
            if Config.REMOTE_API_CONFIGS and Config.CURRENT_REMOTE_CONFIG_INDEX >= 0:
                config = Config.REMOTE_API_CONFIGS[Config.CURRENT_REMOTE_CONFIG_INDEX]
                Config.REMOTE_API_URL = config.get("url", "")
                Config.REMOTE_API_KEY = config.get("key", "")
                Config.REMOTE_API_MODELS = config.get("models", [])
            else:
                # 如果没有配置了，清空当前配置
                Config.REMOTE_API_URL = ""
                Config.REMOTE_API_KEY = ""
                Config.REMOTE_API_MODELS = []
            
            # 保存配置
            Config.save_config()
            
            # 接受对话框结果，但设置特殊结果代码
            self.done(2)  # 使用2表示删除操作
    
    def get_config_data(self):
        """获取对话框中的配置数据"""
        return {
            "name": self.name_input.text().strip(),
            "url": self.api_url_input.text().strip(),
            "key": self.api_key_input.text().strip(),
            "models": [self.model_input.text().strip()]
        }
