"""
支持与帮助标签页模块
显示软件使用方法、用途及支持作者的内容
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from ui.tabs.base import BaseTab

class SupportTab(BaseTab):
    def __init__(self, api_handler):
        super().__init__(api_handler)
        import resources
        
    def init_ui(self):
        # 调用父类的init_ui以设置基本布局
        super().init_ui()
        
        # 创建一个滚动区域以容纳所有内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # 创建容器部件和布局
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # 添加标题
        title_label = QLabel("心动记忆 - 帮助与支持")
        title_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        content_layout.addWidget(title_label)
        
        
        # 定义一个统一的QGroupBox样式，统一支持作者和软件用途说明
        group_box_style = """
            QGroupBox {
                margin-top: 30px; 
                padding-top: 15px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                font-size: 18px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
        """
        # 添加支持作者区域
        support_group = QGroupBox("支持作者 ✧(๑•̀ㅂ•́)و")
        support_group.setStyleSheet(group_box_style)
        support_layout = QVBoxLayout()

        support_text = QLabel(
            "<h3>如果您觉得本软件对您有帮助，可以通过以下方式支持作者：</h3>"
            "<p>您的支持是我持续改进软件的动力！(＾▽＾)</p>"
            #添加联系邮箱
            "<p>如有建议与诉求，请联系QQ/邮箱：<a href='mailto:1600014464@qq.com'>1600014464@qq.com</a></p>"
        )
        support_text.setTextFormat(Qt.RichText)
        support_text.setWordWrap(True)
        support_layout.addWidget(support_text)
        
        # 创建收款码展示区域
        qr_container = QWidget()
        qr_layout = QHBoxLayout(qr_container)
        
        # 微信收款码
        wechat_group = QWidget()
        wechat_layout = QVBoxLayout(wechat_group)
        wechat_label = QLabel("☕️请开发者喝杯咖啡 (￣▽￣)")
        wechat_label.setAlignment(Qt.AlignCenter)
        wechat_label.setFont(QFont("", 12, QFont.Bold))
        
        # 从资源加载微信收款码图片
        wechat_qr = QLabel()
        wechat_qr_pixmap = QPixmap(":/images/wechat_qr.png")
        if wechat_qr_pixmap.isNull():
            wechat_qr.setText("微信收款码图片未找到")
        else:
            wechat_qr_pixmap = wechat_qr_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            wechat_qr.setPixmap(wechat_qr_pixmap)
            wechat_qr.setAlignment(Qt.AlignCenter)
        
        wechat_layout.addWidget(wechat_label)
        wechat_layout.addWidget(wechat_qr)
        
        # 支付宝收款码
        alipay_group = QWidget()
        alipay_layout = QVBoxLayout(alipay_group)
        alipay_label = QLabel("🔋1份支持 = 10小时开发电量")
        alipay_label.setAlignment(Qt.AlignCenter)
        alipay_label.setFont(QFont("", 12, QFont.Bold))
        
        # 从资源加载支付宝收款码图片
        alipay_qr = QLabel()
        alipay_qr_pixmap = QPixmap(":/images/alipay_qr.png")
        if alipay_qr_pixmap.isNull():
            alipay_qr.setText("支付宝收款码图片未找到")
        else:
            alipay_qr_pixmap = alipay_qr_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            alipay_qr.setPixmap(alipay_qr_pixmap)
            alipay_qr.setAlignment(Qt.AlignCenter)
        
        alipay_layout.addWidget(alipay_label)
        alipay_layout.addWidget(alipay_qr)
        
        # 添加收款码到水平布局
        qr_layout.addWidget(wechat_group)
        qr_layout.addWidget(alipay_group)
        
        # 添加收款码容器到支持布局
        support_layout.addWidget(qr_container)
        
        # 添加提示信息
        # note_label = QLabel("注：请确保在resources目录中添加wechat_qr.png和alipay_qr.png收款码图片")
        # note_label.setStyleSheet("color: gray; font-style: italic;")
        # support_layout.addWidget(note_label)
        
        support_group.setLayout(support_layout)
        content_layout.addWidget(support_group)
        
        # 添加帮助信息区域 (现在放在下面)
        help_group = QGroupBox("软件使用指南 (๑╹◡╹)ﾉ")
        help_group.setStyleSheet(group_box_style)
        help_layout = QVBoxLayout()
        
        # 软件用途说明
        purpose_label = QLabel(
            "<h3>软件用途</h3>"
            "<p>心动记忆是一款本地LLM应用工具，主要功能包括：</p>"
            "<ul>"
            "<li>文件处理：针对上传知识内容，以不同风格生成对话式学习卡片，助你在不知不觉中记忆知识点</li>"
            "<li>智能对话：与本地或远程AI模型对话</li>"
            "<li>灵活选择AI模型：支持本地Ollama模型和远程API模型</li>"
            "</ul>"
        )
        purpose_label.setTextFormat(Qt.RichText)
        purpose_label.setWordWrap(True)
        help_layout.addWidget(purpose_label)
        
        # 使用方法说明
        usage_label = QLabel(
            "<h3>使用方法</h3>"
            "<h4>模型来源选择</h4>"
            "<p>在顶部可以选择使用Ollama本地模型或远程API模型：</p>"
            "<ul>"
            "<li><b>Ollama本地模型</b>：</li>"
            "<li>不花钱。但是需要先安装Ollama并下载相关模型,并且需要高性能配置(大显存,大内存)支持,且运行缓慢。建议夜间使用 (￣ω￣)</li>"
            "<li><b>远程API模型</b>：</li>"
            "<li>花点小钱。但是速度快，且流畅。建议使用deepseek模型api（便宜）</li>"
            "</ul>"
            "<h4>文件处理 </h4>"
            "<p>1. 选择文件 → 2. 选择问答风格 → 3. 选择处理方式 → 4. 点击处理按钮</p>"
            "<h4>对话功能</h4>"
            "<p>1. 输入问题 → 2. 点击发送 → 3. 等待AI回答</p>"
        )
        usage_label.setTextFormat(Qt.RichText)
        usage_label.setWordWrap(True)
        help_layout.addWidget(usage_label)
        
        help_group.setLayout(help_layout)
        content_layout.addWidget(help_group)
        
        # 设置滚动区域的部件
        scroll_area.setWidget(content_widget)
        
        # 将滚动区域添加到主布局
        self.layout.addWidget(scroll_area)
        
    def cleanup_resources(self):
        """清理标签页资源的方法，在主窗口关闭时会被调用"""
        print("支持与帮助标签页资源已清理")