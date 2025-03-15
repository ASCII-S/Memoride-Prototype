import sys
# PyQt5相关导入
from PyQt5.QtWidgets import (
    QApplication
)

from core.logging import Logger
from core.error_handler import ErrorHandler
from ui.main_window import MainWindow

if __name__ == '__main__':
    # 初始化日志系统
    Logger.get_instance()
    Logger.info("应用程序启动")
    import resources
    # 安装全局异常处理器
    ErrorHandler.install_handler()
    
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        Logger.info("主窗口显示")
        sys.exit(app.exec_())
    except Exception as e:
        Logger.error(f"应用程序启动失败: {str(e)}")
        sys.exit(1)