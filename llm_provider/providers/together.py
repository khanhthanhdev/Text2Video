import json
import requests
from typing import Dict, List, Optional, Any

class TogetherProvider:
    def __init__(self):
        self.name = 'Together'
        self.get_api_key_link = 'https://api.together.xyz/settings/api-keys'
        
        self.config = {
            'base_url_key': 'TOGETHER_API_BASE_URL',
            'api_token_key': 'TOGETHER_API_KEY',
        }
        
        self.static_models = [
            {
                'name': 'Qwen/Qwen2.5-Coder-32B-Instruct',
                'label': 'Qwen/Qwen2.5-Coder-32B-Instruct',
                'provider': 'Together',
                'max_token_allowed': 8000,
            },
            {
                'name': 'meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo',
                'label': 'meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo',
                'provider': 'Together',
                'max_token_allowed': 8000,
            },
            {
                'name': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
                'label': 'Mixtral 8x7B Instruct',
                'provider': 'Together',
                'max_token_allowed': 8192,
            },
        ]

    def get_provider_base_url_and_key(self, options: Dict[str, Any]) -> Dict[str, str]:
        """Extract base URL and API key from options"""
        api_keys = options.get('api_keys', {})
        provider_settings = options.get('provider_settings', {})
        server_env = options.get('server_env', {})
        default_base_url_key = options.get('default_base_url_key', 'TOGETHER_API_BASE_URL')
        default_api_token_key = options.get('default_api_token_key', 'TOGETHER_API_KEY')
        
        # Try to get base URL and API key from different sources
        base_url = (
            provider_settings.get('baseUrl') or 
            api_keys.get(default_base_url_key) or 
            server_env.get(default_base_url_key)
        )
        
        api_key = (
            provider_settings.get('apiKey') or 
            api_keys.get(default_api_token_key) or 
            server_env.get(default_api_token_key)
        )
        
        return {'base_url': base_url, 'api_key': api_key}

    async def get_dynamic_models(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        settings: Optional[Dict[str, Any]] = None,
        server_env: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch available models from Together API"""
        if server_env is None:
            server_env = {}
            
        provider_info = self.get_provider_base_url_and_key({
            'api_keys': api_keys,
            'provider_settings': settings,
            'server_env': server_env,
            'default_base_url_key': 'TOGETHER_API_BASE_URL',
            'default_api_token_key': 'TOGETHER_API_KEY',
        })
        
        base_url = provider_info['base_url'] or 'https://api.together.xyz/v1'
        api_key = provider_info['api_key']
        
        if not base_url or not api_key:
            return []
            
        try:
            response = requests.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            data = response.json()
            chat_models = [model for model in data if model.get('type') == 'chat']
            
            return [{
                'name': model['id'],
                'label': f"{model['display_name']} - in:${model['pricing']['input']:.2f} out:${model['pricing']['output']:.2f} - context {model['context_length'] // 1000}k",
                'provider': self.name,
                'max_token_allowed': 8000,
            } for model in chat_models]
            
        except Exception as e:
            print(f"Error fetching models from Together API: {e}")
            return []

    def get_model_instance(self, options: Dict[str, Any]) -> Any:
        """Get a model instance for inference"""
        model = options.get('model')
        server_env = options.get('server_env', {})
        api_keys = options.get('api_keys', {})
        provider_settings = options.get('provider_settings', {}).get(self.name, {})
        
        provider_info = self.get_provider_base_url_and_key({
            'api_keys': api_keys,
            'provider_settings': provider_settings,
            'server_env': server_env,
            'default_base_url_key': 'TOGETHER_API_BASE_URL',
            'default_api_token_key': 'TOGETHER_API_KEY',
        })
        
        base_url = provider_info['base_url']
        api_key = provider_info['api_key']
        
        if not base_url or not api_key:
            raise ValueError(f"Missing configuration for {self.name} provider")
            
        # This would return appropriate model interface
        # Implementation would depend on how models are used in the Python codebase
        return {
            'base_url': base_url,
            'api_key': api_key,
            'model': model
        }
