from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import os

class FileDropZone(QWidget):
    files_dropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.files = []
        self.init_ui()
        
    def init_ui(self):
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加提示标签
        self.label = QLabel('拖放文件到这里')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #666;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                background: rgba(0, 0, 0, 0.02);
            }
        """)
        
        # 添加文件列表显示区域
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: transparent;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background: rgba(33, 150, 243, 0.1);
            }
        """)
        self.file_list.setMinimumHeight(150)
        self.file_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 将两个组件添加到布局中，它们会重叠显示
        layout.addWidget(self.label)
        layout.addWidget(self.file_list)
        
        # 初始时隐藏文件列表
        self.file_list.hide()
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet("""
                QLabel {
                    color: #2196F3;
                    border: 2px dashed #2196F3;
                    border-radius: 8px;
                    padding: 20px;
                    background: rgba(33, 150, 243, 0.1);
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("""
            QLabel {
                color: #666;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                background: rgba(0, 0, 0, 0.02);
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_files(files)
        self.files_dropped.emit(files)
        self.label.setStyleSheet("""
            QLabel {
                color: #666;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                background: rgba(0, 0, 0, 0.02);
            }
        """)
    
    def add_files(self, files):
        """添加文件到列表中"""
        # 追加新文件并去重
        existing_files = set(self.files)
        new_files = [f for f in files if f not in existing_files]
        self.files += new_files
        self.update_file_list()
    
    def get_files(self):
        """获取当前文件列表"""
        return self.files
    
    def remove_file(self, file):
        """从列表中移除文件"""
        if file in self.files:
            self.files.remove(file)
            self.update_file_list()
    
    def update_file_list(self):
        """更新文件列表显示"""
        self.file_list.clear()
        
        if self.files:
            # 如果有文件，显示文件列表并隐藏提示标签
            self.label.hide()
            self.file_list.show()
            
            for file in self.files:
                item = QListWidgetItem()
                item_widget = QWidget()
                layout = QHBoxLayout(item_widget)
                layout.setContentsMargins(0, 0, 0, 0)
                
                # 文件名和路径标签
                file_label = QLabel(f"<b>{os.path.basename(file)}</b><br><span style='color:#666;font-size:11px;'>{file}</span>")
                file_label.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        border-bottom: 1px solid #eee;
                    }
                """)
                file_label.setTextFormat(Qt.RichText)
                layout.addWidget(file_label, 1)
                
                # 删除按钮
                delete_btn = QPushButton('×')
                delete_btn.setStyleSheet("""
                    QPushButton {
                        color: #f44336;
                        font: bold 18px;
                        border: none;
                        min-width: 32px;
                        max-width: 32px;
                        padding: 0;
                    }
                    QPushButton:hover {
                        background: rgba(244,67,54,0.1);
                    }
                """)
                delete_btn.clicked.connect(lambda checked, f=file: self.remove_file(f))
                layout.addWidget(delete_btn)
                
                item_widget.setLayout(layout)
                item.setSizeHint(item_widget.sizeHint())
                self.file_list.addItem(item)
                self.file_list.setItemWidget(item, item_widget)
        else:
            # 如果没有文件，显示提示标签并隐藏文件列表
            self.label.show()
            self.file_list.hide()
    
    def clear_files(self):
        """清空文件列表"""
        self.files = []
        self.update_file_list()