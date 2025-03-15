from PyQt5.QtWidgets import (
    QPushButton, QComboBox, QLabel, QFrame,
    QHBoxLayout, QVBoxLayout
)

# UI辅助类
class UIHelper:
    """UI组件创建和样式设置的辅助类"""
    
    @staticmethod
    def create_styled_button(text, on_click=None, color="#3498db", hover_color="#2980b9", pressed_color="#1f6aa5"):
        """创建一个带样式的按钮"""
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """)
        
        if on_click:
            button.clicked.connect(on_click)
            
        return button
    
    @staticmethod
    def create_styled_combo_box(items=None):
        """创建一个带样式的下拉框"""
        combo = QComboBox()
        combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 150px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #999;
            }
            QComboBox:focus {
                border-color: #3498db;
                border-width: 2px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: none;
            }
        """)
        if items:
            combo.addItems(items)
        return combo
    
    @staticmethod
    def create_styled_label(text, is_title=False, color="#333"):
        """创建一个带样式的标签"""
        label = QLabel(text)
        font_weight = "bold" if is_title else "normal"
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: {font_weight};
                padding: 2px 4px;
            }}
        """)
        return label
    
    @staticmethod
    def create_styled_frame(horizontal=True):
        """创建一个带样式的框架"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        
        # 根据方向设置布局
        if horizontal:
            layout = QHBoxLayout(frame)
        else:
            layout = QVBoxLayout(frame)
            
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        return frame, layout