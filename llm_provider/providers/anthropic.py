import os
import json
import requests
from typing import Dict, List, Optional, Any, Union

from ..base_provider import BaseProvider
from ..types import ModelInfo

class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self):
        self.name = 'Anthropic'
        self.get_api_key_link = 'https://console.anthropic.com/settings/keys'
        
        self.config = {
            'api_token_key': 'ANTHROPIC_API_KEY',
        }
        
        self.static_models = [
            {
                'name': 'claude-3-7-sonnet-20250219',
                'label': 'Claude 3.7 Sonnet',
                'provider': 'Anthropic',
                'max_token_allowed': 8000,
            },
            {
                'name': 'claude-3-5-sonnet-latest',
                'label': 'Claude 3.5 Sonnet (new)',
                'provider': 'Anthropic',
                'max_token_allowed': 8000,
            },
            {
                'name': 'claude-3-5-sonnet-20240620',
                'label': 'Claude 3.5 Sonnet (old)',
                'provider': 'Anthropic',
                'max_token_allowed': 8000,
            },
            {
                'name': 'claude-3-5-haiku-latest',
                'label': 'Claude 3.5 Haiku (new)',
                'provider': 'Anthropic',
                'max_token_allowed': 8000,
            },
            {
                'name': 'claude-3-opus-latest',
                'label': 'Claude 3 Opus',
                'provider': 'Anthropic',
                'max_token_allowed': 8000
            },
            {
                'name': 'claude-3-sonnet-20240229',
                'label': 'Claude 3 Sonnet',
                'provider': 'Anthropic',
                'max_token_allowed': 8000
            },
            {
                'name': 'claude-3-haiku-20240307',
                'label': 'Claude 3 Haiku',
                'provider': 'Anthropic',
                'max_token_allowed': 8000
            },
        ]
    
    async def get_dynamic_models(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        settings: Optional[Dict[str, Any]] = None,
        server_env: Optional[Dict[str, str]] = None
    ) -> List[ModelInfo]:
        """Retrieve available models from Anthropic API."""
        api_key_info = self.get_provider_base_url_and_key(
            api_keys=api_keys,
            provider_settings=settings,
            server_env=server_env,
            default_base_url_key='',
            default_api_token_key='ANTHROPIC_API_KEY'
        )
        
        api_key = api_key_info.get('api_key')
        
        if not api_key:
            raise ValueError(f"Missing API Key configuration for {self.name} provider")
        
        response = requests.get(
            "https://api.anthropic.com/v1/models",
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
            }
        )
        
        response_data = response.json()
        static_model_ids = [model['name'] for model in self.static_models]
        
        filtered_models = [
            model for model in response_data.get('data', [])
            if model.get('type') == 'model' and model.get('id') not in static_model_ids
        ]
        
        return [
            {
                'name': model['id'],
                'label': model['display_name'],
                'provider': self.name,
                'max_token_allowed': 32000
            }
            for model in filtered_models
        ]
    
    def get_model_instance(
        self,
        model: str,
        server_env: Dict[str, str],
        api_keys: Optional[Dict[str, str]] = None,
        provider_settings: Optional[Dict[str, Any]] = None
    ):
        """Get an instance of the Anthropic model."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with 'pip install anthropic'")
        
        api_key_info = self.get_provider_base_url_and_key(
            api_keys=api_keys,
            provider_settings=provider_settings,
            server_env=server_env,
            default_base_url_key='',
            default_api_token_key='ANTHROPIC_API_KEY'
        )
        
        api_key = api_key_info.get('api_key')
        
        if not api_key:
            raise ValueError(f"Missing API Key configuration for {self.name} provider")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        def generate_text(prompt: str, **kwargs):
            return client.messages.create(
                model=model,
                max_tokens=kwargs.get('max_tokens', 1000),
                messages=[{"role": "user", "content": prompt}]
            ).content[0].text
        
        def generate_chat(messages: List[Dict[str, str]], **kwargs):
            # Convert to Anthropic message format
            anthropic_messages = []
            for msg in messages:
                if msg["role"] in ["user", "assistant"]:
                    anthropic_messages.append({"role": msg["role"], "content": msg["content"]})
            
            response = client.messages.create(
                model=model,
                max_tokens=kwargs.get('max_tokens', 1000),
                messages=anthropic_messages
            )
            return response.content[0].text
        
        # Create a callable object with both methods
        model_instance = type('AnthropicModel', (), {
            'generate_text': generate_text,
            'generate_chat': generate_chat,
            'model': model,
            'provider': self.name
        })()
        
        return model_instance
    
    def get_provider_base_url_and_key(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        provider_settings: Optional[Dict[str, Any]] = None,
        server_env: Optional[Dict[str, str]] = None,
        default_base_url_key: str = '',
        default_api_token_key: str = ''
    ) -> Dict[str, str]:
        """Helper to get API key and base URL from various sources."""
        api_keys = api_keys or {}
        provider_settings = provider_settings or {}
        server_env = server_env or {}
        
        # First try from provided api_keys
        api_key = api_keys.get(self.name)
        
        # Then try from provider settings
        if not api_key and self.name in provider_settings:
            settings = provider_settings.get(self.name, {})
            api_key = settings.get('apiKey')
        
        # Finally, try from environment variables
        if not api_key:
            api_key = server_env.get(default_api_token_key) or os.environ.get(default_api_token_key)
        
        return {
            'api_key': api_key,
            'base_url': None  # Anthropic doesn't use base URL
        }
