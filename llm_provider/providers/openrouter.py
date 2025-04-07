from typing import Dict, List, Optional, Any
import requests
from ..base_provider import BaseProvider
from ..types import ModelInfo
import math
class OpenRouterProvider(BaseProvider):
    def __init__(self):
        self.name = "OpenRouter"
        self.get_api_key_link = "https://openrouter.ai/settings/keys"
        
        self.config = {
            "api_token_key": "OPEN_ROUTER_API_KEY"
        }
        
        self.static_models = [
            ModelInfo(name="anthropic/claude-3.5-sonnet", label="Anthropic: Claude 3.5 Sonnet (OpenRouter)", provider="OpenRouter", max_token_allowed=8000),
            ModelInfo(name="anthropic/claude-3-haiku", label="Anthropic: Claude 3 Haiku (OpenRouter)", provider="OpenRouter", max_token_allowed=8000),
            ModelInfo(name="deepseek/deepseek-coder", label="Deepseek-Coder V2 236B (OpenRouter)", provider="OpenRouter", max_token_allowed=8000),
            ModelInfo(name="google/gemini-flash-1.5", label="Google Gemini Flash 1.5 (OpenRouter)", provider="OpenRouter", max_token_allowed=8000),
            ModelInfo(name="google/gemini-pro-1.5", label="Google Gemini Pro 1.5 (OpenRouter)", provider="OpenRouter", max_token_allowed=8000),
            ModelInfo(name="x-ai/grok-beta", label="xAI Grok Beta (OpenRouter)", provider="OpenRouter", max_token_allowed=8000),
            ModelInfo(name="mistralai/mistral-nemo", label="OpenRouter Mistral Nemo (OpenRouter)", provider="OpenRouter", max_token_allowed=8000),
            ModelInfo(name="qwen/qwen-110b-chat", label="OpenRouter Qwen 110b Chat (OpenRouter)", provider="OpenRouter", max_token_allowed=8000),
            ModelInfo(name="cohere/command", label="Cohere Command (OpenRouter)", provider="OpenRouter", max_token_allowed=4096),
        ]
    
    async def get_dynamic_models(
        self, 
        api_keys: Optional[Dict[str, str]] = None, 
        settings: Optional[Dict[str, Any]] = None, 
        server_env: Optional[Dict[str, str]] = None
    ) -> List[ModelInfo]:
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Content-Type": "application/json"}
            )
            
            data = response.json()
            
            # Sort models by name and convert to ModelInfo objects
            sorted_models = sorted(data.get("data", []), key=lambda m: m.get("name", ""))
            
            return [
                ModelInfo(
                    name=model["id"],
                    label=f"{model['name']} - in:${(model['pricing']['prompt'] * 1_000_000):.2f} "
                          f"out:${(model['pricing']['completion'] * 1_000_000):.2f} - "
                          f"context {math.floor(model['context_length'] / 1000)}k",
                    provider=self.name,
                    max_token_allowed=8000
                )
                for model in sorted_models
            ]
        except Exception as error:
            print(f"Error getting OpenRouter models: {error}")
            return []
    
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
            default_api_token_key="OPEN_ROUTER_API_KEY"
        )
        
        api_key = api_key_info.get("api_key")
        
        if not api_key:
            raise ValueError(f"Missing API key for {self.name} provider")
        
        # Implementation for connecting to OpenRouter
        # This would depend on your specific Python client for OpenRouter
        # For example:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
        )
        return client.get_model(model)
