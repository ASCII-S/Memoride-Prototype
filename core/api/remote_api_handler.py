"""
远程API处理模块
处理与远程API服务的通信
"""

from core.api.api_handler import APIHandler
from core.config import Config
from typing import Dict, Optional
import requests
import json
from core.api.utils import handle_stream_response 

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
