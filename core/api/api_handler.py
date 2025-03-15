from typing import Dict, Optional

class APIHandler:
    """API处理器基类，为不同类型的API处理器提供共同的接口"""
    def generate_completion(self, model: str, prompt: str, stream: bool = False, 
                           format: Optional[Dict] = None, options: Optional[Dict] = None) -> Dict:
        """生成文本补全"""
        raise NotImplementedError("子类需要实现此方法")
    
    def list_models(self) -> Dict:
        """列出可用模型"""
        raise NotImplementedError("子类需要实现此方法")
