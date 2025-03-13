import requests
import json
from typing import Optional, Dict
from config import Config, OLLAMA_API_URL
import ollama
from ollama import Client, AsyncClient

class APIHandler:
    """API处理器基类，为不同类型的API处理器提供共同的接口"""
    def generate_completion(self, model: str, prompt: str, stream: bool = False, 
                           format: Optional[Dict] = None, options: Optional[Dict] = None) -> Dict:
        """生成文本补全"""
        raise NotImplementedError("子类需要实现此方法")
    
    def list_models(self) -> Dict:
        """列出可用模型"""
        raise NotImplementedError("子类需要实现此方法")

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

class RemoteAPIHandler(APIHandler):
    """远程API处理器，用于处理远程模型API调用"""
    def __init__(self):
        self.api_url = Config.REMOTE_API_URL.rstrip('/')  # 移除末尾的斜杠，确保URL格式一致
        self.api_key = Config.REMOTE_API_KEY
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
    
    def generate_completion(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        format: Optional[Dict] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """生成文本补全，远程API实现"""
        # 根据常见API格式调整请求结构
        try:
            # 检测API类型并调整请求格式
            api_url_lower = self.api_url.lower()
            
            if "deepseek.com" in api_url_lower or "openai" in api_url_lower:
                # DeepSeek API 或 OpenAI兼容格式使用chat completions接口
                # 解析历史消息 - 如果prompt是字符串，将其转换为单一用户消息
                messages = []
                
                if isinstance(prompt, str):
                    messages = [{"role": "user", "content": prompt}]
                elif isinstance(prompt, list):
                    # 如果prompt已经是消息列表格式，直接使用
                    messages = prompt
                
                # 针对DeepSeek API的特殊处理
                if "deepseek.com" in api_url_lower:
                    # 确保使用的是正确的模型名称
                    if model in Config.REMOTE_API_MODELS:
                        actual_model = model  # 使用配置中指定的模型
                    else:
                        # 如果提供的模型名称不在配置列表中，使用第一个可用的模型
                        actual_model = Config.REMOTE_API_MODELS[0] if Config.REMOTE_API_MODELS else "deepseek-chat"
                        print(f"警告: 模型 '{model}' 不在配置的模型列表中，使用 '{actual_model}' 代替")
                else:
                    actual_model = model
                
                chat_payload = {
                    "model": actual_model,
                    "messages": messages,
                    "stream": stream
                }
                
                # 添加其他选项
                if options:
                    for key, value in options.items():
                        if key not in chat_payload and key not in ["prompt"]:
                            chat_payload[key] = value
                
                # 特别处理response_format参数，用于DeepSeek的JSON输出功能
                if options and "response_format" in options:
                    chat_payload["response_format"] = options["response_format"]
                    print(f"启用JSON输出功能，response_format: {options['response_format']}")
                
                print(f"使用OpenAI兼容接口调用: /v1/chat/completions")
                print(f"模型: {actual_model}, API URL: {self.api_url}")
                print(f"API密钥长度: {len(self.api_key) if self.api_key else 0}字符")
                
                # 检查API密钥是否为空
                if not self.api_key:
                    return {
                        "error": "API密钥为空，请在远程API配置中设置有效的API密钥"
                    }
                
                return self._post_request("/v1/chat/completions", chat_payload)
            else:
                # 构建基本请求负载
                payload = {
                    "model": model,
                    "prompt": prompt
                }
                
                # 根据是否流式传输增加参数
                if stream is not None:
                    payload["stream"] = stream
                    
                # 如果有格式要求
                if format:
                    payload["format"] = format
                    
                # 合并任何额外选项
                if options:
                    # 不直接使用update()以避免覆盖已有键
                    for key, value in options.items():
                        if key not in payload:
                            payload[key] = value
                
                # 默认格式，假设是通用的completions端点
                print(f"使用默认接口调用: /generate")
                return self._post_request("/generate", payload)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"远程API请求异常详细信息: {error_trace}")
            return {
                "error": f"远程API请求失败: {str(e)}"
            }
        
    def list_models(self) -> Dict:
        """列出远程API可用的模型"""
        # 如果配置中有预设模型列表，直接返回
        if Config.REMOTE_API_MODELS:
            return {"models": [{"name": model} for model in Config.REMOTE_API_MODELS]}
        
        # 尝试从API获取 - 根据常见API格式调整
        api_url_lower = self.api_url.lower()
        if "deepseek.com" in api_url_lower or "openai" in api_url_lower:
            print("尝试从OpenAI兼容API获取模型列表: /v1/models")
            response = self._get_request("/v1/models")
            
            # 处理OpenAI格式的响应
            if "data" in response and isinstance(response["data"], list):
                # 转换为标准格式
                models = [{"name": model.get("id")} for model in response["data"] if model.get("id")]
                return {"models": models}
            return response
        else:
            # 默认尝试通用模型列表端点
            print("尝试从默认API获取模型列表: /models")
            return self._get_request("/models")
    
    def list_local_models(self) -> Dict:
        """列出本地模型（远程API模式下返回空列表）"""
        print("RemoteAPIHandler.list_local_models: 远程API模式不支持本地模型，返回空列表")
        return {"models": []}

    def _get_request(self, endpoint: str) -> Dict:
        """发送GET请求到远程API"""
        try:
            # 确保endpoint以/开头
            if not endpoint.startswith("/"):
                endpoint = f"/{endpoint}"
                
            url = f"{self.api_url}{endpoint}"
            print(f"发送GET请求到: {url}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            # 尝试处理响应
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {
                        "error": "远程API返回了非JSON响应",
                        "response": response.text
                    }
            else:
                response.raise_for_status()  # 触发HTTPError异常
                
        except requests.exceptions.HTTPError as e:
            return {
                "error": f"远程API HTTP错误: {str(e)}",
                "status_code": response.status_code if 'response' in locals() else None,
                "response": response.text if 'response' in locals() else None
            }
        except Exception as e:
            return {
                "error": f"远程API请求异常: {str(e)}"
            }
    
    def _post_request(self, endpoint: str, payload: Dict) -> Dict:
        """发送POST请求到远程API"""
        try:
            # 确保endpoint以/开头
            if not endpoint.startswith("/"):
                endpoint = f"/{endpoint}"
                
            url = f"{self.api_url}{endpoint}"
            print(f"发送POST请求到: {url}")
            print(f"请求负载: {json.dumps(payload, ensure_ascii=False)}")
            
            timeout = Config.REQUEST_TIMEOUT * 2  # 生成请求允许更长的超时时间
            
            # 检查是否是流式请求
            is_stream = payload.get('stream', False)
            is_openai_compatible = "deepseek.com" in self.api_url.lower() or "openai" in self.api_url.lower()
            
            # 处理流式请求
            if is_stream:
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=timeout
                )
                
                # 检查响应状态
                if response.status_code == 200:
                    # 返回一个生成器
                    return handle_stream_response(response, is_openai_compatible=is_openai_compatible)
                else:
                    # 如果响应不成功，输出详细信息
                    print(f"请求失败 - 状态码: {response.status_code}")
                    print(f"响应内容: {response.text}")
                    print(f"请求头: {self.headers}")
                    # 隐藏API密钥
                    safe_headers = self.headers.copy()
                    if 'Authorization' in safe_headers:
                        safe_headers['Authorization'] = 'Bearer ****'
                    print(f"发送的请求头: {safe_headers}")
                    
                    response.raise_for_status()  # 触发HTTPError异常
            
            # 非流式请求的处理
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            # 尝试处理响应
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print(f"响应不是有效的JSON格式: {response.text}")
                    return {
                        "error": "远程API返回了非JSON响应",
                        "response": response.text
                    }
            else:
                # 如果响应不成功，输出详细信息
                print(f"请求失败 - 状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
                # 隐藏API密钥
                safe_headers = self.headers.copy()
                if 'Authorization' in safe_headers:
                    safe_headers['Authorization'] = 'Bearer ****'
                print(f"发送的请求头: {safe_headers}")
                
                response.raise_for_status()  # 触发HTTPError异常
                
        except requests.exceptions.HTTPError as e:
            error_msg = f"远程API HTTP错误: {str(e)}"
            print(f"HTTP错误详情: {error_msg}")
            
            if 'response' in locals():
                print(f"状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
                # 尝试解析JSON响应（如果有）
                try:
                    error_json = response.json()
                    print(f"错误JSON: {json.dumps(error_json, ensure_ascii=False)}")
                except:
                    pass
                    
            return {
                "error": error_msg,
                "status_code": response.status_code if 'response' in locals() else None,
                "response": response.text if 'response' in locals() else None
            }
        except Exception as e:
            import traceback
            print(f"远程API请求异常: {str(e)}")
            print(f"异常堆栈: {traceback.format_exc()}")
            return {
                "error": f"远程API请求异常: {str(e)}"
            }

def get_api_handler():
    """根据配置选择合适的API处理器"""
    if Config.MODEL_SOURCE == 'Ollama本地模型':
        return OllamaAPIHandler()
    else:
        return RemoteAPIHandler()

# 流式响应处理函数
def handle_stream_response(response, is_openai_compatible=False):
    """处理流式响应，支持Ollama原生格式和OpenAI兼容格式(DeepSeek等)
    
    Args:
        response: requests的响应对象
        is_openai_compatible: 是否为OpenAI兼容格式(DeepSeek等)
    
    Yields:
        解析后的响应数据字典
    """
    for line in response.iter_lines():
        if not line:
            continue
            
        decoded = line.decode('utf-8')
        
        # 处理OpenAI兼容格式的SSE流
        if is_openai_compatible:
            if decoded.startswith('data: '):
                data_str = decoded[6:]
                
                # 处理 [DONE] 结束标记
                if data_str.strip() == '[DONE]':
                    yield {"done": True}
                    continue
                    
                try:
                    data = json.loads(data_str)
                    
                    # 提取OpenAI格式的输出内容
                    if 'choices' in data and len(data['choices']) > 0:
                        choice = data['choices'][0]
                        
                        if 'delta' in choice and 'content' in choice['delta']:
                            # 构造与Ollama格式类似的响应
                            yield {
                                "response": choice['delta']['content'],
                                "model": data.get("model", "unknown"),
                                "created_at": data.get("created", ""),
                                "done": choice.get("finish_reason") is not None
                            }
                        elif 'finish_reason' in choice and choice['finish_reason']:
                            # 流结束的标记
                            yield {"done": True}
                        # 处理DeepSeek/OpenAI非流式响应格式
                        elif 'message' in choice and 'content' in choice['message']:
                            yield {
                                "response": choice['message']['content'],
                                "model": data.get("model", "unknown"),
                                "created_at": data.get("created", ""),
                                "done": True
                            }
                            
                except json.JSONDecodeError as e:
                    yield {"error": f"无效的JSON响应: {e}, 原始内容: {data_str}"}
        
        # 处理Ollama原生格式
        else:
            if decoded.startswith('data: '):
                try:
                    data = json.loads(decoded[6:])
                    yield data
                except json.JSONDecodeError as e:
                    yield {"error": f"无效的JSON响应: {e}, 原始内容: {decoded[6:]}"}
            else:
                # 尝试直接解析整行
                try:
                    data = json.loads(decoded)
                    yield data
                except json.JSONDecodeError:
                    # 如果不是JSON，则返回原始文本
                    yield {"response": decoded, "done": False}