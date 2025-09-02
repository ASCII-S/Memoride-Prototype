# Memoride (记忆之旅)

一个基于PyQt5的大语言模型交互应用，支持本地和远程API模型的使用和管理。

## 项目简介

Memoride是一个桌面应用程序，旨在为用户提供一个友好的界面来与大语言模型进行交互。无论是本地托管的Ollama模型还是远程API模型，Memoride都能为您提供一个统一的使用体验。

## 主要功能

- **多模型支持**：支持本地Ollama模型和远程API模型
- **模型管理**：便捷的模型安装、选择和配置界面
- **智能交互**：用户友好的对话界面
- **配置管理**：灵活的API配置和模型参数设置
- **日志系统**：完整的日志记录，便于问题排查

## 程序截图
<img width="916" height="702" alt="image" src="https://github.com/user-attachments/assets/20dce47a-4572-41c6-bb8a-0b64d6888c59" />

<img width="916" height="702" alt="image" src="https://github.com/user-attachments/assets/397ac77f-2ad0-43f2-baa7-4bcff56a2bfa" />

<img width="916" height="702" alt="image" src="https://github.com/user-attachments/assets/4ed9df14-69a0-4636-b3e0-c8b1a317dfb9" />


## 系统要求

- 操作系统：Windows/macOS/Linux
- Python 3.7+
- PyQt5
- 如需使用本地模型，需安装Ollama

## 安装说明

1. 克隆本仓库：
```bash
git clone https://github.com/yourusername/memoride.git
cd memoride
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行应用：
```bash
python main.py
```

## 使用指南

### 基本使用

1. 启动应用后，选择您希望使用的模型来源（本地Ollama模型或远程API模型）
2. 选择具体的模型或API配置
3. 在交互界面中输入您的问题或指令，开始与模型对话

### Ollama本地模型

如果您选择使用本地Ollama模型，应用会检查Ollama服务是否正在运行。如果没有运行，会提供指导帮助您安装和启动Ollama服务。

### 远程API模型

使用远程API模型时，您需要配置相应的API密钥和服务地址。应用提供了便捷的API配置管理界面。

## 项目结构

- `core/`: 核心功能模块，包含配置管理、日志、API交互等
- `ui/`: 用户界面相关代码
- `resources/`: 应用资源文件
- `system_prompts/`: 系统提示词模板
- `output_cards/`: 输出内容的保存目录

## 开发者指南

### 添加新功能

1. 遵循项目现有的模块化结构
2. 核心功能应当放在`core/`目录下
3. UI相关代码放在`ui/`目录下
4. 确保所有功能都有适当的错误处理和日志记录

### 贡献指南

欢迎提交PR和问题报告。在提交代码前，请确保：

1. 代码符合项目的代码风格
2. 所有新功能都有相应的测试
3. 文档已更新

## 许可证

[在此添加您的许可证信息]

## 联系方式

[在此添加您的联系方式] 
