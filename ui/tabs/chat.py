"""
聊天标签页模块
提供基于对话的交互功能
"""

from PyQt5.QtCore import QObject, pyqtSignal
from core import Config
from .base import BaseTab
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QTextEdit, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThreadPool, QRunnable

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
        system_prompt_layout.addWidget(QLabel('问答风格：'))
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
