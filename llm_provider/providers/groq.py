from typing import Dict, List, Optional, Any
import requests
from ..base_provider import BaseProvider
from ..types import ModelInfo

class GroqProvider(BaseProvider):
    def __init__(self):
        self.name = "Groq"
        self.get_api_key_link = "https://console.groq.com/keys"
        
        self.config = {
            "api_token_key": "GROQ_API_KEY"
        }
        
        self.static_models = [
            ModelInfo(name="llama-3.1-8b-instant", label="Llama 3.1 8b (Groq)", provider="Groq", max_token_allowed=8000),
            ModelInfo(name="llama-3.2-11b-vision-preview", label="Llama 3.2 11b (Groq)", provider="Groq", max_token_allowed=8000),
            ModelInfo(name="llama-3.2-90b-vision-preview", label="Llama 3.2 90b (Groq)", provider="Groq", max_token_allowed=8000),
            ModelInfo(name="llama-3.2-3b-preview", label="Llama 3.2 3b (Groq)", provider="Groq", max_token_allowed=8000),
            ModelInfo(name="llama-3.2-1b-preview", label="Llama 3.2 1b (Groq)", provider="Groq", max_token_allowed=8000),
            ModelInfo(name="llama-3.3-70b-versatile", label="Llama 3.3 70b (Groq)", provider="Groq", max_token_allowed=8000),
            ModelInfo(name="deepseek-r1-distill-llama-70b", label="Deepseek R1 Distill Llama 70b (Groq)", provider="Groq", max_token_allowed=131072),
        ]
    
    async def get_dynamic_models(
        self, 
        api_keys: Optional[Dict[str, str]] = None, 
        settings: Optional[Dict[str, Any]] = None, 
        server_env: Optional[Dict[str, str]] = None
    ) -> List[ModelInfo]:
        api_key_info = self.get_provider_base_url_and_key(
            api_keys=api_keys,
            provider_settings=settings,
            server_env=server_env,
            default_base_url_key="",
            default_api_token_key="GROQ_API_KEY"
        )
        
        api_key = api_key_info.get("api_key")
        
        if not api_key:
            raise ValueError(f"Missing Api Key configuration for {self.name} provider")
        
        response = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        res = response.json()
        
        data = [
            model for model in res.get("data", [])
            if model.get("object") == "model" and model.get("active") and model.get("context_window", 0) > 8000
        ]
        
        return [
            ModelInfo(
                name=model["id"],
                label=f"{model['id']} - context {str(model['context_window'] // 1000) + 'k' if model.get('context_window') else 'N/A'} [ by {model.get('owned_by', 'unknown')}]",
                provider=self.name,
                max_token_allowed=model.get("context_window", 8000)
            )
            for model in data
        ]
    
    def get_model_instance(self, options: Dict[str, Any]):
        model = options.get("model")
        server_env = options.get("server_env")
        api_keys = options.get("api_keys")
        provider_settings = options.get("provider_settings", {})
        
        api_key_info = self.get_provider_base_url_and_key(
            api_keys=api_keys,
            provider_settings=provider_settings.get(self.name),
            server_env=server_env,
            default_base_url_key="",
            default_api_token_key="GROQ_API_KEY"
        )
        
        api_key = api_key_info.get("api_key")
        
        if not api_key:
            raise ValueError(f"Missing API key for {self.name} provider")
        
        # This part would depend on your Python implementation's way of creating an OpenAI-like client
        # For example, using the openai Python package:
        from openai import OpenAI
        
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        
        return client.models.retrieve(model)
