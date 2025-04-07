from ..base_provider import BaseProvider
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio

class GoogleProvider(BaseProvider):
    def __init__(self):
        super().__init__()
        self._name = 'Google'
        self.get_api_key_link = 'https://aistudio.google.com/app/apikey'
        self._config = {
            'api_token_key': 'GOOGLE_GENERATIVE_AI_API_KEY',
        }
        
        self._static_models = [
            {'name': 'gemini-1.5-flash-latest', 'label': 'Gemini 1.5 Flash', 'provider': 'Google', 'max_token_allowed': 8192},
            {'name': 'gemini-2.0-flash-thinking-exp-01-21', 'label': 'Gemini 2.0 Flash-thinking-exp-01-21', 'provider': 'Google', 'max_token_allowed': 65536},
            {'name': 'gemini-2.0-flash-exp', 'label': 'Gemini 2.0 Flash', 'provider': 'Google', 'max_token_allowed': 8192},
            {'name': 'gemini-1.5-flash-002', 'label': 'Gemini 1.5 Flash-002', 'provider': 'Google', 'max_token_allowed': 8192},
            {'name': 'gemini-1.5-flash-8b', 'label': 'Gemini 1.5 Flash-8b', 'provider': 'Google', 'max_token_allowed': 8192},
            {'name': 'gemini-1.5-pro-latest', 'label': 'Gemini 1.5 Pro', 'provider': 'Google', 'max_token_allowed': 8192},
            {'name': 'gemini-1.5-pro-002', 'label': 'Gemini 1.5 Pro-002', 'provider': 'Google', 'max_token_allowed': 8192},
            {'name': 'gemini-exp-1206', 'label': 'Gemini exp-1206', 'provider': 'Google', 'max_token_allowed': 8192},
        ]
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def config(self) -> Dict[str, Any]:
        return self._config
    
    @property
    def static_models(self) -> List[Dict[str, Any]]:
        return self._static_models
    
    async def get_dynamic_models(self, api_keys=None, settings=None, server_env=None) -> List[Dict[str, Any]]:
        provider_info = self.get_provider_base_url_and_key({
            'api_keys': api_keys,
            'provider_settings': settings,
            'server_env': server_env,
            'default_base_url_key': '',
            'default_api_token_key': 'GOOGLE_GENERATIVE_AI_API_KEY',
        })
        
        api_key = provider_info.get('api_key')
        
        if not api_key:
            raise ValueError(f"Missing Api Key configuration for {self.name} provider")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                headers={"Content-Type": "application/json"}
            ) as response:
                res = await response.json()
        
        # Filter models with output token limit > 8000
        filtered_models = [model for model in res.get('models', []) if model.get('outputTokenLimit', 0) > 8000]
        
        # Convert to our model format
        return [
            {
                'name': m.get('name', '').replace('models/', ''),
                'label': f"{m.get('displayName', '')} - context {str(int((m.get('inputTokenLimit', 0) + m.get('outputTokenLimit', 0)) / 1000)) + 'k'}",
                'provider': self.name,
                'max_token_allowed': m.get('inputTokenLimit', 0) + m.get('outputTokenLimit', 0) or 8000,
            }
            for m in filtered_models
        ]
    
    def get_model_instance(self, options: Dict[str, Any]) -> Any:
        model = options.get('model')
        server_env = options.get('server_env')
        api_keys = options.get('api_keys')
        provider_settings = options.get('provider_settings')
        
        provider_info = self.get_provider_base_url_and_key({
            'api_keys': api_keys,
            'provider_settings': provider_settings.get(self.name) if provider_settings else None,
            'server_env': server_env,
            'default_base_url_key': '',
            'default_api_token_key': 'GOOGLE_GENERATIVE_AI_API_KEY',
        })
        
        api_key = provider_info.get('api_key')
        
        if not api_key:
            raise ValueError(f"Missing API key for {self.name} provider")
        
        # Placeholder for creating a Google Generative AI model instance
        return self._create_google_model(api_key, model)
    
    def _create_google_model(self, api_key: str, model: str) -> Any:
        """
        Placeholder for creating a Google Generative AI model instance.
        
        In a real implementation, you would use your Python equivalent of
        the createGoogleGenerativeAI function from the TypeScript code.
        """
        # This is where you'd implement the actual model creation
        # using Google's generative AI Python SDK
        # For example:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model)
        return model

