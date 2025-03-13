from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLineEdit, QComboBox, QLabel, QSplitter, QHBoxLayout, QListWidget, QListWidgetItem, QProgressBar
from PyQt5.QtCore import Qt
import os
import time
import csv
import json
from file_drop_zone import FileDropZone
from PyQt5.QtCore import pyqtSignal, QObject, QThreadPool, QRunnable
from config import Config

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
        # self.layout.addWidget(self.model_selector)  # 删除这一行

    def update_model_list(self, models):
        self.model_selector.clear()
        self.model_selector.addItems([model['name'] for model in models])

class ModelManagerTab(BaseTab):
    def __init__(self, api_handler):
        super().__init__(api_handler)
        self.main_window = None  # 引用主窗口
        self.setup_model_controls()
        self.loading_label = QLabel('加载中...')
        self.layout.addWidget(self.loading_label)
        
        # 检查当前模型来源
        from config import Config
        if Config.MODEL_SOURCE == 'Ollama本地模型':
            self.load_models_async()
        else:
            # 远程API模式下显示提示信息
            self.loading_label.hide()
            
            # 创建更详细的提示信息
            from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
            from PyQt5.QtGui import QIcon, QPixmap, QFont
            
            info_container = QWidget()
            info_layout = QVBoxLayout(info_container)
            
            # 标题
            title_label = QLabel('远程API模式')
            title_label.setFont(QFont('Arial', 12, QFont.Bold))
            title_label.setStyleSheet("color: #333;")
            info_layout.addWidget(title_label)
            
            # 说明文本
            info_text = """
            <p>您当前使用的是<b>远程API模式</b>，本功能仅适用于Ollama本地模型。</p>
            <p>当前已配置：<b>{config_name}</b> ({api_url})</p>
            <p>可用模型：{models}</p>
            <p>如需管理本地模型，请在顶部选择"Ollama本地模型"模式。</p>
            <p>如需配置远程API，请点击顶部的"配置"按钮。</p>
            """.format(
                config_name=Config.REMOTE_API_CONFIGS[Config.CURRENT_REMOTE_CONFIG_INDEX].get('name', '未命名') if Config.REMOTE_API_CONFIGS and Config.CURRENT_REMOTE_CONFIG_INDEX < len(Config.REMOTE_API_CONFIGS) else '未知',
                api_url=Config.REMOTE_API_URL,
                models=', '.join(Config.REMOTE_API_MODELS) if Config.REMOTE_API_MODELS else '无'
            )
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            info_label.setStyleSheet("""
                QLabel {
                    color: #333;
                    padding: 20px;
                    background-color: #f8f8f8;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                }
            """)
            info_layout.addWidget(info_label)
            
            # 如果是DeepSeek API，添加特别说明
            if "deepseek.com" in Config.REMOTE_API_URL.lower():
                deepseek_info = QLabel("""
                <p><b>DeepSeek API 使用说明：</b></p>
                <p>1. 确保您已在配置中填入有效的API密钥</p>
                <p>2. 模型名称应设为 "deepseek-reasoner" 或其他有效的DeepSeek模型</p>
                <p>3. 如遇到 400 错误，请检查API密钥是否正确</p>
                <p>4. <a href="https://platform.deepseek.com/">点击这里</a>访问DeepSeek官方平台获取API密钥</p>
                """)
                deepseek_info.setOpenExternalLinks(True)
                deepseek_info.setWordWrap(True)
                deepseek_info.setStyleSheet("""
                    QLabel {
                        color: #333;
                        padding: 20px;
                        background-color: #e6f7ff;
                        border-radius: 5px;
                        border: 1px solid #91d5ff;
                        margin-top: 10px;
                    }
                    a {
                        color: #1890ff;
                        text-decoration: none;
                    }
                    a:hover {
                        text-decoration: underline;
                    }
                """)
                info_layout.addWidget(deepseek_info)
            
            self.layout.addWidget(info_container)
            
            # 禁用刷新按钮，如果存在的话
            if hasattr(self, 'refresh_btn'):
                self.refresh_btn.setEnabled(False)

    def set_main_window(self, main_window):
        """设置对主窗口的引用"""
        self.main_window = main_window

    def load_models_async(self):
        from PyQt5.QtCore import QThreadPool, QRunnable
        
        # 如果主窗口存在且有本地模型缓存，则使用缓存
        if self.main_window and self.main_window.local_models_cache:
            print("ModelManagerTab: 使用主窗口缓存的本地模型列表")
            self.handle_cached_models(self.main_window.local_models_cache)
            return
            
        # 否则正常加载
        print("ModelManagerTab: 从API加载本地模型列表")
        
        class ModelLoader(QRunnable):
            class Signals(QObject):
                result = pyqtSignal(dict)

            def __init__(self, callback):
                super().__init__()
                self.callback = callback
                self.signals = self.Signals()

            def run(self):
                try:
                    response = self.callback()
                    self.signals.result.emit(response)
                except Exception as e:
                    self.signals.result.emit({})

        self.thread_pool = QThreadPool()
        worker = ModelLoader(self.api_handler.list_local_models)
        worker.signals.result.connect(self.handle_model_response)
        self.thread_pool.start(worker)

    def handle_cached_models(self, models):
        """处理从缓存中获取的模型列表"""
        self.loading_label.hide()
        if models:
            # 转换为字典列表格式以匹配API响应格式
            model_list = [{'name': model} for model in models]
            self.update_model_list(model_list)
        else:
            self.layout.addWidget(QLabel('无本地模型'))

    def handle_model_response(self, response):
        self.loading_label.hide()
        if 'models' in response and response['models']:
            # 如果有主窗口引用，更新其缓存
            if self.main_window:
                self.main_window.local_models_cache = [m['name'] for m in response['models']]
                print(f"ModelManagerTab: 更新主窗口缓存，共{len(self.main_window.local_models_cache)}个模型")
                
            self.update_model_list(response['models'])
        else:
            self.layout.addWidget(QLabel('无本地模型'))

    def setup_model_controls(self):
        self.refresh_btn = QPushButton('刷新模型列表')
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #EF6C00;
                padding: 9px 16px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.layout.addWidget(self.refresh_btn)
        
        self.refresh_btn.clicked.connect(self.load_models)

    def load_models(self):
        # 如果有主窗口引用，清空其缓存
        if self.main_window:
            self.main_window.local_models_cache = []
            print("ModelManagerTab: 清空主窗口缓存，强制重新加载模型")
            
        self.loading_label.show()
        self.load_models_async()

