"""
API 工具模块
提供API处理所需的通用工具函数
"""

import json

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