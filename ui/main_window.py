"""
主窗口模块，包含应用程序的主要UI框架。
"""

import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QMessageBox, QDialog,
    QLineEdit, QProgressBar, QFrame,
    QDialogButtonBox, QApplication, QCheckBox
)

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, QUrl
from PyQt5.QtGui import QDesktopServices
import core
from core import Config

# 导入其他UI组件
from .helpers import UIHelper

# 导入对话框组件
from .dialogs import ApiConfigDialog
from core import ModelLoader
# 导入核心组件
from core.config_manager import ConfigManager
from core.logging import Logger

# 这两个模块暂时保留原始导入路径，后续可以重构到core中
from core.api import get_api_handler
from core import OllamaModelManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化管理器和助手类
        self.model_manager = OllamaModelManager(self)
        # self.model_selector_helper = ModelSelectorHelper()
        self.setWindowTitle('Memoride')
        self.setGeometry(100, 100, 900, 650)  # 稍微增加默认窗口大小，提供更好的视觉体验
        
        # 设置默认模型来源为远程API模型
        Config.MODEL_SOURCE = '远程API模型'
        Config.save_config()
    

        # 初始化API处理器
        self.api_handler = get_api_handler()
        
        # 缓存本地模型列表
        self.local_models_cache = []
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)  # 设置统一的边距
        self.layout.setSpacing(8)  # 设置垂直间距

        # 创建菜单栏
        self.create_menu_bar()

        # 顶部控制栏
        self.create_top_control_panel()

        # 初始化UI状态 - 根据当前模型来源设置标签和按钮可见性
        self.update_ui_for_model_source(Config.MODEL_SOURCE)

        # 连接模型来源选择器的信号 - 放在初始化UI后面
        self.model_source_selector.currentTextChanged.connect(self.on_model_source_changed)
        
        # 添加模型选择器变化的监听事件
        self.model_selector.currentTextChanged.connect(self.on_model_changed)
        
        # 添加模型选择器点击事件处理，解决没有配置时点击新增配置无效的问题
        self.model_selector.activated.connect(self.on_model_selector_activated)

        # 初始化选项卡
        self.create_tab_widget()
        
        # 添加操作面板
        self.create_control_panel()
        
        # 根据当前模型来源初始化选择器
        self.initialize_model_selector()
        
        # 如果当前是远程API模式，确保加载远程配置
        if Config.MODEL_SOURCE == '远程API模型':
            # 如果有远程配置，加载第一个配置
            if Config.REMOTE_API_CONFIGS:
                first_config = Config.REMOTE_API_CONFIGS[0]
                Config.CURRENT_REMOTE_CONFIG_INDEX = 0
                Config.REMOTE_API_URL = first_config.get('url', '')
                Config.REMOTE_API_KEY = first_config.get('key', '')
                Config.REMOTE_API_MODELS = first_config.get('models', [])
                Config.save_config()
                
                # 更新UI
                self.update_remote_config_selector()
                self.update_remote_models()
            else:
                # 如果没有远程配置，提示用户添加配置
                QMessageBox.information(self, "远程API模型配置", 
                                      "您需要先配置远程API连接信息才能使用远程模型。",
                                      QMessageBox.Ok)
                self.open_api_config_dialog(is_new_config=True)
        

    
    def create_top_control_panel(self):
        """创建顶部控制面板"""
        # 顶部控制栏 - 使用UIHelper创建带边框的面板
        top_panel, top_bar = UIHelper.create_styled_frame(horizontal=True)
        
        # 添加模型来源选择控件
        model_source_label = UIHelper.create_styled_label('模型来源:', is_title=True)
        self.model_source_selector = UIHelper.create_styled_combo_box(['Ollama本地模型', '远程API模型'])
        
        # 设置默认选择的模型来源
        if Config.MODEL_SOURCE in ['Ollama本地模型', '远程API模型']:
            self.model_source_selector.setCurrentText(Config.MODEL_SOURCE)
        
        # 创建一个模型来源组
        source_group = QWidget()
        source_layout = QHBoxLayout(source_group)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.setSpacing(8)
        source_layout.addWidget(model_source_label)
        source_layout.addWidget(self.model_source_selector)
        
        top_bar.addWidget(source_group)
        
        # 模型/配置选择区域 - 创建一个分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        separator.setFixedWidth(1)
        top_bar.addWidget(separator)
        
        # 创建模型选择组
        model_group = QWidget()
        model_layout = QHBoxLayout(model_group)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(8)
        
        # 创建固定的模型标签对象，以便后续直接访问
        self.model_label = UIHelper.create_styled_label('', is_title=True)
        model_layout.addWidget(self.model_label)
        
        # 统一使用一个选择器，根据当前模式显示不同内容
        self.model_selector = UIHelper.create_styled_combo_box()
        model_layout.addWidget(self.model_selector)
        
        # 添加远程API配置按钮
        self.api_config_btn = UIHelper.create_styled_button('配置')
        self.api_config_btn.clicked.connect(lambda: self.open_api_config_dialog(is_new_config=False))
        model_layout.addWidget(self.api_config_btn)
        
        # 添加刷新本地模型按钮
        self.refresh_btn = UIHelper.create_styled_button('刷新', color="#FF9800", hover_color="#F57C00", pressed_color="#EF6C00")
        self.refresh_btn.clicked.connect(self.refresh_local_models)
        model_layout.addWidget(self.refresh_btn)
        
        # 添加安装模型按钮
        self.install_model_btn = UIHelper.create_styled_button('安装模型', color="#4CAF50", hover_color="#388E3C", pressed_color="#2E7D32")
        self.install_model_btn.clicked.connect(self.model_manager.install_ollama_model)
        model_layout.addWidget(self.install_model_btn)
        
        top_bar.addWidget(model_group)
        top_bar.addStretch()
        self.layout.addWidget(top_panel)
    
    def create_tab_widget(self):
        """创建选项卡控件"""
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                padding: 2px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e6e6e6;
            }
        """)
        self.layout.addWidget(self.tabs, 1)  # 设置拉伸因子为1，使标签页区域占据更多空间
        self.init_ui_components()
    
    def create_control_panel(self):
        """创建底部控制面板"""
        # 创建底部控制面板
        control_panel, control_layout = UIHelper.create_styled_frame(horizontal=True)
        
        # 添加状态信息标签
        status_label = QLabel('状态: 就绪')
        status_label.setStyleSheet("""
            QLabel {
                color: #555;
                font-style: italic;
                padding: 2px 8px;
                border-left: 3px solid #4CAF50;
            }
        """)
        
        # 添加版本信息
        version_label = QLabel('版本: 1.0.0')
        version_label.setStyleSheet("""
            QLabel {
                color: #777;
                font-size: 11px;
            }
        """)
        
        # 添加到布局
        control_layout.addWidget(status_label)
        control_layout.addStretch(1)
        control_layout.addWidget(version_label)
        
        # 添加到主布局
        self.layout.addWidget(control_panel)
    
    def initialize_model_selector(self):
        """根据当前模型来源初始化选择器"""
        if Config.MODEL_SOURCE == 'Ollama本地模型':
            # 如果本地缓存为空，则加载本地模型
            if not self.local_models_cache:
                # 显示加载状态并初始化加载器
                self.model_selector.addItem('加载本地模型中...')
                self.model_selector.setEnabled(False)
                # 初始化模型加载器
                self.init_model_loader()
            else:
                # 使用缓存填充
                self.populate_model_selector_from_cache()
        else:
            # 远程API模式，初始化配置选择器
            self.update_remote_config_selector()
    
    def update_ui_for_model_source(self, source):
        """根据模型来源更新UI元素"""
        # 更新模型标签文本
        if source == 'Ollama本地模型':
            self.model_label.setText('当前使用模型:')
        else:
            self.model_label.setText('远程API配置:')
        
        # 更新按钮可见性
        self.api_config_btn.setVisible(source == '远程API模型')
        self.refresh_btn.setVisible(source == 'Ollama本地模型')
        self.install_model_btn.setVisible(source == 'Ollama本地模型')
    
    def on_model_source_changed(self, source):
        """当模型来源选择改变时，更新模型列表和配置"""
        # 保存到配置
        ConfigManager.switch_model_source(source)
        
        # 更新UI元素状态
        self.update_ui_for_model_source(source)
        
        # 清空并禁用模型选择器，避免旧数据干扰
        self.model_selector.clear()
        self.model_selector.setEnabled(False)
        
        # 重新初始化API处理器
        from core.api import get_api_handler
        self.api_handler = get_api_handler()
        
        # 更新各个标签页中的API处理器
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab, 'api_handler'):
                tab.api_handler = self.api_handler
                
                # 更新系统提示词选择器的可见性（如果存在）
                if hasattr(tab, 'system_prompt_container'):
                    tab.system_prompt_container.setVisible(True)
        
        # 处理模型来源变更后的UI更新
        if source == 'Ollama本地模型':
            # 检查是否有缓存
            if self.local_models_cache:
                print("使用本地模型缓存，跳过加载过程")
                self.populate_model_selector_from_cache()
            else:
                # 没有缓存，需要加载
                self.model_selector.addItem('加载本地模型中...')
                self.init_model_loader()
        else:
            # 远程API模型 - 首先检查是否有历史配置
            self.model_selector.setEnabled(True)  # 启用选择器
            self.update_remote_config_selector()
            
            # 如果没有远程配置，提示用户并打开配置对话框
            if len(Config.REMOTE_API_CONFIGS) == 0:
                print("未发现远程API历史配置，打开配置对话框")
                QMessageBox.information(self, "远程API模型配置", 
                                      "您需要先配置远程API连接信息才能使用远程模型。",
                                      QMessageBox.Ok)
                self.open_api_config_dialog()
    
    def on_model_changed(self, selection):
        """处理模型或配置选择变更"""
        if not selection:
            return
            
        if Config.MODEL_SOURCE == 'Ollama本地模型':
            # 本地模型模式 - 更新所选模型
            self.handle_local_model_selection(selection)
        else:
            # 远程API模式 - 处理配置选择
            self.handle_remote_config_selection(selection)
            
    def handle_local_model_selection(self, model_name):
        """处理本地模型选择"""
        if model_name in ['加载本地模型中...', '模型加载失败']:
            return
            
        # 更新全局配置
        ConfigManager.select_model(model_name)
        
        # 更新各个标签页中的模型选择器
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab, 'model_selector'):
                tab.model_selector.blockSignals(True)  # 阻止信号循环
                tab.model_selector.setCurrentText(model_name)
                tab.model_selector.blockSignals(False)
                
    def handle_remote_config_selection(self, selection):
        """处理远程API配置选择"""
        # 如果选择了"新增配置"
        if selection == '+ 新增配置':
            self.open_api_config_dialog(is_new_config=True)
            return
            
        # 查找并切换到选择的配置
        for i, config in enumerate(Config.REMOTE_API_CONFIGS):
            if config.get('name', '') == selection:
                # 更新当前配置索引
                Config.CURRENT_REMOTE_CONFIG_INDEX = i
                
                # 更新所有配置内容到全局Config
                Config.REMOTE_API_URL = config.get('url', '')
                Config.REMOTE_API_KEY = config.get('key', '')
                Config.REMOTE_API_MODELS = config.get('models', [])
                
                # 保存配置
                Config.save_config()
                
                print(f"完全切换到配置：{selection}，URL：{Config.REMOTE_API_URL[:15]}...")
                
                # 重新初始化API处理器
                from core.api import get_api_handler
                self.api_handler = get_api_handler()
                
                # 更新各个标签页中的API处理器
                for tab_index in range(self.tabs.count()):
                    tab = self.tabs.widget(tab_index)
                    if hasattr(tab, 'api_handler'):
                        tab.api_handler = self.api_handler
                        
                # 加载远程模型
                self.update_remote_models()
                break
    
    def open_api_config_dialog(self, is_new_config=False):
        """打开远程API配置对话框"""
        # 判断是否在编辑现有配置
        config_name = ""
        config_index = -1
        
        # 如果不是新增配置且在远程API模型模式下有当前配置，则认为是在编辑配置
        if not is_new_config and Config.MODEL_SOURCE == '远程API模型' and 0 <= Config.CURRENT_REMOTE_CONFIG_INDEX < len(Config.REMOTE_API_CONFIGS):
            config_index = Config.CURRENT_REMOTE_CONFIG_INDEX
            config = Config.REMOTE_API_CONFIGS[config_index]
            config_name = config.get('name', '未命名配置')
        
        # 创建对话框实例
        dialog = ApiConfigDialog(self, config_name, config_index)
        
        # 显示对话框并获取结果
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # 获取配置数据
            config_data = dialog.get_config_data()
            
            # 保存配置
            ConfigManager.save_remote_config(
                config_data['name'], 
                config_data['url'], 
                config_data['key'], 
                config_data['models'],
                config_index if not is_new_config else None
            )
            
            # 更新配置选择器
            self.update_remote_config_selector()
            
            # 重新初始化API处理器
            from core.api import get_api_handler
            self.api_handler = get_api_handler()
            
            # 更新各个标签页中的模型选择器
            self.update_remote_models()
        elif result == 2:  # 删除操作的特殊返回值
            # 更新配置选择器
            self.update_remote_config_selector()
            
            # 如果删除了当前配置，需要切换到新的当前配置
            if 0 <= Config.CURRENT_REMOTE_CONFIG_INDEX < len(Config.REMOTE_API_CONFIGS):
                # 更新API处理器
                from core.api import get_api_handler
                self.api_handler = get_api_handler()
                
                # 更新模型列表
                self.update_remote_models()
            elif len(Config.REMOTE_API_CONFIGS) == 0:
                # 如果没有配置了，显示新增配置提示
                self.model_selector.setCurrentText('+ 新增配置')
        else:
            # 取消，恢复选择器状态
            self.update_remote_config_selector()
    
    def update_remote_models(self):
        """更新远程模型信息（在选择远程配置后调用）"""
        # 如果当前配置有模型列表，使用第一个模型
        if Config.REMOTE_API_MODELS and len(Config.REMOTE_API_MODELS) > 0:
            selected_model = Config.REMOTE_API_MODELS[0]
            ConfigManager.select_model(selected_model)
            print(f"使用远程配置中的模型: {selected_model}")
        else:
            print("远程配置中没有可用的模型")
            
        # 更新各个标签页
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab, 'model_selector'):
                # 标签页中不再需要模型选择器，因为我们只使用配置中的单个模型
                if hasattr(tab, 'update_model'):
                    # 如果标签页有update_model方法，通知其模型已更新
                    tab.update_model(Config.SELECTED_MODEL)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 不再需要刷新模型菜单，因为已经添加了独立按钮
        # 如果需要添加其他菜单项可以在此处添加
        
        # 注意：具体的模型加载/初始化已移至__init__方法结束部分，这里不再需要调用
        # 这样避免重复初始化

    def refresh_local_models(self):
        """手动刷新本地模型列表"""
        if Config.MODEL_SOURCE != 'Ollama本地模型':
            QMessageBox.information(self, "刷新模型", "只有在本地模型模式下才能刷新模型列表。", QMessageBox.Ok)
            return
            
        # 清空缓存
        self.local_models_cache = []
        
        # 显示加载状态
        self.model_selector.clear()
        self.model_selector.addItem('加载本地模型中...')
        self.model_selector.setEnabled(False)
        
        # 重新加载模型
        self.init_model_loader()
        
        # 通知用户
        print("手动刷新本地模型列表")

    def init_model_loader(self):
        self.loader_thread = QThread()
        self.model_loader = ModelLoader(self.api_handler)
        self.model_loader.moveToThread(self.loader_thread)
        self.loader_thread.started.connect(self.model_loader.run)
        self.model_loader.finished.connect(self.on_models_loaded)
        self.loader_thread.start()

    def on_models_loaded(self, models):
        self.model_selector.clear()
        self.model_selector.setEnabled(True)  # 重新启用选择器
        
        if models:
            # 更新缓存
            self.local_models_cache = models.copy()
            print(f"成功加载并缓存{len(models)}个本地模型")
            
            self.model_selector.addItems(models)
            
            # 如果有默认模型，选择它
            if Config.SELECTED_MODEL in models:
                self.model_selector.setCurrentText(Config.SELECTED_MODEL)
            elif models:
                # 否则选择第一个模型并更新配置
                first_model = models[0]
                self.model_selector.setCurrentText(first_model)
                ConfigManager.select_model(first_model)
        else:
            # 加载失败时显示错误信息并提供解决方案
            self.model_selector.addItem('模型加载失败')
            self.offer_ollama_solutions()
            
        self.loader_thread.quit()
        self.loader_thread.wait()
    
    def offer_ollama_solutions(self):
        """当Ollama模型加载失败时提供解决方案选项"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Ollama模型加载问题")
        msg_box.setText("无法加载Ollama本地模型，请：\n\
        1. 检查是否安装Ollama\n\
        2. 检查是否启动Ollama\n\
        3. 检查是否有可用模型\n")
        msg_box.setIcon(QMessageBox.Warning)
        
        # 添加按钮
        start_service_btn = msg_box.addButton("启动Ollama服务", QMessageBox.ActionRole)
        install_model_btn = msg_box.addButton("安装模型", QMessageBox.ActionRole)
        install_ollama_btn = msg_box.addButton("安装Ollama", QMessageBox.ActionRole)
        cancel_btn = msg_box.addButton("取消", QMessageBox.RejectRole)
        
        msg_box.exec_()
        
        # 根据用户选择执行对应操作
        clicked_button = msg_box.clickedButton()
        if clicked_button == start_service_btn:
            self.start_ollama_service()
        elif clicked_button == install_model_btn:
            self.model_manager.install_ollama_model()
        elif clicked_button == install_ollama_btn:
            self.install_ollama()
    
    def start_ollama_service(self):
        """尝试启动Ollama服务"""
        try:
            Logger.info("尝试启动Ollama服务")
            
            # 创建启动服务的对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("启动Ollama服务")
            dialog.setMinimumWidth(450)
            
            layout = QVBoxLayout(dialog)
            
            # 添加说明文本
            info_label = QLabel("正在尝试启动Ollama服务...\n如果服务已安装但未运行，这将启动服务。")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # 添加状态文本
            status_label = QLabel("准备启动...")
            layout.addWidget(status_label)
            
            # 添加进度条
            progress = QProgressBar()
            progress.setRange(0, 0)  # 设置为不确定模式
            layout.addWidget(progress)
            
            # 添加按钮
            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # 显示对话框但不阻塞
            dialog.show()
            QApplication.processEvents()
            
            # 尝试启动Ollama服务
            import platform
            import subprocess
            
            system = platform.system().lower()
            
            if system == "windows":
                # Windows系统
                status_label.setText("在Windows上尝试启动Ollama服务...")
                QApplication.processEvents()
                
                # 首先检查是否有模型
                try:
                    # 尝试访问Ollama API获取模型列表
                    import requests
                    response = requests.get("http://localhost:11434/api/tags", timeout=3)
                    if response.status_code == 200:
                        # 服务已经在运行，检查是否有模型
                        models = response.json().get('models', [])
                        if models:
                            # 有模型，服务正常运行
                            status_label.setText("Ollama服务已运行，检测到可用模型。")
                            status_label.setStyleSheet("color: green;")
                            
                            # 添加刷新按钮
                            refresh_btn = button_box.addButton("刷新模型列表", QDialogButtonBox.ActionRole)
                            refresh_btn.clicked.connect(lambda: self.refresh_after_service_start(dialog))
                            return
                        else:
                            # 服务运行但没有模型
                            status_label.setText("Ollama服务已运行，但未检测到模型。")
                            status_label.setStyleSheet("color: #FF8C00;")  # 橙色
                            
                            # 添加安装模型按钮
                            install_btn = button_box.addButton("安装模型", QDialogButtonBox.ActionRole)
                            install_btn.clicked.connect(lambda: self.install_model_from_dialog(dialog))
                    else:
                        # 服务未运行或返回错误
                        status_label.setText("Ollama服务未运行，尝试启动...")
                        QApplication.processEvents()
                except requests.exceptions.ConnectionError:
                    # 服务未运行
                    status_label.setText("Ollama服务未运行，尝试启动...")
                    QApplication.processEvents()
                
                # 尝试静默启动服务
                try:
                    # 使用subprocess.Popen静默启动服务
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    # 使用shell=True但隐藏窗口
                    process = subprocess.Popen(
                        ["ollama", "serve"],
                        startupinfo=startupinfo,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    status_label.setText("Ollama服务启动命令已执行，正在检查服务是否运行...")
                    QApplication.processEvents()
                    
                    # 等待几秒让服务有时间启动
                    import time
                    time.sleep(2)
                    
                    # 检查服务是否启动成功
                    try:
                        response = requests.get("http://localhost:11434/api/tags", timeout=3)
                        if response.status_code == 200:
                            # 服务已经启动成功
                            status_label.setText("Ollama服务已成功启动，您现在可以安装或使用模型。")
                            status_label.setStyleSheet("color: green;")
                            
                            # 添加安装模型和刷新按钮
                            install_btn = button_box.addButton("安装模型", QDialogButtonBox.ActionRole)
                            install_btn.clicked.connect(lambda: self.install_model_from_dialog(dialog))
                            
                            refresh_btn = button_box.addButton("刷新模型列表", QDialogButtonBox.ActionRole)
                            refresh_btn.clicked.connect(lambda: self.refresh_after_service_start(dialog))
                        else:
                            # 服务启动但返回错误状态码
                            status_label.setText(f"服务启动但返回错误状态码: {response.status_code}")
                            status_label.setStyleSheet("color: red;")
                            
                            # 添加手动启动指南按钮
                            manual_btn = button_box.addButton("手动启动指南", QDialogButtonBox.ActionRole)
                            manual_btn.clicked.connect(self.show_manual_windows_start_guide)
                    except requests.exceptions.ConnectionError:
                        # 服务可能未成功启动
                        status_label.setText("无法连接到Ollama服务，请检查是否安装了Ollama。")
                        status_label.setStyleSheet("color: red;")
                        
                        # 尝试检查Ollama是否已安装
                        check_result = subprocess.run(["where", "ollama"], capture_output=True, text=True, shell=True)
                        if "ollama.exe" in check_result.stdout:
                            # Ollama已安装但启动失败
                            status_label.setText("Ollama已安装但服务启动失败。请尝试手动启动Ollama或重启电脑后再试。")
                            status_label.setStyleSheet("color: #FF8C00;")  # 深橙色
                            
                            # 添加手动启动指南按钮
                            manual_btn = button_box.addButton("手动启动指南", QDialogButtonBox.ActionRole)
                            manual_btn.clicked.connect(self.show_manual_windows_start_guide)
                        else:
                            # Ollama可能未安装
                            status_label.setText("未检测到Ollama安装，请先安装Ollama。")
                            status_label.setStyleSheet("color: red;")
                            
                            # 添加安装Ollama按钮
                            install_btn = button_box.addButton("安装Ollama", QDialogButtonBox.ActionRole)
                            install_btn.clicked.connect(lambda: self.install_ollama_from_dialog(dialog))
                except Exception as e:
                    # 启动命令执行失败
                    status_label.setText(f"启动Ollama服务出错: {str(e)}")
                    status_label.setStyleSheet("color: red;")
                    Logger.error(f"启动Ollama服务出错: {str(e)}")
                    
                    # 添加手动启动指南和安装Ollama按钮
                    manual_btn = button_box.addButton("手动启动指南", QDialogButtonBox.ActionRole)
                    manual_btn.clicked.connect(self.show_manual_windows_start_guide)
                    
                    install_btn = button_box.addButton("安装Ollama", QDialogButtonBox.ActionRole)
                    install_btn.clicked.connect(lambda: self.install_ollama_from_dialog(dialog))
            
            elif system == "darwin":
                # macOS系统
                status_label.setText("在macOS上尝试启动Ollama服务...")
                QApplication.processEvents()
                
                try:
                    # 检查Ollama服务状态
                    result = subprocess.run(["pgrep", "ollama"], capture_output=True, text=True)
                    if result.returncode != 0:
                        # 服务未运行，尝试启动
                        subprocess.Popen(["open", "-a", "Ollama"])
                        status_label.setText("Ollama应用已启动，请等待服务初始化...")
                        refresh_btn = button_box.addButton("刷新模型列表", QDialogButtonBox.ActionRole)
                        refresh_btn.clicked.connect(lambda: self.refresh_after_service_start(dialog))
                    else:
                        status_label.setText("Ollama服务已在运行。您可以安装或使用模型。")
                        status_label.setStyleSheet("color: green;")
                        
                        # 添加安装模型和刷新按钮
                        install_btn = button_box.addButton("安装模型", QDialogButtonBox.ActionRole)
                        install_btn.clicked.connect(lambda: self.install_model_from_dialog(dialog))
                        
                        refresh_btn = button_box.addButton("刷新模型列表", QDialogButtonBox.ActionRole)
                        refresh_btn.clicked.connect(lambda: self.refresh_after_service_start(dialog))
                except Exception as e:
                    status_label.setText(f"启动服务时出错: {str(e)}")
                    Logger.error(f"启动Ollama服务出错: {str(e)}")
            
            elif system == "linux":
                # Linux系统
                status_label.setText("在Linux上尝试启动Ollama服务...")
                QApplication.processEvents()
                
                try:
                    # 尝试启动服务
                    result = subprocess.run(["systemctl", "is-active", "ollama"], capture_output=True, text=True)
                    if "inactive" in result.stdout:
                        # 服务未激活，尝试启动
                        subprocess.run(["systemctl", "start", "ollama"])
                        status_label.setText("已尝试启动Ollama服务，请等待服务初始化...")
                        
                        refresh_btn = button_box.addButton("刷新模型列表", QDialogButtonBox.ActionRole)
                        refresh_btn.clicked.connect(lambda: self.refresh_after_service_start(dialog))
                    else:
                        status_label.setText("Ollama服务已在运行。您可以安装或使用模型。")
                        status_label.setStyleSheet("color: green;")
                        
                        # 添加安装模型和刷新按钮
                        install_btn = button_box.addButton("安装模型", QDialogButtonBox.ActionRole)
                        install_btn.clicked.connect(lambda: self.install_model_from_dialog(dialog))
                        
                        refresh_btn = button_box.addButton("刷新模型列表", QDialogButtonBox.ActionRole)
                        refresh_btn.clicked.connect(lambda: self.refresh_after_service_start(dialog))
                except Exception as e:
                    status_label.setText(f"启动服务时出错: {str(e)}")
                    Logger.error(f"启动Ollama服务出错: {str(e)}")
            
            else:
                status_label.setText(f"不支持的操作系统: {system}")
                
            # 停止进度条
            progress.setRange(0, 100)
            progress.setValue(100)
            
        except Exception as e:
            Logger.error(f"启动Ollama服务过程中出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"启动Ollama服务过程中出错: {str(e)}")
    
    def install_model_from_dialog(self, dialog):
        """从对话框中调用安装模型的方法"""
        dialog.accept()  # 关闭对话框
        self.model_manager.install_ollama_model
        
    def show_manual_windows_start_guide(self):
        """显示Windows手动启动Ollama的指南"""
        guide_dialog = QDialog(self)
        guide_dialog.setWindowTitle("Windows手动启动Ollama指南")
        guide_dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(guide_dialog)
        
        # 添加说明文本
        guide_text = """
        <h3>在Windows上手动启动Ollama的方法：</h3>
        <ol>
          <li>使用开始菜单搜索"Ollama"并点击打开</li>
          <li>如果找不到Ollama图标，请在命令提示符或PowerShell中运行:</li>
        </ol>
        <pre>ollama serve</pre>
        <p>或者:</p>
        <ol>
          <li>按下Win+R打开运行对话框</li>
          <li>输入"cmd"打开命令提示符</li>
          <li>在命令提示符中输入: <code>ollama serve</code></li>
        </ol>
        <p>注意：保持命令窗口运行，不要关闭它，否则Ollama服务将停止。</p>
        """
        
        guide_label = QLabel(guide_text)
        guide_label.setTextFormat(Qt.RichText)
        guide_label.setWordWrap(True)
        layout.addWidget(guide_label)
        
        # 添加关闭按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(guide_dialog.reject)
        layout.addWidget(button_box)
        
        guide_dialog.exec_()
    
    def refresh_after_service_start(self, dialog):
        """服务启动后刷新模型列表"""
        dialog.accept()  # 关闭对话框
        # 延迟一秒再刷新，给服务一些启动时间
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, self.refresh_local_models)
    
    def install_ollama_from_dialog(self, dialog):
        """从对话框中调用安装Ollama的方法"""
        dialog.accept()  # 关闭对话框
        self.install_ollama()
    
    def install_ollama(self):
        """提供Ollama安装指导"""
        dialog = QDialog(self)
        dialog.setWindowTitle("安装Ollama")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # 添加说明文本
        info_label = QLabel("Ollama需要单独安装。请根据您的操作系统按照以下步骤安装：")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 根据操作系统提供不同的安装指南
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            install_text = """
            <h3>Windows安装步骤：</h3>
            <ol>
              <li>访问Ollama官方网站: <a href="https://ollama.com/download">https://ollama.com/download</a></li>
              <li>下载Windows安装程序</li>
              <li>运行下载的安装程序</li>
              <li>完成安装后启动Ollama</li>
            </ol>
            <p>或者点击下面的按钮直接打开下载页面：</p>
            """
            download_url = "https://ollama.com/download"
        elif system == "darwin":
            install_text = """
            <h3>macOS安装步骤：</h3>
            <ol>
              <li>访问Ollama官方网站: <a href="https://ollama.com/download">https://ollama.com/download</a></li>
              <li>下载macOS安装程序</li>
              <li>打开下载的.dmg文件</li>
              <li>将Ollama拖到Applications文件夹</li>
              <li>从Applications文件夹启动Ollama</li>
            </ol>
            <p>或者点击下面的按钮直接打开下载页面：</p>
            """
            download_url = "https://ollama.com/download"
        elif system == "linux":
            install_text = """
            <h3>Linux安装步骤：</h3>
            <p>使用以下命令安装：</p>
            <pre>curl -fsSL https://ollama.com/install.sh | sh</pre>
            <p>或者访问Ollama GitHub页面获取更多安装选项：<a href="https://github.com/ollama/ollama">https://github.com/ollama/ollama</a></p>
            """
            download_url = "https://github.com/ollama/ollama"
        else:
            install_text = f"<p>不支持的操作系统: {system}。请访问Ollama官方网站获取安装指南：<a href='https://ollama.com/download'>https://ollama.com/download</a></p>"
            download_url = "https://ollama.com/download"
        
        # 显示安装指南
        guide_label = QLabel(install_text)
        guide_label.setTextFormat(Qt.RichText)
        guide_label.setOpenExternalLinks(True)
        guide_label.setWordWrap(True)
        layout.addWidget(guide_label)
        
        # 添加直接下载按钮
        download_btn = QPushButton("打开Ollama下载页面")
        download_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(download_url)))
        layout.addWidget(download_btn)
        
        # 添加关闭按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()
    
    # 重构到model_manager.py
    
    def init_ui_components(self):
        '''初始化各个功能界面组件'''
        from ui.tabs import FileProcessingTab, ChatTab, SupportTab
        
        self.tabs.addTab(FileProcessingTab(self.api_handler), '文件处理')
        self.tabs.addTab(ChatTab(self.api_handler), '对话')
        self.tabs.addTab(SupportTab(self.api_handler), '帮助与支持')    
        
        # 移除模型管理标签页
        # model_manager = ModelManagerTab(self.api_handler)
        # model_manager.set_main_window(self)  # 设置主窗口引用
        # self.tabs.addTab(model_manager, '模型管理')

    def generate_output_path(self, original_path):
        '''生成带时间戳的输出文件路径'''
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base, ext = os.path.splitext(original_path)
        return f'{base}_{timestamp}{ext}'

# 远程api
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
#

    def closeEvent(self, event):
        """程序关闭时的处理"""
        try:
            # 如果当前使用的是Ollama本地模型，关闭服务
            if Config.MODEL_SOURCE == 'Ollama本地模型' and hasattr(self, 'api_handler'):
                # 不再卸载模型，直接关闭服务
                print("[程序关闭] 正在关闭Ollama服务...")
                import platform
                system = platform.system().lower()
                
                if system == "windows":
                    # Windows系统使用taskkill命令关闭ollama进程
                    import subprocess
                    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], 
                                 capture_output=True, 
                                 text=True)
                elif system == "darwin":
                    # macOS系统使用pkill命令关闭ollama进程
                    subprocess.run(["pkill", "ollama"], 
                                 capture_output=True, 
                                 text=True)
                elif system == "linux":
                    # Linux系统使用systemctl停止ollama服务
                    subprocess.run(["systemctl", "stop", "ollama"], 
                                 capture_output=True, 
                                 text=True)
                
                print("[程序关闭] Ollama服务已关闭")
        except Exception as e:
            print(f"[程序关闭] 关闭服务时出错: {str(e)}")
        
        # 调用父类的closeEvent
        super().closeEvent(event)
