"""
Ollama服务管理模块
处理Ollama服务的启动、关闭和状态检查
"""

import platform
import subprocess
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import Qt, QApplication
from core import Config, Logger

class OllamaService:
    """Ollama服务管理类"""
    
    @staticmethod
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
    
    
    @staticmethod
    def _start_windows_service(dialog, status_label, button_box, progress):
        """启动Windows上的Ollama服务"""
        status_label.setText("在Windows上尝试启动Ollama服务...")
        QApplication.processEvents()
        
        try:
            # ...Windows服务启动逻辑...
            pass
        except Exception as e:
            # 处理异常
            pass
    
    @staticmethod
    def _start_macos_service(dialog, status_label, button_box, progress):
        """启动macOS上的Ollama服务"""
        # ...macOS服务启动逻辑...
        pass
    
    @staticmethod
    def _start_linux_service(dialog, status_label, button_box, progress):
        """启动Linux上的Ollama服务"""
        # ...Linux服务启动逻辑...
        pass
    
    @staticmethod
    def shutdown_service():
        """关闭Ollama服务"""
        try:
            Logger.info("正在关闭Ollama服务...")
            system = platform.system().lower()
            
            if system == "windows":
                # Windows系统使用taskkill命令关闭ollama进程
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
            
            Logger.info("Ollama服务已关闭")
            return True
        except Exception as e:
            Logger.error(f"关闭Ollama服务时出错: {str(e)}")
            return False