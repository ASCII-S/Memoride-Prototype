"""
模型管理模块
处理模型的安装、管理和使用
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout, 
    QLineEdit, QProgressBar, QCheckBox, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
import platform
import subprocess
import os
from core import Config, Logger

class ModelManager:
    """模型管理类，处理模型的安装和管理"""
    
    def __init__(self, parent_window):
        """
        初始化模型管理器
        
        Args:
            parent_window: 父窗口，用于显示对话框
        """
        self.parent = parent_window
    
    def install_model(self):
        """提供Ollama模型安装指导"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("安装Ollama模型")
        dialog.setMinimumWidth(500)
        
        # ... 安装模型对话框的UI代码 ...
        
    def show_manual_install_guide(self, model_name):
        """
        显示手动安装模型的指南
        
        Args:
            model_name: 要安装的模型名称
        """
        guide_dialog = QDialog(self.parent)
        guide_dialog.setWindowTitle("手动安装Ollama模型指南")
        
        # ... 手动安装指南的UI代码 ...
    
    def install_ollama(self):
        """提供Ollama安装指导"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("安装Ollama")
        
        # ... Ollama安装指南的UI代码 ...
    
    def show_manual_windows_start_guide(self):
        """显示Windows手动启动Ollama的指南"""
        guide_dialog = QDialog(self.parent)
        guide_dialog.setWindowTitle("Windows手动启动Ollama指南")
        
        # ... Windows启动指南的UI代码 ...