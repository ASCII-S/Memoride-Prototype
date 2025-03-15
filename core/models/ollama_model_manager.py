"""
模型管理器模块
处理Ollama模型的安装、管理和其他相关操作
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QHBoxLayout,
    QLineEdit, QProgressBar, QCheckBox, QDialogButtonBox, QApplication, QPushButton
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

class OllamaModelManager:
    """Ollama模型管理器类，负责安装和管理Ollama模型"""
    
    def __init__(self, parent_window):
        """初始化模型管理器
        
        Args:
            parent_window: 父窗口，用于显示对话框
        """
        self.parent = parent_window
        self.install_thread = None
        self.local_models = []
    
    def install_ollama_model(self):
        """提供Ollama模型安装指导"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("安装Ollama模型")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # 添加说明文本
        info_label = QLabel("选择要安装的Ollama模型：")
        layout.addWidget(info_label)
        
        # 创建模型选择组合框
        model_combo = QComboBox()
        popular_models = ["llama3", "llama3:8b", "llama3:70b", "codellama", "mistral", "mixtral", "gemma:2b", "gemma:7b", "phi3:mini"]
        model_combo.addItems(popular_models)
        layout.addWidget(model_combo)
        
        # 添加自定义模型输入框
        custom_layout = QHBoxLayout()
        custom_label = QLabel("或输入自定义模型名称：")
        custom_input = QLineEdit()
        custom_input.setPlaceholderText("例如：stable-code:latest")
        custom_layout.addWidget(custom_label)
        custom_layout.addWidget(custom_input)
        layout.addLayout(custom_layout)
        
        # 检测当前系统
        import platform
        system = platform.system().lower()
        
        # 对于Windows系统，添加PowerShell选项
        use_powershell = False
        if system == "windows":
            ps_checkbox = QCheckBox("使用PowerShell安装模型（推荐）")
            ps_checkbox.setChecked(True)  # 默认选中
            layout.addWidget(ps_checkbox)
            use_powershell = True
        
        # 添加状态标签
        status_label = QLabel("")
        layout.addWidget(status_label)
        
        # 添加进度条
        progress = QProgressBar()
        progress.setRange(0, 100)  # 设置为确定模式
        progress.setVisible(False)
        layout.addWidget(progress)
        
        # 添加按钮
        button_box = QDialogButtonBox()
        install_btn = button_box.addButton("安装", QDialogButtonBox.AcceptRole)
        close_btn = button_box.addButton("关闭", QDialogButtonBox.RejectRole)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 安装模型的函数
        def start_model_installation():
            # 获取选择的模型
            model_name = custom_input.text() if custom_input.text() else model_combo.currentText()
            
            if not model_name:
                status_label.setText("请选择或输入模型名称")
                status_label.setStyleSheet("color: red;")
                return
            
            # 更新UI状态
            status_label.setText(f"正在安装模型 {model_name}，这可能需要一些时间...")
            status_label.setStyleSheet("color: blue;")
            progress.setVisible(True)
            install_btn.setEnabled(False)
            custom_input.setEnabled(False)
            model_combo.setEnabled(False)
            if system == "windows":
                ps_checkbox.setEnabled(False)
            QApplication.processEvents()
            
            # 使用QThread执行安装任务
            class ModelInstallThread(QThread):
                finished_signal = pyqtSignal(bool, str)
                progress_signal = pyqtSignal(int)  # 新增信号用于传递进度
                cancel_signal = pyqtSignal()  # 新增信号用于取消安装
                
                def __init__(self, model_name, use_powershell=False):
                    super().__init__()
                    self.model_name = model_name
                    self.use_powershell = use_powershell and system == "windows"
                    self._is_cancelled = False  # 用于标记是否取消
                
                def run(self):
                    import subprocess
                    from tqdm import tqdm
                    from ollama import pull
                    try:
                        current_digest, bars = '', {}
                        for progress_data in pull(self.model_name, stream=True):
                            if self._is_cancelled:
                                self.finished_signal.emit(False, "安装已取消")
                                return

                            digest = progress_data.get('digest', '')
                            if digest != current_digest and current_digest in bars:
                                bars[current_digest].close()

                            if not digest:
                                print(progress_data.get('status'))
                                continue

                            if digest not in bars and (total := progress_data.get('total')):
                                bars[digest] = tqdm(total=total, desc=f'pulling {digest[7:19]}', unit='B', unit_scale=True)

                            if completed := progress_data.get('completed'):
                                bars[digest].update(completed - bars[digest].n)
                                # 发出进度信号
                                self.progress_signal.emit(int((completed / total) * 100))

                            current_digest = digest

                        self.finished_signal.emit(True, "模型安装成功")
                    except Exception as e:
                        self.finished_signal.emit(False, f"安装过程出错: {str(e)}")

                def cancel(self):
                    self._is_cancelled = True
            
            # 获取PowerShell选项状态
            use_ps = False
            if system == "windows":
                use_ps = ps_checkbox.isChecked()
            
            # 创建并启动线程
            self.install_thread = ModelInstallThread(model_name, use_ps)
            
            # 连接信号
            def on_install_finished(success, message):
                progress.setVisible(False)
                install_btn.setEnabled(True)
                custom_input.setEnabled(True)
                model_combo.setEnabled(True)
                if system == "windows":
                    ps_checkbox.setEnabled(True)
                
                if success:
                    status_label.setText(f"{message}！模型 {model_name} 已安装。")
                    status_label.setStyleSheet("color: green;")
                else:
                    status_label.setText(message)
                    status_label.setStyleSheet("color: red;")
                    
                    # 添加手动安装指南按钮
                    if system == "windows":
                        guide_btn = button_box.addButton("手动安装指南", QDialogButtonBox.HelpRole)
                        guide_btn.clicked.connect(lambda: self.show_manual_install_guide(model_name))
            
            self.install_thread.finished_signal.connect(on_install_finished)
            self.install_thread.progress_signal.connect(lambda value: progress.setValue(value))
            self.install_thread.cancel_signal.connect(self.install_thread.cancel)
            button_box.rejected.connect(lambda: self.install_thread.cancel())
            self.install_thread.start()
        
        # 连接安装按钮
        install_btn.clicked.connect(start_model_installation)
        
        dialog.exec_()
    
    def show_manual_install_guide(self, model_name):
        """显示手动安装模型的指南"""
        guide_dialog = QDialog(self.parent)
        guide_dialog.setWindowTitle("手动安装Ollama模型指南")
        guide_dialog.setMinimumWidth(550)
        
        layout = QVBoxLayout(guide_dialog)
        
        # 添加说明文本
        guide_text = f"""
        <h3>手动安装Ollama模型 {model_name} 的方法：</h3>
        
        <h4>使用PowerShell（推荐）:</h4>
        <ol>
          <li>按下Win+X，选择"Windows PowerShell"或"Windows终端"</li>
          <li>输入以下命令并按Enter:</li>
        </ol>
        <pre>ollama pull {model_name}</pre>
        
        <h4>使用命令提示符:</h4>
        <ol>
          <li>按下Win+R打开运行对话框</li>
          <li>输入"cmd"打开命令提示符</li>
          <li>输入以下命令并按Enter:</li>
        </ol>
        <pre>ollama pull {model_name}</pre>
        
        <p>注意：安装过程可能需要几分钟到几小时，取决于模型大小和您的网络速度。</p>
        <p>安装完成后，请在应用程序中点击"刷新模型列表"按钮。</p>
        """
        
        guide_label = QLabel(guide_text)
        guide_label.setTextFormat(Qt.RichText)
        guide_label.setWordWrap(True)
        layout.addWidget(guide_label)
        
        # 添加复制命令按钮
        copy_layout = QHBoxLayout()
        copy_label = QLabel("复制安装命令:")
        copy_btn = QPushButton("复制命令")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(f"ollama pull {model_name}"))
        copy_layout.addWidget(copy_label)
        copy_layout.addWidget(copy_btn)
        copy_layout.addStretch()
        layout.addLayout(copy_layout)
        
        # 添加关闭按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(guide_dialog.reject)
        layout.addWidget(button_box)
        
        guide_dialog.exec_()
    
    def refresh_after_model_install(self, dialog):
        """模型安装后刷新模型列表"""
        dialog.accept()  # 关闭对话框
        self.refresh_local_models()
        
    def refresh_local_models(self):
        """刷新本地已安装的模型列表"""
        try:
            import ollama
            self.local_models = ollama.list()['models']
            if hasattr(self.parent, 'update_model_list') and callable(self.parent.update_model_list):
                self.parent.update_model_list(self.local_models)
        except Exception as e:
            print(f"刷新模型列表时出错: {str(e)}")
