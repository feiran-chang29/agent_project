import os
from typing import Optional
from openai import OpenAI
from hello_agents import HelloAgentsLLM
from dotenv import load_dotenv

BASE_PROMPT = "你是一个有用的AI助手。"

class MyLLM(HelloAgentsLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: Optional[str] = "ollama",
        **kwargs
    ):
        load_dotenv()
        if provider == "modelscope":
            print("正在使用自定义的 ModelScope Provider")
            self.provider = "modelscope"
            
            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY")
            self.base_url = base_url or "https://api-inference.modelscope.cn/v1/"
            
            if not self.api_key:
                raise ValueError("ModelScope API key not found. Please set MODELSCOPE_API_KEY environment variable.")

            self.model = model or os.getenv("LLM_MODEL_ID") or "Qwen/Qwen2.5-VL-72B-Instruct"
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens')
            self.timeout = kwargs.get('timeout', 60)
            self._client = self._create_client()
            
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
        elif provider == "ollama":
            print("正在使用自定义的 Ollama Provider")
            self.provider = "ollama"

            self.api_key = "Ollama"
            self.base_url = base_url or "http://localhost:11434/v1"
            self.model = model or os.getenv("LLM_MODEL_ID") or "llama3.2:3b"
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens')
            self.timeout = kwargs.get('timeout', 60)
            self._client = self._create_client()

        else:
            super().__init__(model=model, api_key=api_key, base_url=base_url, provider=provider, **kwargs)