class FileProcessingTab(BaseTab):
    def __init__(self, api_handler):
        super().__init__(api_handler)
        self.setup_ui_components()
        self.thread_pool = QThreadPool()
        self.current_worker = None  # 添加对当前工作线程的引用
        self.output_files = []  # 存储生成的输出文件列表
        
        # 由于生成学习卡片是默认选择的功能，提前准备好输出目录
        output_dir = "output_cards"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = os.path.abspath(output_dir)
        
    def setup_ui_components(self):
        # 创建分割器以便更好地组织UI
        splitter = QSplitter(Qt.Vertical)
        
        # 添加文件拖放区域
        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self.handle_files_update)
        splitter.addWidget(self.drop_zone)
        
        # 添加处理方式选择
        process_control = QWidget()
        
        # 创建垂直布局来组织多行控件
        process_vertical_layout = QVBoxLayout(process_control)
        process_vertical_layout.setContentsMargins(0, 0, 0, 0)
        
        # 系统提示词选择行
        from config import Config
        system_prompt_layout = QHBoxLayout()
        self.system_prompt_selector = QComboBox()
        self.system_prompt_selector.addItem('无')  # 默认选项
        
        # 打开系统提示词文件夹按钮
        open_prompts_folder_btn = QPushButton('打开文件夹')
        open_prompts_folder_btn.setToolTip('打开系统提示词文件夹')
        open_prompts_folder_btn.clicked.connect(self.open_system_prompts_folder)
        open_prompts_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #78909C;
            }
            QPushButton:pressed {
                background-color: #455A64;
            }
        """)
        
        # 刷新系统提示词按钮
        refresh_prompts_btn = QPushButton('刷新')
        refresh_prompts_btn.setToolTip('刷新系统提示词列表')
        refresh_prompts_btn.clicked.connect(self.load_system_prompts)
        refresh_prompts_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #26C6DA;
            }
            QPushButton:pressed {
                background-color: #0097A7;
            }
        """)
        
        # 添加到布局
        system_prompt_layout.addWidget(QLabel('系统提示词：'))
        system_prompt_layout.addWidget(self.system_prompt_selector)
        system_prompt_layout.addWidget(refresh_prompts_btn)
        system_prompt_layout.addWidget(open_prompts_folder_btn)
        system_prompt_layout.addStretch()
        
        # 直接添加布局到垂直布局，与处理选择器保持一致
        process_vertical_layout.addLayout(system_prompt_layout)
        
        # 加载系统提示词
        self.load_system_prompts()
        
        # 第一行：处理方式选择
        process_selector_layout = QHBoxLayout()
        self.process_selector = QComboBox()
        self.process_selector.addItems(['生成学习卡片', '显示文件内容', '生成文件摘要', '提取关键信息'])
        process_selector_layout.addWidget(QLabel('处理方式：'))
        process_selector_layout.addWidget(self.process_selector)
        process_selector_layout.addStretch()
        
        # 添加第一行到垂直布局
        process_vertical_layout.addLayout(process_selector_layout)
        
        # 当处理方式改变时更新UI
        self.process_selector.currentTextChanged.connect(self.on_process_type_changed)
        
        # 第二行：按钮和状态
        button_layout = QHBoxLayout()
        
        # 运行按钮
        self.run_btn = QPushButton('运行')
        self.run_btn.clicked.connect(self.start_processing)
        
        # 停止按钮
        self.stop_btn = QPushButton('停止')
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)  # 初始禁用
        
        # 添加状态标签
        self.status_label = QLabel('准备就绪')
        
        # 按钮样式 - 增强反馈效果
        self.run_btn.setStyleSheet('''
            QPushButton {
                background: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #66BB6A;
            }
            QPushButton:pressed {
                background: #2E7D32;
                padding-top: 10px;
                padding-bottom: 6px;
            }
            QPushButton:disabled {
                background: #81C784;
            }
        ''')
        
        # 停止按钮样式
        self.stop_btn.setStyleSheet('''
            QPushButton {
                background: #F44336;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #EF5350;
            }
            QPushButton:pressed {
                background: #C62828;
                padding-top: 10px;
                padding-bottom: 6px;
            }
            QPushButton:disabled {
                background: #FFCDD2;
                color: #D32F2F;
            }
        ''')
        
        # 状态提示样式
        self.status_label.setStyleSheet('''
            QLabel {
                color: #666;
                font-style: italic;
                border-left: 3px solid #2196F3;
                padding: 4px 8px;
            }
        ''')
        
        # 添加按钮到按钮布局
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet('''
            QProgressBar {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                text-align: center;
                background: #F5F5F5;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        ''')
        self.progress_bar.setVisible(False)  # 初始隐藏
        
        # 将按钮布局添加到处理控制布局
        process_vertical_layout.addLayout(button_layout)
        
        # 添加进度条布局
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        process_vertical_layout.addLayout(progress_layout)
        
        splitter.addWidget(process_control)
        
        # 文件信息区域 - 仅用于内部跟踪，不显示在UI中
        self.file_info = QTextEdit()
        self.file_info.setReadOnly(True)
        self.file_info.hide()  # 隐藏调试信息区域
        
        # 输出文件列表区域（生成卡片后显示）
        self.output_files_widget = QWidget()
        output_files_layout = QVBoxLayout(self.output_files_widget)
        
        # 添加标题
        output_title_layout = QHBoxLayout()
        output_title_layout.addWidget(QLabel("生成的卡片文件:"))
        output_title_layout.addStretch()
        
        # 添加打开文件夹按钮和查看文件按钮
        self.open_folder_btn = QPushButton("打开文件夹")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setStyleSheet('''
            QPushButton {
                background: #2196F3;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #42A5F5;
            }
            QPushButton:pressed {
                background: #1976D2;
            }
            QPushButton:disabled {
                background: #BBDEFB;
                color: #64B5F6;
            }
        ''')
        
        output_title_layout.addWidget(self.open_folder_btn)
        output_files_layout.addLayout(output_title_layout)
        
        # 文件列表
        self.output_files_list = QListWidget()
        self.output_files_list.setStyleSheet('''
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: transparent;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
                color: #1976D2;
            }
        ''')
        output_files_layout.addWidget(self.output_files_list)
        
        # 初始隐藏输出文件区域
        self.output_files_widget.setVisible(False)
        
        # 输出区域
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("处理结果将显示在这里")
        self.output_area.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                color: #333;
                font-family: Consolas, Monaco, monospace;
            }
        """)
        
        # 创建输出区域布局
        output_splitter = QSplitter(Qt.Vertical)
        output_splitter.addWidget(self.output_area)
        output_splitter.addWidget(self.output_files_widget)
        
        # 设置初始大小比例
        output_splitter.setSizes([700, 300])
        
        # 不添加file_info到分割器，添加输出区域和文件列表
        splitter.addWidget(output_splitter)
        
        # 添加到主布局
        self.layout.addWidget(splitter)
        
        # 初始化处理状态标志
        self.is_processing = False
        self.current_progress = 0
        self.total_files = 0
        
        # 添加初始提示信息
        self.output_area.setText("拖放文件到上方区域，点击'运行'按钮开始生成学习卡片。\n\n"
                                "学习卡片将保存在程序目录下的output_cards文件夹中。")
    
    def on_process_type_changed(self, process_type):
        """当处理方式改变时更新UI"""
        # 现在不需要对UI进行任何改变
        pass
    
    def handle_files_update(self, files):
        """处理文件更新事件"""
        self.update_file_info()
        
        # 清空输出文件列表
        self.output_files = []
        self.output_files_list.clear()
        self.output_files_widget.setVisible(False)
    
    def update_file_info(self):
        """更新文件信息显示"""
        files = self.drop_zone.get_files()
        if not files:
            self.file_info.setPlainText("未选择文件")
            return
            
        info_text = f"已选择{len(files)}个文件：\n"
        for file in files:
            info_text += f"• {os.path.basename(file)} ({file})\n"
        self.file_info.setPlainText(info_text)
    
    def start_processing(self):
        """开始处理文件"""
        files = self.drop_zone.get_files()
        if not files:
            self.output_area.setPlainText("错误：未选择任何文件")
            return
        
        # 如果已经在处理中，则返回
        if self.is_processing:
            return
            
        # 更新处理状态
        self.is_processing = True
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText('处理中...')
        
        # 获取处理方式
        process_type = self.process_selector.currentText()
            
        try:
            # 清空输出区域
            self.output_area.clear()
            
            # 清空输出文件列表
            self.output_files = []
            self.output_files_list.clear()
            self.output_files_widget.setVisible(False)
            
            # 获取当前选择的模型名称和处理方式
            from config import Config
            model_name = Config.SELECTED_MODEL
            
            # 显示处理信息
            self.output_area.append(f"使用模型: {model_name}")
            self.output_area.append(f"处理方式: {process_type}\n")
            
            # 根据不同的处理方式执行不同的操作
            if process_type == '生成学习卡片':
                # 初始化进度条
                self.progress_bar.setValue(0)
                self.progress_bar.setVisible(True)
                
                # 创建后台任务
                self.create_learning_cards_task(files)
            elif process_type == '生成文件摘要':
                # 测试功能：打印即将执行的参数
                self.output_area.append("\n=== 测试功能：参数信息 ===")
                self.output_area.append(f"当前模型: {model_name}")
                self.output_area.append(f"API处理器类型: {type(self.api_handler).__name__}")
                
                # 获取系统提示词
                system_prompt = self.get_selected_system_prompt()
                if system_prompt:
                    self.output_area.append(f"\n系统提示词: {system_prompt}")
                else:
                    self.output_area.append("\n系统提示词: 无")
                
                # 获取API URL和远程API模型信息
                if hasattr(self.api_handler, 'api_url'):
                    self.output_area.append(f"\nAPI URL: {self.api_handler.api_url}")
                    # 显示远程API模型信息
                    if hasattr(Config, 'REMOTE_API_MODELS') and Config.REMOTE_API_MODELS:
                        self.output_area.append("\n可用的远程API模型:")
                        for i, model in enumerate(Config.REMOTE_API_MODELS, 1):
                            self.output_area.append(f"{i}. {model}")
                        # 显示当前选择的远程模型
                        if model_name in Config.REMOTE_API_MODELS:
                            self.output_area.append(f"\n当前选择的远程模型: {model_name}")
                        else:
                            self.output_area.append(f"\n警告: 当前选择的模型 {model_name} 不在远程API模型列表中")
                
                # 显示选中的文件信息
                self.output_area.append("\n选中的文件:")
                for i, file in enumerate(files, 1):
                    self.output_area.append(f"{i}. {os.path.basename(file)}")
                
                # 完成处理
                self.is_processing = False
                self.run_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.status_label.setText('准备就绪')
            else:
                # 原有的文件内容显示逻辑
                for file in files:
                    # 检查是否已请求停止处理
                    if not self.is_processing:
                        self.output_area.append("\n--- 处理已被用户中断 ---")
                        break
                        
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        self.output_area.append(f"\n--- {os.path.basename(file)} ---\n")
                        self.output_area.append(content)
                        self.output_area.append("\n")
                    except Exception as e:
                        self.output_area.append(f"读取文件 {os.path.basename(file)} 时出错: {str(e)}\n")
                        
                # 完成处理
                self.is_processing = False
                self.run_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.status_label.setText('准备就绪')
            
        except Exception as e:
            self.output_area.append(f"处理过程中出错: {str(e)}")
            self.is_processing = False
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText('准备就绪')
            self.progress_bar.setVisible(False)
    
    def open_output_folder(self):
        """打开输出文件夹"""
        if self.output_dir and os.path.exists(self.output_dir):
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_dir))
        else:
            self.output_area.append("输出目录不存在")
    
    def open_output_file(self, file_path):
        """打开输出文件"""
        if os.path.exists(file_path):
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            self.output_area.append(f"文件不存在: {file_path}")
            
    def stop_processing(self):
        """停止当前处理"""
        if self.is_processing:
            self.is_processing = False
            self.status_label.setText('正在停止...')
            self.output_area.append("\n正在停止处理...\n")
            
            # 如果有正在运行的worker，也将其is_processing设为False
            if self.current_worker:
                self.current_worker.is_processing = False
                
            # 立即恢复UI状态，不等待worker线程结束
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText('已停止')
            
            # 添加文件打开提示
            if self.output_files:
                self.output_area.append(f"已生成 {len(self.output_files)} 个文件，可以直接双击打开")

    def update_progress(self, current, total, message=''):
        """更新进度信息"""
        self.current_progress = current
        self.total_files = total
        progress_percentage = int((current / total) * 100)
        
        # 更新进度条
        self.progress_bar.setValue(progress_percentage)
        
        # 更新状态标签
        status_text = f'处理中... {progress_percentage}% ({current}/{total})'
        if message:
            status_text += f' - {message}'
        self.status_label.setText(status_text)
        
        # 添加日志信息
        if message:
            self.output_area.append(f"处理进度: {current}/{total} ({progress_percentage}%) - {message}")
        else:
            self.output_area.append(f"处理进度: {current}/{total} ({progress_percentage}%)")

    def add_output_file(self, file_path, description):
        """添加输出文件到列表"""
        if file_path not in self.output_files:
            self.output_files.append(file_path)
            
            # 创建可点击的列表项
            item = QListWidgetItem(f"{os.path.basename(file_path)} - {description}")
            item.setData(Qt.UserRole, file_path)  # 存储完整路径
            self.output_files_list.addItem(item)
            
            # 显示文件列表区域
            self.output_files_widget.setVisible(True)
            
            # 确保双击功能已连接 - 先断开之前的连接以防多次连接
            try:
                self.output_files_list.itemDoubleClicked.disconnect()
            except:
                pass  # 如果之前没有连接则忽略
                
            # 重新连接双击事件
            self.output_files_list.itemDoubleClicked.connect(
                lambda item: self.open_output_file(item.data(Qt.UserRole))
            )
            
    def create_learning_cards_task(self, files):
        """创建后台任务生成学习卡片"""
        # 创建一个带信号的Worker类
        class CardGeneratorWorker(QRunnable):
            class Signals(QObject):
                progress = pyqtSignal(int, int, str)
                log = pyqtSignal(str)
                finished = pyqtSignal(bool, str)
                file_processed = pyqtSignal(str, str)  # 文件路径, 描述
                
            def __init__(self, parent, files, output_dir):
                super().__init__()
                self.signals = self.Signals()
                self.parent = parent
                self.files = files
                self.output_dir = output_dir
                self.is_processing = True
                self.api_handler = parent.api_handler
                self.model_name = Config.SELECTED_MODEL
                self.processed_sections = set()  # 用于跟踪已处理的文件片段
                
            def log_message(self, message):
                self.signals.log.emit(message)
                
            def update_progress(self, current, total, message=''):
                self.signals.progress.emit(current, total, message)
                
            def check_if_should_stop(self):
                """检查是否应该停止处理"""
                return not self.parent.is_processing or not self.is_processing
            
            def get_output_filename(self, input_file):
                """生成输出文件名: 输入文件名-模型名-功能名.csv"""
                base_name = os.path.basename(input_file)
                file_name, _ = os.path.splitext(base_name)
                
                # 替换模型名称中的非法字符（特别是冒号）
                safe_model_name = self.model_name.replace(':', '-').replace('/', '-').replace('\\', '-').replace('*', '-').replace('?', '-').replace('"', '-').replace('<', '-').replace('>', '-').replace('|', '-')
                
                output_name = f"{file_name}-{safe_model_name}-学习卡片.csv"
                self.log_message(f"生成安全的输出文件名: {output_name}")
                return os.path.join(self.output_dir, output_name)
            
            def process_file(self, file_path, file_index, total_files):
                """处理单个文件"""
                try:
                    # 检查是否应该停止处理
                    if self.check_if_should_stop():
                        return False
                    
                    self.log_message(f"\n--- 开始处理文件 {os.path.basename(file_path)} ---")
                    self.log_message(f"文件路径: {file_path}")
                    self.log_message(f"处理进度: {file_index}/{total_files}")
                    
                    # 更新进度
                    self.update_progress(file_index, total_files, f"处理文件: {os.path.basename(file_path)}")
                    
                    # 为当前文件创建输出文件
                    output_file = self.get_output_filename(file_path)
                    self.log_message(f"输出文件: {output_file}")
                    
                    # 创建临时目录存放切割文件
                    import tempfile
                    temp_dir = tempfile.mkdtemp(prefix=f"file_{file_index}_")
                    self.log_message(f"创建临时目录: {temp_dir}")
                    
                    try:
                        # 切割文件
                        self.log_message(f"开始切割文件: {os.path.basename(file_path)}")
                        section_count = self.parent.split_md_by_title(file_path, temp_dir)
                        
                        if section_count == 0:
                            self.log_message(f"文件 {os.path.basename(file_path)} 没有可处理的内容")
                            return False
                            
                        self.log_message(f"文件切割完成，共 {section_count} 个片段")
                        
                        # 列出所有切割后的片段文件
                        section_files = sorted(os.listdir(temp_dir))
                        self.log_message(f"切割后的片段文件列表:")
                        for idx, sec_file in enumerate(section_files):
                            sec_path = os.path.join(temp_dir, sec_file)
                            sec_size = os.path.getsize(sec_path)
                            self.log_message(f"  {idx+1}. {sec_file} ({sec_size} 字节)")
                        
                        # 创建输出CSV文件
                        with open(output_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['问题', '答案'])  # 写入表头
                        self.log_message(f"创建CSV输出文件: {output_file}")
                        
                        # 处理每个片段
                        processed_sections = 0
                        all_cards = []
                        
                        # 遍历临时目录中的所有切割文件
                        for i, section_file in enumerate(section_files):
                            # 检查是否应该停止处理
                            if self.check_if_should_stop():
                                self.log_message(f"处理被中断，停止处理剩余片段")
                                return False
                                
                            section_path = os.path.join(temp_dir, section_file)
                            
                            # 跳过已处理的片段
                            section_id = f"{temp_dir}_{section_file}"
                            if section_id in self.processed_sections:
                                self.log_message(f"跳过已处理的片段: {section_file}")
                                continue
                                
                            processed_sections += 1
                            self.processed_sections.add(section_id)  # 标记为已处理
                            
                            self.log_message(f"\n--- 开始处理片段 {processed_sections}/{section_count}: {section_file} ---")
                            
                            # 更新进度 - 使用小片段进度
                            progress_message = f"处理文件 {file_index}/{total_files}: {os.path.basename(file_path)} - 片段 {processed_sections}/{section_count}"
                            self.update_progress(
                                (file_index - 1) * 100 + (processed_sections * 100) // section_count,
                                total_files * 100,
                                progress_message
                            )
                            
                            # 处理当前片段，传递原始文件路径用于生成输出
                            start_time = time.time()
                            cards = self.process_section(section_path, i + 1, section_count, output_file)
                            end_time = time.time()
                            self.log_message(f"片段处理耗时: {end_time - start_time:.2f}秒")
                            
                            # 添加卡片到结果集合中
                            all_cards.extend(cards)
                            
                            # 输出已经在process_section中处理了，这里不再需要写入CSV
                            
                            self.log_message(f"--- 片段 {processed_sections}/{section_count} 处理完成 ---\n")
                        
                        # 完成处理
                        card_count = len(all_cards)
                        if card_count > 0:
                            self.log_message(f"文件 {os.path.basename(file_path)} 处理完成，共生成了 {card_count} 个学习卡片")
                            self.log_message(f"输出文件: {output_file}")
                            
                            # 发送文件处理完成信号
                            description = f"{card_count}个卡片"
                            self.signals.file_processed.emit(output_file, description)
                            return True
                        else:
                            self.log_message(f"文件 {os.path.basename(file_path)} 没有生成卡片")
                            return False
                            
                    finally:
                        # 清理临时目录
                        import shutil
                        try:
                            self.log_message(f"清理临时目录: {temp_dir}")
                            shutil.rmtree(temp_dir)
                        except Exception as e:
                            self.log_message(f"清理临时文件时出错: {str(e)}")
                
                except Exception as e:
                    self.log_message(f"处理文件 {os.path.basename(file_path)} 时出错: {str(e)}")
                    import traceback
                    self.log_message(f"详细错误: {traceback.format_exc()}")
                    return False
            
            def process_section(self, section_path, section_index, total_sections, output_file):
                """处理单个文件片段"""
                try:
                    # 检查是否应该停止处理
                    if self.check_if_should_stop():
                        return []
                        
                    # 读取文件内容
                    with open(section_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content:  # 跳过空内容
                        return []
                    
                    # 计算内容行数
                    content_lines = content.split('\n')
                    line_count = len(content_lines)
                    self.log_message(f"当前片段内容行数: {line_count}")
                    
                    # 如果内容行数少于20行，持续合并多个片段直到达到20行
                    original_line_count = line_count
                    if line_count < 20 and section_index < total_sections:
                        self.log_message(f"内容行数少于20行，开始尝试合并片段")
                        
                        # 获取当前片段所在目录
                        dir_path = os.path.dirname(section_path)
                        
                        # 获取目录中的所有文件并排序
                        all_files = sorted([f for f in os.listdir(dir_path) if f.endswith('.md')])
                        
                        # 找到当前文件的索引
                        current_filename = os.path.basename(section_path)
                        if current_filename in all_files:
                            current_index = all_files.index(current_filename)
                            next_index = current_index + 1
                            
                            # 持续合并后续片段，直到行数达到或超过20行，或者没有更多片段可合并
                            merged_count = 0
                            while line_count < 20 and next_index < len(all_files):
                                next_filename = all_files[next_index]
                                next_file_path = os.path.join(dir_path, next_filename)
                                
                                # 读取下一个文件的内容
                                try:
                                    self.log_message(f"尝试合并片段 {next_index-current_index}: {next_filename}")
                                    with open(next_file_path, 'r', encoding='utf-8') as f:
                                        next_content = f.read().strip()
                                    
                                    # 将下一个片段标记为已处理
                                    next_section_id = f"{dir_path}_{next_filename}"
                                    self.processed_sections.add(next_section_id)
                                    self.log_message(f"已将片段 {next_filename} 标记为已处理")
                                    
                                    # 合并内容
                                    content = content + "\n\n" + next_content
                                    content_lines = content.split('\n')
                                    line_count = len(content_lines)
                                    merged_count += 1
                                    self.log_message(f"合并后内容行数: {line_count}")
                                    
                                    # 继续查找下一个片段
                                    next_index += 1
                                    
                                except Exception as e:
                                    self.log_message(f"读取片段 {next_filename} 时出错: {str(e)}")
                                    next_index += 1  # 尝试下一个片段
                            
                            # 合并完成后记录信息
                            if merged_count > 0:
                                self.log_message(f"合并完成: 已合并 {merged_count} 个片段，内容行数从 {original_line_count} 增加到 {line_count}")
                            else:
                                self.log_message(f"未找到可合并的片段")
                    
                    # 如果内容仍然少于20行，记录信息
                    if line_count < 20:
                        self.log_message(f"警告: 即使尝试合并多个片段，内容仍少于20行 ({line_count}行)")
                    else:
                        self.log_message(f"内容行数已达到目标: {line_count}行")
                    
                    # 生成AI提示
                    prompt = f"""
                    请将以下内容转换为学习卡片(问答对)格式。请严格按照JSON输出格式:
                    {{
                    "cards": [
                        {{
                        "q": "问题1",
                        "a": "答案1"
                        }},
                        {{
                        "q": "问题2",
                        "a": "答案2"
                        }}
                    ]
                    }}
                    
                    原始内容:
                    {content}
                    """
                    
                    # 检查是否应该停止处理
                    if self.check_if_should_stop():
                        return []
                    
                    # 调用API处理内容
                    self.log_message(f"正在通过模型生成卡片...")
                    self.log_message(f"使用模型: {self.model_name}")
                    self.log_message(f"提示内容: \n{prompt}")
                    
                    # 获取系统提示词（如果选择了）
                    system_prompt = None
                    if hasattr(self.parent, 'get_selected_system_prompt'):
                        system_prompt = self.parent.get_selected_system_prompt()
                        if system_prompt:
                            self.log_message(f"使用系统提示词: {system_prompt[:100]}..." if len(system_prompt) > 100 else f"使用系统提示词: {system_prompt}")
                    
                    # 设置一个较短的超时时间来允许中断检查
                    try:
                        # 调用API生成卡片 - 添加超时参数
                        import time
                        response = None
                        
                        # 使用分段请求方式，使得可以更频繁检查停止标志
                        for _ in range(30):  # 最多尝试30次，每次等待1秒
                            if self.check_if_should_stop():
                                return []
                                
                            try:
                                self.log_message(f"尝试API调用...")
                                
                                # 检查是否使用系统提示词（远程API模式）
                                # 修改：无论使用何种模型来源，都可以使用系统提示词
                                # if system_prompt and Config.MODEL_SOURCE == '远程API模型':
                                if system_prompt:
                                    # 创建包含系统提示词的消息列表
                                    messages = [
                                        {"role": "system", "content": system_prompt},
                                        {"role": "user", "content": prompt}
                                    ]
                                    
                                    # 使用消息格式调用API
                                    self.log_message(f"使用系统提示词进行API调用")
                                    response = self.api_handler.generate_completion(
                                        model=self.model_name,
                                        prompt=messages
                                    )
                                else:
                                    # 常规API调用
                                    response = self.api_handler.generate_completion(
                                        model=self.model_name,
                                        prompt=prompt
                                    )
                                    
                                self.log_message(f"API调用成功，获取到响应")
                                break  # 如果成功获取到响应，跳出循环
                            except Exception as e:
                                # 检查是否要求停止
                                if self.check_if_should_stop():
                                    return []
                                    
                                # 如果不是超时错误，则抛出
                                if "timeout" not in str(e).lower():
                                    self.log_message(f"非超时错误: {str(e)}")
                                    raise
                                    
                                # 如果是超时错误，等待一秒后重试
                                self.log_message(f"请求超时，等待重试...")
                                time.sleep(1)
                    except Exception as e:
                        self.log_message(f"API调用错误: {str(e)}")
                        return []
                    
                    # 检查是否应该停止处理
                    if self.check_if_should_stop():
                        return []
                    
                    # 处理响应并提取JSON
                    try:
                        # 检查返回的是否是错误信息
                        if isinstance(response, dict) and 'error' in response:
                            self.log_message(f"API错误: {response['error']}")
                            return []
                            
                        # 假设返回的是JSON字符串或结果对象
                        self.log_message(f"原始响应类型: {type(response)}")
                        self.log_message(f"原始响应内容: {str(response)}")
                        
                        # 处理DeepSeek/OpenAI格式的响应
                        if isinstance(response, dict) and 'choices' in response:
                            # 提取DeepSeek/OpenAI格式的响应内容
                            self.log_message("检测到DeepSeek/OpenAI格式的响应")
                            self.log_message(f"响应结构: {list(response.keys())}")
                            
                            if len(response['choices']) > 0:
                                # 从第一个选择中获取消息内容
                                choice = response['choices'][0]
                                self.log_message(f"choice结构: {list(choice.keys())}")
                                
                                if 'message' in choice:
                                    message = choice['message']
                                    self.log_message(f"message结构: {list(message.keys())}")
                                    response_text = message.get('content', '')
                                    self.log_message(f"从DeepSeek/OpenAI格式的响应中提取内容: {response_text[:200]}...")
                                elif 'text' in choice:
                                    response_text = choice['text']
                                    self.log_message(f"从OpenAI completion格式的响应中提取内容: {response_text[:200]}...")
                                else:
                                    response_text = str(choice)
                                    self.log_message(f"未知的选择格式，使用字符串转换: {response_text[:200]}...")
                            else:
                                self.log_message("响应中没有选择项")
                                return []
                        else:
                            # 默认响应格式处理
                            response_text = response.get('response', '') if isinstance(response, dict) else str(response)
                            self.log_message(f"使用默认格式处理响应: {response_text[:200]}...")
                        
                        self.log_message(f"提取的响应文本: {response_text}")
                        
                        # 增强版JSON提取逻辑，处理可能包含代码块的情况
                        try:
                            # 首先尝试直接解析为JSON（如果完整响应就是JSON）
                            try:
                                cards_data = json.loads(response_text)
                                self.log_message(f"成功直接解析为JSON")
                                json_str = response_text
                            except json.JSONDecodeError:
                                # 如果直接解析失败，尝试提取代码块中的JSON
                                
                                # 检查是否有 ```json 标记
                                if "```json" in response_text:
                                    self.log_message(f"检测到JSON代码块格式，尝试提取")
                                    # 查找第一个 ```json 的位置
                                    start_pos = response_text.find("```json") + 7
                                    # 找到匹配的结束 ``` 
                                    # 这里要特别处理答案中可能包含的代码块
                                    json_block = response_text[start_pos:]
                                    
                                    # 找到最外层JSON代码块的结束位置
                                    # 计算大括号的嵌套深度
                                    brace_depth = 0
                                    found_first_brace = False
                                    end_pos = -1
                                    
                                    for i, char in enumerate(json_block):
                                        if char == '{':
                                            brace_depth += 1
                                            found_first_brace = True
                                        elif char == '}':
                                            brace_depth -= 1
                                            if found_first_brace and brace_depth == 0:
                                                # 找到了匹配的最外层右大括号
                                                end_pos = i + 1  # 包含右大括号
                                                break
                                    
                                    if end_pos != -1:
                                        json_str = json_block[:end_pos].strip()
                                        self.log_message(f"成功根据大括号匹配提取JSON: 长度 {len(json_str)}")
                                    else:
                                        # 如果无法通过大括号匹配找到，使用传统方法
                                        json_str = json_block.split("```")[0].strip()
                                        self.log_message(f"通过传统方法提取JSON: 长度 {len(json_str)}")
                                
                                # 如果没有 ```json 但有其他代码块标记
                                elif "```" in response_text:
                                    self.log_message(f"检测到代码块格式，尝试提取")
                                    # 查找第一个 ``` 的位置，这个可能是任何类型的代码块
                                    parts = response_text.split("```")
                                    if len(parts) >= 3:  # 至少要有开始和结束的 ```
                                        # 提取第一个代码块内容，忽略代码块类型标记
                                        code_block = parts[1].strip()
                                        if code_block.split("\n")[0].strip() in ["json", "javascript", "js"]:
                                            # 如果代码块类型是json或js相关，去掉第一行
                                            json_str = "\n".join(code_block.split("\n")[1:]).strip()
                                        else:
                                            json_str = code_block
                                        self.log_message(f"从代码块中提取内容: 长度 {len(json_str)}")
                                    else:
                                        # 异常情况，直接使用原始响应
                                        json_str = response_text.strip()
                                        self.log_message(f"无法识别代码块，使用原始文本")
                                else:
                                    # 如果没有代码块标记，直接使用原始文本
                                    json_str = response_text.strip()
                                    self.log_message(f"使用原始文本作为JSON")
                                
                                # 尝试将提取的内容解析为JSON
                                try:
                                    cards_data = json.loads(json_str)
                                    self.log_message(f"成功解析提取后的内容为JSON")
                                except json.JSONDecodeError as je:
                                    # 如果解析失败，尝试修复常见的JSON错误
                                    self.log_message(f"JSON解析失败，尝试修复: {str(je)}")
                                    
                                    # 尝试移除内部的代码块标记，它们可能干扰JSON解析
                                    fixed_json = self._clean_nested_code_blocks(json_str)
                                    cards_data = json.loads(fixed_json)
                                    json_str = fixed_json
                                    self.log_message(f"修复后成功解析JSON")
                        
                            # 记录最终使用的JSON字符串
                            self.log_message(f"解析前的JSON字符串: {json_str[:200]}..." if len(json_str) > 200 else f"解析前的JSON字符串: {json_str}")
                        except Exception as e:
                            # 如果所有尝试都失败，使用原始文本重新抛出异常
                            self.log_message(f"所有JSON提取方法均失败: {str(e)}")
                            raise json.JSONDecodeError(f"无法从响应中提取有效JSON: {str(e)}", response_text, 0)
                        
                        # 显示解析后的JSON对象
                        self.log_message(f"解析后的JSON对象: {cards_data}")
                        
                        if 'cards' in cards_data and isinstance(cards_data['cards'], list):
                            cards = cards_data['cards']
                            self.log_message(f"从该片段中生成了 {len(cards)} 个学习卡片")
                            
                            # 打印每个卡片的内容
                            for i, card in enumerate(cards):
                                self.log_message(f"卡片 {i+1}:")
                                self.log_message(f"问题: {card.get('q', '无问题')}")
                                self.log_message(f"答案: {card.get('a', '无答案')}")
                            
                            # 增量保存卡片到CSV文件
                            with open(output_file, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                for card in cards:
                                    if 'q' in card and 'a' in card:
                                        question = card['q'].replace('\n', ' ').strip()
                                        answer = card['a'].replace('\n', ' ').strip()
                                        self.log_message(f"写入卡片: Q: {question[:30]}... A: {answer[:30]}...")
                                        writer.writerow([question, answer])
                                
                            self.log_message(f"已将 {len(cards)} 个卡片保存到文件: {output_file}")
                            return cards
                        else:
                            self.log_message(f"错误: 无法从响应中提取卡片数据，缺少'cards'字段或格式不正确")
                            return []
                    except json.JSONDecodeError as je:
                        self.log_message(f"JSON解析错误: {str(je)}")
                        self.log_message(f"无效的JSON字符串: {response_text}")
                        return []
                    except Exception as e:
                        self.log_message(f"处理响应时出错: {str(e)}")
                        self.log_message(f"异常类型: {type(e).__name__}")
                        import traceback
                        self.log_message(f"错误详情: {traceback.format_exc()}")
                        return []
                
                except Exception as e:
                    self.log_message(f"整体处理时出错: {str(e)}")
                    import traceback
                    self.log_message(f"详细错误堆栈: {traceback.format_exc()}")
                    return []
            
            def _clean_nested_code_blocks(self, json_str):
                """清理JSON字符串中可能存在的嵌套代码块标记"""
                self.log_message("正在清理嵌套代码块标记...")
                
                # 检查是否需要处理嵌套代码块
                if "```" not in json_str:
                    return json_str
                
                # 处理可能的嵌套代码块
                try:
                    # 尝试解析JSON结构
                    data = json.loads(json_str)
                    
                    # 如果成功解析为JSON，但包含cards字段
                    if 'cards' in data and isinstance(data['cards'], list):
                        # 遍历所有卡片
                        for card in data['cards']:
                            # 处理答案字段中的代码块
                            if 'a' in card and isinstance(card['a'], str):
                                # 替换所有的代码块标记为普通文本
                                card['a'] = card['a'].replace('```', '⟪code⟫')
                        
                        # 将修改后的数据重新序列化为JSON字符串
                        fixed_json = json.dumps(data)
                        self.log_message(f"嵌套代码块清理完成")
                        return fixed_json
                    else:
                        return json_str
                except Exception as e:
                    self.log_message(f"清理嵌套代码块时出错: {str(e)}")
                    
                    # 如果无法解析JSON，则使用正则表达式替换
                    import re
                    # 替换任何不在卡片内容中的代码块标记
                    fixed_json = re.sub(r'```[^`]*```', '', json_str)
                    # 替换任何剩余的代码块开始和结束标记
                    fixed_json = fixed_json.replace('```', '')
                    
                    self.log_message(f"使用正则表达式清理嵌套代码块")
                    return fixed_json
                
            def run(self):
                """在后台线程中执行卡片生成任务"""
                try:
                    # 确保输出目录存在
                    if not os.path.exists(self.output_dir):
                        os.makedirs(self.output_dir)
                        self.log_message(f"创建输出目录: {self.output_dir}")
                    else:
                        self.log_message(f"使用现有输出目录: {self.output_dir}")
                    
                    # 初始化统计信息
                    total_files = len(self.files)
                    processed_files = 0
                    successful_files = 0
                    
                    self.log_message(f"\n{'='*30} 开始处理 {'='*30}")
                    self.log_message(f"当前使用模型: {self.model_name}")
                    self.log_message(f"待处理文件数量: {total_files} 个")
                    self.log_message(f"文件列表:")
                    for idx, file_path in enumerate(self.files):
                        self.log_message(f"  {idx+1}. {file_path}")
                    self.log_message(f"{'='*70}\n")
                    
                    # 为每个文件生成卡片
                    for i, file_path in enumerate(self.files, 1):
                        # 检查是否应该停止处理
                        if self.check_if_should_stop():
                            self.log_message("\n--- 处理已被用户中断 ---")
                            self.signals.finished.emit(False, "用户中断处理")
                            return
                        
                        self.log_message(f"\n{'*'*30} 开始处理文件 {i}/{total_files} {'*'*30}")
                        self.log_message(f"当前文件: {file_path}")
                        
                        processed_files += 1
                        
                        # 处理当前文件
                        start_time = time.time()
                        success = self.process_file(file_path, i, total_files)
                        end_time = time.time()
                        
                        if success:
                            successful_files += 1
                            self.log_message(f"文件处理成功，耗时: {end_time - start_time:.2f}秒")
                        else:
                            self.log_message(f"文件处理失败，耗时: {end_time - start_time:.2f}秒")
                        
                        self.log_message(f"{'*'*30} 文件 {i}/{total_files} 处理完成 {'*'*30}\n")
                    
                    # 完成处理
                    if not self.check_if_should_stop():  # 如果不是因为中断而结束
                        self.log_message(f"\n{'='*20} 处理完成统计 {'='*20}")
                        self.log_message(f"总文件数: {total_files}")
                        self.log_message(f"处理文件数: {processed_files}")
                        self.log_message(f"成功文件数: {successful_files}")
                        self.log_message(f"失败文件数: {processed_files - successful_files}")
                        self.log_message(f"成功率: {successful_files/processed_files*100:.2f}% 如果有失败的文件")
                        self.log_message(f"学习卡片已保存到目录: {self.output_dir}")
                        self.log_message(f"{'='*60}")
                        self.signals.finished.emit(True, f"完成 - 处理了 {successful_files}/{total_files} 个文件")
                    else:
                        self.signals.finished.emit(False, "用户中断处理")
                        
                except Exception as e:
                    self.log_message(f"生成学习卡片出错: {str(e)}")
                    self.signals.finished.emit(False, f"错误: {str(e)}")
        
        # 获取输出目录
        output_dir = "output_cards"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_dir = os.path.abspath(output_dir)
        self.output_dir = output_dir
            
        self.output_area.append(f"开始处理文件，输出到目录: {output_dir}\n")
        
        # 创建worker并保存引用
        self.current_worker = CardGeneratorWorker(self, files, output_dir)
        
        # 连接信号
        self.current_worker.signals.progress.connect(self.update_progress)
        self.current_worker.signals.log.connect(self.output_area.append)
        self.current_worker.signals.file_processed.connect(self.add_output_file)
        self.current_worker.signals.finished.connect(self.handle_processing_finished)
        
        # 启动worker
        self.thread_pool.start(self.current_worker)
        
    def handle_processing_finished(self, success, message):
        """处理完成的回调"""
        # 恢复UI状态
        self.is_processing = False
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText('准备就绪')
        
        # 详细日志输出
        self.output_area.append("\n" + "="*50)
        self.output_area.append("处理完成状态摘要:")
        self.output_area.append(f"成功状态: {'成功' if success else '失败'}")
        self.output_area.append(f"状态消息: {message}")
        self.output_area.append(f"输出目录: {self.output_dir}")
        
        # 如果有输出文件，确保显示文件列表区域
        if self.output_files:
            self.output_area.append(f"生成文件数量: {len(self.output_files)}")
            self.output_area.append("生成文件列表:")
            for i, file_path in enumerate(self.output_files):
                # 从列表项中获取描述
                item = self.output_files_list.item(i)
                if item:
                    item_text = item.text()
                    # 从项目文本中提取描述部分
                    desc = item_text.split(' - ', 1)[1] if ' - ' in item_text else '无描述'
                    self.output_area.append(f"  {i+1}. {os.path.basename(file_path)} - {desc}")
                else:
                    self.output_area.append(f"  {i+1}. {os.path.basename(file_path)}")
            
            self.output_files_widget.setVisible(True)
        else:
            self.output_area.append("没有生成任何文件")
            
        # 最终更新进度条并隐藏
        if success:
            self.progress_bar.setValue(100)
        else:
            self.progress_bar.setValue(0)
            
        # 一秒后隐藏进度条
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
        
        # 完成消息
        self.output_area.append(f"\n{message}")
        
        # 添加提示消息
        if self.output_files:
            self.output_area.append(f"\n您可以双击列表中的文件直接打开查看")
            self.output_area.append(f"文件已保存在: {self.output_dir}")
        
        self.output_area.append("="*50)

    def split_md_by_title(self, md_file_path, output_dir):
        """按标题切割Markdown文件"""
        try:
            with open(md_file_path, 'r', encoding='utf-8') as md_file:
                content = md_file.readlines()
            
            file_content = []
            file_counter = 1  # 文件编号
            
            for line in content:
                # 跳过以 #include 开头的行
                if line.strip().startswith("#include"):
                    continue
                if "https://" in line or "http://" in line:  # 跳过链接
                    continue
                
                # 处理一级标题、二级标题或三级标题
                if line.startswith('#') and line.count('#') in [1, 2, 3]:
                    # 如果当前内容有实际内容且不为空，保存
                    if file_content:
                        cleaned_content = self.clean_content(file_content)
                        if cleaned_content:  # 如果清理后的内容不为空
                            file_name = f"{file_counter:03d}.md"
                            file_path = os.path.join(output_dir, file_name)
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
                            with open(file_path, 'w', encoding='utf-8') as section_file:
                                section_file.writelines(cleaned_content)
                            file_counter += 1
                    
                    # 开始新的内容段落，保留标题
                    file_content = [line]
                else:
                    # 添加当前内容行
                    file_content.append(line)
            
            # 保存最后一部分的内容
            if file_content:
                cleaned_content = self.clean_content(file_content)
                if cleaned_content:  # 如果清理后的内容不为空
                    file_name = f"{file_counter:03d}.md"
                    file_path = os.path.join(output_dir, file_name)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
                    with open(file_path, 'w', encoding='utf-8') as section_file:
                        section_file.writelines(cleaned_content)
                    file_counter += 1
            
            return file_counter - 1  # 返回实际创建的文件数量
        
        except Exception as e:
            self.output_area.append(f"切割文件时出错: {str(e)}")
            return 0
    
    def clean_content(self, content_lines):
        """清理内容，去除空行和无用信息"""
        cleaned_lines = []
        has_content = False
        
        for line in content_lines:
            line = line.rstrip()
            
            # 跳过纯空行和只包含空白字符的行
            if not line.strip():
                continue
                
            # 添加有内容的行
            cleaned_lines.append(line + '\n')
            
            # 如果不是标题行，标记为有实际内容
            if not line.strip().startswith('#'):
                has_content = True
        
        # 如果只有标题没有内容，或者清理后完全为空，则返回空
        if not has_content or not cleaned_lines:
            return []
            
        return cleaned_lines

    def load_system_prompts(self):
        """加载系统提示词文件夹中的提示词文件"""
        import os
        
        self.system_prompt_selector.blockSignals(True)
        current_selection = self.system_prompt_selector.currentText()
        
        # 清除当前列表，保留"无"选项
        self.system_prompt_selector.clear()
        self.system_prompt_selector.addItem('无')
        
        # 系统提示词文件夹路径 - 修改为使用当前工作目录
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        print(f"系统提示词文件夹路径: {prompts_dir}")
        
        # 确保文件夹存在
        if not os.path.exists(prompts_dir):
            try:
                os.makedirs(prompts_dir)
                if hasattr(self, 'output_area'):
                    self.output_area.append(f"已创建系统提示词文件夹: {prompts_dir}")
                print(f"已创建系统提示词文件夹: {prompts_dir}")
            except Exception as e:
                if hasattr(self, 'output_area'):
                    self.output_area.append(f"创建系统提示词文件夹失败: {str(e)}")
                print(f"创建系统提示词文件夹失败: {str(e)}")
                self.system_prompt_selector.blockSignals(False)
                return
        
        # 列出文件夹中的文本文件
        try:
            files = [f for f in os.listdir(prompts_dir) if f.endswith(('.txt', '.md'))]
            files.sort()  # 按字母顺序排序
            
            for file in files:
                # 添加文件名（不含扩展名）
                prompt_name = os.path.splitext(file)[0]
                self.system_prompt_selector.addItem(prompt_name)
            
            if hasattr(self, 'output_area'):
                self.output_area.append(f"已加载 {len(files)} 个系统提示词")
            print(f"已加载 {len(files)} 个系统提示词")
            
            # 尝试恢复之前的选择
            if current_selection and self.system_prompt_selector.findText(current_selection) >= 0:
                self.system_prompt_selector.setCurrentText(current_selection)
                
        except Exception as e:
            if hasattr(self, 'output_area'):
                self.output_area.append(f"加载系统提示词失败: {str(e)}")
            print(f"加载系统提示词失败: {str(e)}")
        
        self.system_prompt_selector.blockSignals(False)
    
    def open_system_prompts_folder(self):
        """打开系统提示词文件夹"""
        import os
        import subprocess
        
        # 系统提示词文件夹路径 - 修改为使用当前工作目录
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        print(f"系统提示词文件夹路径: {prompts_dir}")
        
        # 确保文件夹存在
        if not os.path.exists(prompts_dir):
            try:
                os.makedirs(prompts_dir)
                self.output_area.append(f"已创建系统提示词文件夹: {prompts_dir}")
                print(f"已创建系统提示词文件夹: {prompts_dir}")
            except Exception as e:
                self.output_area.append(f"创建系统提示词文件夹失败: {str(e)}")
                print(f"创建系统提示词文件夹失败: {str(e)}")
                return
        
        # 打开文件夹
        try:
            # 使用操作系统默认的文件浏览器打开文件夹
            if os.name == 'nt':  # Windows
                os.startfile(prompts_dir)
            elif os.name == 'posix':  # Linux, Mac OS X
                if os.uname().sysname == 'Darwin':  # Mac OS X
                    subprocess.call(['open', prompts_dir])
                else:  # Linux
                    subprocess.call(['xdg-open', prompts_dir])
            
            self.output_area.append(f"已打开系统提示词文件夹: {prompts_dir}")
            print(f"已打开系统提示词文件夹: {prompts_dir}")
        except Exception as e:
            self.output_area.append(f"打开系统提示词文件夹失败: {str(e)}")
            print(f"打开系统提示词文件夹失败: {str(e)}")
            
    def get_selected_system_prompt(self):
        """获取选中的系统提示词内容"""
        import os
        
        selected_prompt = self.system_prompt_selector.currentText()
        if selected_prompt == '无':
            return None
            
        # 系统提示词文件夹路径 - 修改为使用当前工作目录
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        
        # 查找可能的文件扩展名
        for ext in ['.txt', '.md']:
            prompt_file = os.path.join(prompts_dir, selected_prompt + ext)
            if os.path.exists(prompt_file):
                try:
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        return f.read().strip()
                except Exception as e:
                    self.output_area.append(f"读取系统提示词文件失败: {str(e)}")
                    print(f"读取系统提示词文件失败: {str(e)}")
                    return None
        
        self.output_area.append(f"系统提示词文件不存在: {selected_prompt}")
        print(f"系统提示词文件不存在: {selected_prompt}")
        return None

class CompletionTab(BaseTab):
    def __init__(self, api_handler):
        super().__init__(api_handler)
        self.setup_components()

    def setup_components(self):
        from config import Config
        layout = QVBoxLayout()
        
        # 创建系统提示词选择行
        system_prompt_layout = QHBoxLayout()
        self.system_prompt_selector = QComboBox()
        self.system_prompt_selector.addItem('无')  # 默认选项
        self.load_system_prompts()  # 加载系统提示词文件
        
        # 打开系统提示词文件夹按钮
        open_prompts_folder_btn = QPushButton('打开文件夹')
        open_prompts_folder_btn.setToolTip('打开系统提示词文件夹')
        open_prompts_folder_btn.clicked.connect(self.open_system_prompts_folder)
        open_prompts_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #78909C;
            }
            QPushButton:pressed {
                background-color: #455A64;
            }
        """)
        
        # 刷新系统提示词按钮
        refresh_prompts_btn = QPushButton('刷新')
        refresh_prompts_btn.setToolTip('刷新系统提示词列表')
        refresh_prompts_btn.clicked.connect(self.load_system_prompts)
        refresh_prompts_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #26C6DA;
            }
            QPushButton:pressed {
                background-color: #0097A7;
            }
        """)
        
        # 添加到布局
        system_prompt_layout.addWidget(QLabel('系统提示词：'))
        system_prompt_layout.addWidget(self.system_prompt_selector)
        system_prompt_layout.addWidget(refresh_prompts_btn)
        system_prompt_layout.addWidget(open_prompts_folder_btn)
        system_prompt_layout.addStretch()
        
        # 直接添加布局到垂直布局，与处理选择器保持一致
        layout.addLayout(system_prompt_layout)
        
        # 保留系统提示词容器的引用，但不再添加到布局中
        self.system_prompt_container = QWidget()
        self.system_prompt_container.setLayout(QHBoxLayout())
        self.system_prompt_container.setVisible(True)
        
        # 添加提示文字和生成按钮
        prompt_label = QLabel('输入提示词:')
        layout.addWidget(prompt_label)
        
        self.prompt_input = QTextEdit()
        layout.addWidget(self.prompt_input)
        
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton('生成')
        self.generate_btn.clicked.connect(self.generate_completion)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                padding: 9px 16px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        self.stop_btn = QPushButton('停止')
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
            QPushButton:pressed {
                background-color: #d32f2f;
                padding: 9px 16px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #ffcdd2;
                color: #b71c1c;
            }
        """)
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        output_label = QLabel('生成结果:')
        layout.addWidget(output_label)
        
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)
        
        # 设置主布局
        widget = QWidget()
        widget.setLayout(layout)
        self.layout.addWidget(widget)
        
    def load_system_prompts(self):
        """加载系统提示词文件夹中的提示词文件"""
        import os
        
        self.system_prompt_selector.blockSignals(True)
        current_selection = self.system_prompt_selector.currentText()
        
        # 清除当前列表，保留"无"选项
        self.system_prompt_selector.clear()
        self.system_prompt_selector.addItem('无')
        
        # 系统提示词文件夹路径 - 修改为使用当前工作目录
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        print(f"系统提示词文件夹路径: {prompts_dir}")
        
        # 确保文件夹存在
        if not os.path.exists(prompts_dir):
            try:
                os.makedirs(prompts_dir)
                if hasattr(self, 'output_area'):
                    self.output_area.append(f"已创建系统提示词文件夹: {prompts_dir}")
                print(f"已创建系统提示词文件夹: {prompts_dir}")
            except Exception as e:
                if hasattr(self, 'output_area'):
                    self.output_area.append(f"创建系统提示词文件夹失败: {str(e)}")
                print(f"创建系统提示词文件夹失败: {str(e)}")
                self.system_prompt_selector.blockSignals(False)
                return
        
        # 列出文件夹中的文本文件
        try:
            files = [f for f in os.listdir(prompts_dir) if f.endswith(('.txt', '.md'))]
            files.sort()  # 按字母顺序排序
            
            for file in files:
                # 添加文件名（不含扩展名）
                prompt_name = os.path.splitext(file)[0]
                self.system_prompt_selector.addItem(prompt_name)
            
            if hasattr(self, 'output_area'):
                self.output_area.append(f"已加载 {len(files)} 个系统提示词")
            print(f"已加载 {len(files)} 个系统提示词")
            
            # 尝试恢复之前的选择
            if current_selection and self.system_prompt_selector.findText(current_selection) >= 0:
                self.system_prompt_selector.setCurrentText(current_selection)
                
        except Exception as e:
            self.output_area.append(f"加载系统提示词失败: {str(e)}")
        
        self.system_prompt_selector.blockSignals(False)
    
    def open_system_prompts_folder(self):
        """打开系统提示词文件夹"""
        import os
        import subprocess
        
        # 系统提示词文件夹路径 - 修改为使用当前工作目录
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        print(f"系统提示词文件夹路径: {prompts_dir}")
        
        # 确保文件夹存在
        if not os.path.exists(prompts_dir):
            try:
                os.makedirs(prompts_dir)
                self.output_area.append(f"已创建系统提示词文件夹: {prompts_dir}")
                print(f"已创建系统提示词文件夹: {prompts_dir}")
            except Exception as e:
                self.output_area.append(f"创建系统提示词文件夹失败: {str(e)}")
                print(f"创建系统提示词文件夹失败: {str(e)}")
                return
        
        # 打开文件夹
        try:
            # 使用操作系统默认的文件浏览器打开文件夹
            if os.name == 'nt':  # Windows
                os.startfile(prompts_dir)
            elif os.name == 'posix':  # Linux, Mac OS X
                if os.uname().sysname == 'Darwin':  # Mac OS X
                    subprocess.call(['open', prompts_dir])
                else:  # Linux
                    subprocess.call(['xdg-open', prompts_dir])
            
            self.output_area.append(f"已打开系统提示词文件夹: {prompts_dir}")
            print(f"已打开系统提示词文件夹: {prompts_dir}")
        except Exception as e:
            self.output_area.append(f"打开系统提示词文件夹失败: {str(e)}")
            print(f"打开系统提示词文件夹失败: {str(e)}")
            
    def get_selected_system_prompt(self):
        """获取选中的系统提示词内容"""
        import os
        
        selected_prompt = self.system_prompt_selector.currentText()
        if selected_prompt == '无':
            return None
            
        # 系统提示词文件夹路径 - 修改为使用当前工作目录
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        
        # 查找可能的文件扩展名
        for ext in ['.txt', '.md']:
            prompt_file = os.path.join(prompts_dir, selected_prompt + ext)
            if os.path.exists(prompt_file):
                try:
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        return f.read().strip()
                except Exception as e:
                    self.output_area.append(f"读取系统提示词文件失败: {str(e)}")
                    print(f"读取系统提示词文件失败: {str(e)}")
                    return None
        
        self.output_area.append(f"系统提示词文件不存在: {selected_prompt}")
        print(f"系统提示词文件不存在: {selected_prompt}")
        return None
        
    def generate_completion(self):
        """生成文本补全"""
        from config import Config
        
        # 获取提示词
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            self.output_area.append("错误: 请输入提示词")
            return
            
        # 获取系统提示词（如果选择了）
        system_prompt = None
        # 修改：无论使用何种模型来源，都可以使用系统提示词
        # if Config.MODEL_SOURCE == '远程API模型':
        system_prompt = self.get_selected_system_prompt()
        if system_prompt:
            self.output_area.append(f"使用系统提示词: {system_prompt[:100]}..." if len(system_prompt) > 100 else f"使用系统提示词: {system_prompt}")
        
        # 禁用生成按钮
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 清空输出区域
        self.output_area.clear()
        self.output_area.append("正在生成...\n")
        
        # 更新界面
        QApplication.processEvents()
        
        try:
            # 使用系统提示词
            # 修改：无论使用何种模型来源，都可以使用系统提示词
            # if system_prompt and Config.MODEL_SOURCE == '远程API模型':
            if system_prompt:
                # 创建包含系统提示词的消息列表
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                
                # 使用消息格式调用API
                self.output_area.append("使用系统提示词进行API调用...\n")
                response = self.api_handler.generate_completion(
                    model=Config.SELECTED_MODEL,
                    prompt=messages
                )
            else:
                # 常规API调用
                response = self.api_handler.generate_completion(
                    model=Config.SELECTED_MODEL,
                    prompt=prompt
                )
                
            # 处理响应
            if isinstance(response, dict) and 'error' in response:
                self.output_area.append(f"错误: {response['error']}\n")
            else:
                # 尝试提取生成的文本
                response_text = ""
                
                # 如果是OpenAI/DeepSeek格式响应
                if isinstance(response, dict) and 'choices' in response:
                    # 从第一个选择中获取消息内容
                    if len(response['choices']) > 0:
                        choice = response['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            response_text = choice['message']['content']
                        elif 'text' in choice:
                            response_text = choice['text']
                        else:
                            response_text = str(choice)
                else:
                    # 常规响应格式
                    response_text = response.get('response', '') if isinstance(response, dict) else str(response)
                
                self.output_area.append(response_text)
                
        except Exception as e:
            import traceback
            self.output_area.append(f"生成过程中出错: {str(e)}\n")
            self.output_area.append(traceback.format_exc())
        finally:
            # 恢复按钮状态
            self.generate_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            # 滚动到底部
            cursor = self.output_area.textCursor()
            cursor.movePosition(cursor.End)
            self.output_area.setTextCursor(cursor)

class ChatTab(BaseTab):
    class ChatWorker(QRunnable):
        class Signals(QObject):
            finished = pyqtSignal(str)
            error = pyqtSignal(str)
            
        def __init__(self, parent, chat_history):
            super().__init__()
            self.signals = self.Signals()
            self.parent = parent
            self.chat_history = chat_history
            self.api_handler = parent.api_handler
            self.model_name = Config.SELECTED_MODEL
            
        def run(self):
            try:
                # 获取系统提示词（如果选择了）
                system_prompt = None
                if hasattr(self.parent, 'get_selected_system_prompt'):
                    system_prompt = self.parent.get_selected_system_prompt()
                    if system_prompt:
                        print(f"\n[系统提示词] {system_prompt[:100]}..." if len(system_prompt) > 100 else f"\n[系统提示词] {system_prompt}")
                
                # 准备消息列表
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.extend(self.chat_history)
                
                # 打印当前使用的模型
                print(f"\n[模型信息] 当前使用模型: {self.model_name}")
                
                # 打印思考内容
                print("\n[思考内容]")
                for msg in messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    print(f"{role}: {content[:200]}..." if len(content) > 200 else f"{role}: {content}")
                
                # 调用API生成响应
                print(f"\n[API调用] 正在调用API，使用模型: {self.model_name}")
                response = self.api_handler.generate_completion(
                    model=self.model_name,
                    prompt=messages
                )
                
                # 处理响应
                if isinstance(response, dict) and 'error' in response:
                    self.signals.error.emit(response['error'])
                    return
                    
                # 提取响应文本
                response_text = ""
                if isinstance(response, dict) and 'choices' in response:
                    if len(response['choices']) > 0:
                        choice = response['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            response_text = choice['message']['content']
                            print(f"\n[模型响应] {response_text[:200]}..." if len(response_text) > 200 else f"\n[模型响应] {response_text}")
                        elif 'text' in choice:
                            response_text = choice['text']
                            print(f"\n[模型响应] {response_text[:200]}..." if len(response_text) > 200 else f"\n[模型响应] {response_text}")
                        else:
                            response_text = str(choice)
                            print(f"\n[模型响应] {response_text[:200]}..." if len(response_text) > 200 else f"\n[模型响应] {response_text}")
                else:
                    response_text = response.get('response', '') if isinstance(response, dict) else str(response)
                    print(f"\n[模型响应] {response_text[:200]}..." if len(response_text) > 200 else f"\n[模型响应] {response_text}")
                
                if not response_text:
                    self.signals.error.emit("未获取到有效响应")
                    return
                    
                self.signals.finished.emit(response_text)
                
            except Exception as e:
                import traceback
                error_msg = f"生成响应时出错: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                self.signals.error.emit(error_msg)

    def __init__(self, api_handler):
        super().__init__(api_handler)
        self.setup_ui_components()
        self.chat_history = []  # 存储对话历史
        self.is_processing = False  # 处理状态标志
        
    def setup_ui_components(self):
        """设置UI组件"""
        # 创建主布局
        layout = QVBoxLayout()
        
        # 创建系统提示词选择行
        system_prompt_layout = QHBoxLayout()
        self.system_prompt_selector = QComboBox()
        self.system_prompt_selector.addItem('无')  # 默认选项
        
        # 打开系统提示词文件夹按钮
        open_prompts_folder_btn = QPushButton('打开文件夹')
        open_prompts_folder_btn.setToolTip('打开系统提示词文件夹')
        open_prompts_folder_btn.clicked.connect(self.open_system_prompts_folder)
        open_prompts_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #78909C;
            }
            QPushButton:pressed {
                background-color: #455A64;
            }
        """)
        
        # 刷新系统提示词按钮
        refresh_prompts_btn = QPushButton('刷新')
        refresh_prompts_btn.setToolTip('刷新系统提示词列表')
        refresh_prompts_btn.clicked.connect(self.load_system_prompts)
        refresh_prompts_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #26C6DA;
            }
            QPushButton:pressed {
                background-color: #0097A7;
            }
        """)
        
        # 添加到布局
        system_prompt_layout.addWidget(QLabel('系统提示词：'))
        system_prompt_layout.addWidget(self.system_prompt_selector)
        system_prompt_layout.addWidget(refresh_prompts_btn)
        system_prompt_layout.addWidget(open_prompts_folder_btn)
        system_prompt_layout.addStretch()
        
        # 添加系统提示词布局
        layout.addLayout(system_prompt_layout)
        
        # 加载系统提示词
        self.load_system_prompts()
        
        # 创建对话历史区域
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                color: #333;
                font-family: Consolas, Monaco, monospace;
                min-height: 300px;
            }
        """)
        layout.addWidget(self.chat_area)
        
        # 创建输入区域
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        
        # 添加输入框
        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText("在此输入您的问题...")
        self.input_area.setMaximumHeight(100)  # 限制输入框高度
        self.input_area.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                color: #333;
                font-family: Consolas, Monaco, monospace;
            }
        """)
        input_layout.addWidget(self.input_area)
        
        # 添加按钮区域
        button_layout = QHBoxLayout()
        
        # 发送按钮
        self.send_btn = QPushButton('发送')
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                padding: 9px 16px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        # 清除按钮
        self.clear_btn = QPushButton('清除对话')
        self.clear_btn.clicked.connect(self.clear_chat)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
            QPushButton:pressed {
                background-color: #d32f2f;
                padding: 9px 16px 7px 16px;
            }
            QPushButton:disabled {
                background-color: #ffcdd2;
                color: #b71c1c;
            }
        """)
        
        # 添加按钮到布局
        button_layout.addWidget(self.send_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        input_layout.addLayout(button_layout)
        layout.addWidget(input_container)
        
        # 设置主布局
        self.layout.addLayout(layout)
        
        # 连接回车键发送消息
        self.input_area.keyPressEvent = self.handle_key_press
        
        # 连接系统提示词选择变化事件
        self.system_prompt_selector.currentTextChanged.connect(self.on_system_prompt_changed)
        
    def on_system_prompt_changed(self, prompt_name):
        """当系统提示词选择改变时，更新对话历史中的系统提示词"""
        if not self.chat_history:
            return
            
        # 获取新的系统提示词
        new_system_prompt = self.get_selected_system_prompt()
        
        # 更新对话历史中的系统提示词
        if self.chat_history and self.chat_history[0].get('role') == 'system':
            if new_system_prompt:
                self.chat_history[0]['content'] = new_system_prompt
            else:
                self.chat_history.pop(0)
        elif new_system_prompt:
            self.chat_history.insert(0, {'role': 'system', 'content': new_system_prompt})
            
    def handle_key_press(self, event):
        """处理按键事件"""
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            # Ctrl + Enter 发送消息
            self.send_message()
        else:
            # 其他按键使用默认处理
            QTextEdit.keyPressEvent(self.input_area, event)
            
    def send_message(self):
        """发送消息"""
        message = self.input_area.toPlainText().strip()
        if not message:
            return
            
        # 添加调试信息
        print(f"\n[调试] 发送消息:")
        print(f"消息内容: {message}")
        print(f"当前对话历史长度: {len(self.chat_history)}")
        
        # 禁用输入区域和发送按钮
        self.input_area.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # 清空输入区域
        self.input_area.clear()
        
        # 添加用户消息到对话历史
        self.chat_history.append({"role": "user", "content": message})
        
        # 更新对话显示
        self.chat_area.append(f"\n用户: {message}\n")
        
        # 创建并启动工作线程
        worker = self.ChatWorker(self, self.chat_history)
        worker.signals.finished.connect(self.handle_response)
        worker.signals.error.connect(self.handle_error)
        QThreadPool.globalInstance().start(worker)

    def handle_response(self, response_text):
        """处理模型响应"""
        # 添加调试信息
        print(f"\n[调试] 收到模型响应:")
        print(f"响应内容: {response_text[:200]}...")  # 只显示前200个字符
        print(f"响应长度: {len(response_text)}")
        
        # 添加助手消息到对话历史
        self.chat_history.append({"role": "assistant", "content": response_text})
        
        # 更新对话显示
        self.chat_area.append(f"\n助手: {response_text}\n")
        
        # 重新启用输入区域和发送按钮
        self.input_area.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        # 滚动到底部
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
        
        # 添加调试信息
        print(f"当前对话历史长度: {len(self.chat_history)}")
        print(f"最后一条消息角色: {self.chat_history[-1]['role']}")
        print(f"最后一条消息长度: {len(self.chat_history[-1]['content'])}")

    def handle_error(self, error_message):
        """处理错误"""
        # 添加调试信息
        print(f"\n[调试] 发生错误:")
        print(f"错误信息: {error_message}")
        print(f"当前对话历史长度: {len(self.chat_history)}")
        
        # 显示错误消息
        self.chat_area.append(f"\n错误: {error_message}\n")
        
        # 重新启用输入区域和发送按钮
        self.input_area.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        # 滚动到底部
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
        
    def clear_chat(self):
        """清除对话历史"""
        # 取消当前的生成请求
        if hasattr(self.api_handler, 'cancel_generation'):
            self.api_handler.cancel_generation()
            
        # 清空对话历史
        self.chat_history = []
        self.chat_area.clear()
        self.chat_area.append("对话已清除")
    
    def load_system_prompts(self):
        """加载系统提示词文件夹中的提示词文件"""
        import os
        
        self.system_prompt_selector.blockSignals(True)
        current_selection = self.system_prompt_selector.currentText()
        
        # 清除当前列表，保留"无"选项
        self.system_prompt_selector.clear()
        self.system_prompt_selector.addItem('无')
        
        # 系统提示词文件夹路径
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        
        # 确保文件夹存在
        if not os.path.exists(prompts_dir):
            try:
                os.makedirs(prompts_dir)
            except Exception as e:
                print(f"创建系统提示词文件夹失败: {str(e)}")
                self.system_prompt_selector.blockSignals(False)
                return
        
        # 列出文件夹中的文本文件
        try:
            files = [f for f in os.listdir(prompts_dir) if f.endswith(('.txt', '.md'))]
            files.sort()  # 按字母顺序排序
            
            for file in files:
                # 添加文件名（不含扩展名）
                prompt_name = os.path.splitext(file)[0]
                self.system_prompt_selector.addItem(prompt_name)
            
            # 尝试恢复之前的选择
            if current_selection and self.system_prompt_selector.findText(current_selection) >= 0:
                self.system_prompt_selector.setCurrentText(current_selection)
                
        except Exception as e:
            print(f"加载系统提示词失败: {str(e)}")
        
        self.system_prompt_selector.blockSignals(False)
    
    def open_system_prompts_folder(self):
        """打开系统提示词文件夹"""
        import os
        import subprocess
        
        # 系统提示词文件夹路径
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        
        # 确保文件夹存在
        if not os.path.exists(prompts_dir):
            try:
                os.makedirs(prompts_dir)
            except Exception as e:
                print(f"创建系统提示词文件夹失败: {str(e)}")
                return
        
        # 打开文件夹
        try:
            if os.name == 'nt':  # Windows
                os.startfile(prompts_dir)
            elif os.name == 'posix':  # Linux, Mac OS X
                if os.uname().sysname == 'Darwin':  # Mac OS X
                    subprocess.call(['open', prompts_dir])
                else:  # Linux
                    subprocess.call(['xdg-open', prompts_dir])
        except Exception as e:
            print(f"打开系统提示词文件夹失败: {str(e)}")
            
    def get_selected_system_prompt(self):
        """获取选中的系统提示词内容"""
        import os
        
        selected_prompt = self.system_prompt_selector.currentText()
        if selected_prompt == '无':
            return None
            
        # 系统提示词文件夹路径
        cwd = os.getcwd()
        prompts_dir = os.path.join(cwd, 'system_prompts')
        
        # 查找可能的文件扩展名
        for ext in ['.txt', '.md']:
            prompt_file = os.path.join(prompts_dir, selected_prompt + ext)
            if os.path.exists(prompt_file):
                try:
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        return f.read().strip()
                except Exception as e:
                    print(f"读取系统提示词文件失败: {str(e)}")
                    return None
        
        print(f"系统提示词文件不存在: {selected_prompt}")
        return None
