"""
应用程序错误处理模块
提供全局异常捕获和错误显示功能
"""

import sys
import traceback
from PyQt5.QtWidgets import QMessageBox, QApplication

from core.logging import Logger

class ErrorHandler:
    """应用程序错误处理类"""
    
    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常调用栈
        """
        # 将异常记录到日志
        Logger.error(f"未捕获的异常: {exc_value}", exc_info=(exc_type, exc_value, exc_traceback))
        
        # 显示错误对话框（如果应用程序还在运行）
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "应用程序错误",
                                  f"发生了未处理的错误：\n{exc_value}\n\n详细信息已记录到日志文件。")
        except Exception:
            # 如果无法显示UI，至少打印到控制台
            print(f"严重错误: {exc_value}\n{traceback.format_tb(exc_traceback)}")
    
    @staticmethod
    def install_handler():
        """安装全局异常处理器
        
        将系统的默认异常处理器替换为自定义处理器
        """
        Logger.info("安装全局异常处理器")
        sys.excepthook = ErrorHandler.handle_exception
    
    @staticmethod
    def show_error_dialog(parent, title, message):
        """显示错误对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 错误信息
        """
        Logger.error(f"显示错误: {title} - {message}")
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_warning_dialog(parent, title, message):
        """显示警告对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 警告信息
        """
        Logger.warning(f"显示警告: {title} - {message}")
        QMessageBox.warning(parent, title, message)