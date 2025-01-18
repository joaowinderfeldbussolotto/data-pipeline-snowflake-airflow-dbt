from abc import ABC, abstractmethod
from typing import Optional, Set, Dict, Any
from dataclasses import dataclass
import requests
from config import settings
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

@dataclass(frozen=True)
class LLMModel:
    id: str
    name: str
    context_length: int

class LLMProvider(ABC):
    @abstractmethod
    def create(self, model: Optional[str], temperature: float, max_retries: int):
        pass
    
    @abstractmethod
    def list_models(self) -> Set[LLMModel]:
        pass
    
    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if the provider supports function/tool calling."""
        pass

class MistralProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.mistral_api_key
        self.api_url = "https://api.mistral.ai/v1/models"
    
    def create(self, model: Optional[str] = None, temperature: float = 0, max_retries: int = 4):
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model=model or "codestral-latest",
            temperature=temperature,
            max_retries=max_retries,
            api_key=self.api_key
        )
    
    def list_models(self) -> Set[LLMModel]:
        response = requests.get(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        models = response.json()["data"]
        return {
            LLMModel(
                id=model['id'],
                name=model['name'],
                context_length=model['max_context_length']
            )
            for model in models
            if model.get('capabilities', {}).get('completion_chat')
            and model.get('capabilities', {}).get('function_calling')
        }
    
    def supports_tools(self) -> bool:
        return True

class GroqProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.api_url = "https://api.groq.com/openai/v1/models"
    
    def create(self, model: Optional[str] = None, temperature: float = 0, max_retries: int = 4):
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model or "llama-3.1-70b-versatile",
            temperature=temperature,
            max_retries=max_retries,
            api_key=self.api_key
        )
    
    def list_models(self) -> Set[LLMModel]:
        response = requests.get(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        models = response.json()["data"]
        return {
            LLMModel(
                id=model['id'],
                name=model['id'],
                context_length=model['context_window']
            )
            for model in models
            if model.get('active')
            and not 'whisper' in model['id'].lower()
        }
    
    def supports_tools(self) -> bool:
        return True


class LLMFactory:
    _providers = {
        "mistral": MistralProvider,
        "groq": GroqProvider,
    }

    @classmethod
    def create(cls, provider: str, **kwargs) -> Any:
        provider = provider.lower()
        if provider not in cls._providers:
            raise ValueError(f"Provider {provider} not supported. Use {', '.join(cls._providers.keys())}")
        
        provider_instance = cls._providers[provider]()
        if not provider_instance.supports_tools():
            raise ValueError(f"Provider {provider} does not support tool/function calling")
        
        return provider_instance.create(**kwargs)
    
    @classmethod
    def list_models(cls, provider: str) -> Set[LLMModel]:
        provider = provider.lower()
        if provider not in cls._providers:
            raise ValueError(f"Provider {provider} not supported. Use {', '.join(cls._providers.keys())}")
        return cls._providers[provider]().list_models()
    
    @classmethod
    def get_provider_instance(cls, provider: str) -> LLMProvider:
        provider = provider.lower()
        if provider not in cls._providers:
            raise ValueError(f"Provider {provider} not supported. Use {', '.join(cls._providers.keys())}")
        return cls._providers[provider]()


