from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain_community.llms import Ollama

class BaseAgent(ABC):
    def __init__(self, model_name: str = "mistral:latest"):
        self.llm = Ollama(
            model=model_name,
            num_ctx=2048,
            temperature=0.1
        )
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data and return results"""
        pass
    
    def invoke_llm(self, prompt: str) -> str:
        """Invoke LLM with prompt"""
        return self.llm.invoke(prompt)