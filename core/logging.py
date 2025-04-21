"""
应用程序日志系统模块
提供统一的日志记录功能，支持文件和控制台输出
"""

import os
import logging
import sys
import tempfile
from datetime import datetime

# 日志和错误处理类
class Logger:
    """应用程序日志记录类"""
    
    _instance = None
    _logger = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance
    
    def __init__(self):
        """初始化日志记录器"""
        if Logger._logger is not None:
            return
            
        # 创建日志目录 - 使用安全的用户目录
        try:
            # 首先尝试使用APPDATA环境变量(Windows)
            if 'APPDATA' in os.environ:
                log_dir = os.path.join(os.environ['APPDATA'], 'Memoride', 'logs')
            # 其次尝试使用用户主目录
            elif 'HOME' in os.environ:
                log_dir = os.path.join(os.environ['HOME'], '.memoride', 'logs')
            # 最后使用临时目录
            else:
                log_dir = os.path.join(tempfile.gettempdir(), 'memoride_logs')
                
            # 确保日志目录存在
            os.makedirs(log_dir, exist_ok=True)
            
            # 设置日志文件名
            log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
            
            # 创建并配置日志记录器
            logger = logging.getLogger('Memoride')
            logger.setLevel(logging.DEBUG)
            
            # 文件处理器 - 使用try-except确保即使文件创建失败也不会中断程序
            try:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                
                # 格式化器
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                
                # 添加处理器
                logger.addHandler(file_handler)
                
                # 记录日志路径
                print(f"日志文件路径: {log_file}")
            except (PermissionError, IOError) as e:
                # 如果无法创建日志文件，只使用控制台日志
                print(f"警告: 无法创建日志文件，将只使用控制台日志: {str(e)}")
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            Logger._logger = logger
            
        except Exception as e:
            # 创建基本的控制台日志，以便程序可以继续运行
            print(f"警告: 日志系统初始化失败: {str(e)}")
            logger = logging.getLogger('Memoride')
            logger.setLevel(logging.DEBUG)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            logger.addHandler(console_handler)
            Logger._logger = logger
    
    @staticmethod
    def info(message):
        """记录信息日志"""
        Logger.get_instance()._logger.info(message)
    
    @staticmethod
    def error(message, exc_info=True):
        """记录错误日志"""
        Logger.get_instance()._logger.error(message, exc_info=exc_info)
    
    @staticmethod
    def warning(message):
        """记录警告日志"""
        Logger.get_instance()._logger.warning(message)
    
    @staticmethod
    def debug(message):
        """记录调试日志"""
        Logger.get_instance()._logger.debug(message)
