import requests
from typing import List, Dict, Any, Optional
import os
from ..base_provider import BaseProvider
from ..types import ModelInfo

class OpenAIProvider(BaseProvider):
    def __init__(self):
        self.name = 'OpenAI'
        self.get_api_key_link = 'https://platform.openai.com/api-keys'
        
        self.config = {
            'apiTokenKey': 'OPENAI_API_KEY'
        }
        
        self.static_models = [
            {"name": "gpt-4o", "label": "GPT-4o", "provider": "OpenAI", "maxTokenAllowed": 8000},
            {"name": "gpt-4o-mini", "label": "GPT-4o Mini", "provider": "OpenAI", "maxTokenAllowed": 8000},
            {"name": "gpt-4-turbo", "label": "GPT-4 Turbo", "provider": "OpenAI", "maxTokenAllowed": 8000},
            {"name": "gpt-4", "label": "GPT-4", "provider": "OpenAI", "maxTokenAllowed": 8000},
            {"name": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo", "provider": "OpenAI", "maxTokenAllowed": 8000},
        ]
    
    async def get_dynamic_models(
        self, 
        api_keys: Optional[Dict[str, str]] = None,
        settings: Optional[Dict[str, Any]] = None,
        server_env: Optional[Dict[str, str]] = None
    ) -> List[ModelInfo]:
        api_key = self.get_provider_base_url_and_key(
            api_keys=api_keys,
            provider_settings=settings,
            server_env=server_env,
            default_base_url_key='',
            default_api_token_key='OPENAI_API_KEY'
        ).get('api_key')
        
        if not api_key:
            raise ValueError(f"Missing Api Key configuration for {self.name} provider")
        
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        res = response.json()
        static_model_ids = [m["name"] for m in self.static_models]
        
        data = [
            model for model in res.get("data", [])
            if (model.get("object") == "model" and
                (model.get("id", "").startswith("gpt-") or 
                 model.get("id", "").startswith("o") or 
                 model.get("id", "").startswith("chatgpt-")) and
                model.get("id") not in static_model_ids)
        ]
        
        return [
            {
                "name": m.get("id"),
                "label": f"{m.get('id')}",
                "provider": self.name,
                "maxTokenAllowed": m.get("context_window", 32000)
            }
            for m in data
        ]
    
    def get_model_instance(self, options: Dict[str, Any]):
        model = options.get("model")
        server_env = options.get("server_env")
        api_keys = options.get("api_keys")
        provider_settings = options.get("provider_settings", {})
        
        provider_setting = provider_settings.get(self.name, {})
        
        api_key = self.get_provider_base_url_and_key(
            api_keys=api_keys,
            provider_settings=provider_setting,
            server_env=server_env,
            default_base_url_key='',
            default_api_token_key='OPENAI_API_KEY'
        ).get('api_key')
        
        if not api_key:
            raise ValueError(f"Missing API key for {self.name} provider")
        
        # This is a placeholder for the actual model instantiation
        # Since Python doesn't have a direct equivalent to createOpenAI from @ai-sdk/openai
        # you would need to implement or use an appropriate library for OpenAI integration
        import openai
        openai.api_key = api_key
        
        # Return the appropriate model instance
        # This will depend on your actual implementation
        return {
            "model": model,
            "api_key": api_key
        }
