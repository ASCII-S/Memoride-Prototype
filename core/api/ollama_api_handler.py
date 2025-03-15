from core.api.api_handler import APIHandler
from ollama import Client
from core.config import OLLAMA_API_URL
from typing import Dict, Optional


class OllamaAPIHandler(APIHandler):
    def __init__(self):
        self.client = Client(host=OLLAMA_API_URL)
        self.headers = {'Content-Type': 'application/json'}
        self.current_request = None  # 用于跟踪当前的生成请求

    def generate_completion(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        format: Optional[Dict] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        生成文本补全
        使用ollama-sdk的generate方法
        """
        try:
            # 处理消息列表格式
            if isinstance(prompt, list):
                # 将消息列表转换为字符串格式
                formatted_prompt = ""
                for msg in prompt:
                    if isinstance(msg, dict):
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        if role and content:
                            formatted_prompt += f"{role}: {content}\n"
                    elif isinstance(msg, str):
                        formatted_prompt += f"{msg}\n"
                prompt = formatted_prompt.strip()

            # 保存当前请求
            self.current_request = self.client.generate(
                model=model,
                prompt=prompt,
                stream=stream,
                format=format,
                options=options
            )
            
            # 直接返回响应中的有效内容
            if hasattr(self.current_request, 'response'):
                # 过滤掉<think>标签内的内容
                import re
                filtered_response = re.sub(r'<think>.*?</think>', '', self.current_request.response, flags=re.DOTALL).strip()
                
                return {
                    "response": filtered_response,
                    "model": self.current_request.model,
                    "created_at": self.current_request.created_at,
                    "done": self.current_request.done,
                    "done_reason": self.current_request.done_reason if hasattr(self.current_request, 'done_reason') else None
                }
            return self.current_request
        except Exception as e:
            return {
                "error": f"生成补全失败: {str(e)}"
            }
        finally:
            # 清除当前请求
            self.current_request = None

    def cancel_generation(self):
        """
        取消当前的生成请求
        """
        try:
            if self.current_request:
                # 如果请求有cancel方法，调用它
                if hasattr(self.current_request, 'cancel'):
                    self.current_request.cancel()
                # 清除当前请求
                self.current_request = None
        except Exception as e:
            print(f"取消生成请求时出错: {str(e)}")



    def list_models(self) -> Dict:
        """列出可用模型，使用list_local_models的实现"""
        return self.list_local_models()

    def chat_completion(
        self,
        model: str,
        messages: list,
        stream: bool = False,
        format: Optional[Dict] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        聊天补全实现
        使用ollama-sdk的chat方法
        """
        try:
            response = self.client.chat(
                model=model,
                messages=messages,
                stream=stream,
                format=format,
                options=options
            )
            return response
        except Exception as e:
            return {
                "error": f"聊天补全失败: {str(e)}"
            }

    def create_model(
        self,
        model: str,
        modelfile: str,
        stream: bool = False
    ) -> Dict:
        """
        创建新模型
        使用ollama-sdk的create方法
        """
        try:
            response = self.client.create(
                model=model,
                modelfile=modelfile,
                stream=stream
            )
            return response
        except Exception as e:
            return {
                "error": f"创建模型失败: {str(e)}"
            }

    def list_local_models(self) -> Dict:
        """
        列出本地模型
        使用ollama-sdk的list方法
        """
        try:
            response = self.client.list()
            # 转换为原有的返回格式
            return {
                "models": [
                    {
                        "name": model.model,
                        "size": f"{(model.size.real / 1024 / 1024):.2f}MB",
                        "details": {
                            "format": model.details.format if model.details else None,
                            "family": model.details.family if model.details else None,
                            "parameter_size": model.details.parameter_size if model.details else None,
                            "quantization_level": model.details.quantization_level if model.details else None
                        } if model.details else None
                    }
                    for model in response.models
                ]
            }
        except Exception as e:
            return {
                "error": f"获取模型列表失败: {str(e)}"
            }

    def show_model_info(self, model: str) -> Dict:
        """
        显示模型详细信息
        使用ollama-sdk的show方法
        """
        try:
            return self.client.show(model)
        except Exception as e:
            return {
                "error": f"获取模型信息失败: {str(e)}"
            }

    def delete_model(self, model: str) -> Dict:
        """
        删除模型
        使用ollama-sdk的delete方法
        """
        try:
            return self.client.delete(model)
        except Exception as e:
            return {
                "error": f"删除模型失败: {str(e)}"
            }

    def copy_model(self, source: str, destination: str) -> Dict:
        """
        复制模型
        使用ollama-sdk的copy方法
        """
        try:
            return self.client.copy(source, destination)
        except Exception as e:
            return {
                "error": f"复制模型失败: {str(e)}"
            }
