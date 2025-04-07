from ..base_provider import BaseProvider
from typing import Dict, Any, List, Optional

class GithubProvider(BaseProvider):
    def __init__(self):
        super().__init__()
        self._name = 'Github'
        self.get_api_key_link = 'https://github.com/settings/personal-access-tokens'
        self._config = {
            'api_token_key': 'GITHUB_API_KEY',
        }
        
        # find more in https://github.com/marketplace?type=models
        self._static_models = [
            {'name': 'gpt-4o', 'label': 'GPT-4o', 'provider': 'Github', 'max_token_allowed': 8000},
            {'name': 'o1', 'label': 'o1-preview', 'provider': 'Github', 'max_token_allowed': 100000},
            {'name': 'o1-mini', 'label': 'o1-mini', 'provider': 'Github', 'max_token_allowed': 8000},
            {'name': 'gpt-4o-mini', 'label': 'GPT-4o Mini', 'provider': 'Github', 'max_token_allowed': 8000},
            {'name': 'gpt-4-turbo', 'label': 'GPT-4 Turbo', 'provider': 'Github', 'max_token_allowed': 8000},
            {'name': 'gpt-4', 'label': 'GPT-4', 'provider': 'Github', 'max_token_allowed': 8000},
            {'name': 'gpt-3.5-turbo', 'label': 'GPT-3.5 Turbo', 'provider': 'Github', 'max_token_allowed': 8000},
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
            'default_api_token_key': 'GITHUB_API_KEY',
        })
        
        api_key = provider_info.get('api_key')
        
        if not api_key:
            raise ValueError(f"Missing API key for {self.name} provider")
        
        # This is a placeholder for the equivalent Python implementation
        # You'll need to implement or import the equivalent of createOpenAI
        # For example:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key
        )
        return client.chat.completions
        
        # Placeholder implementation
        # return self._create_openai_model(api_key, model)
    
    def _create_openai_model(self, api_key: str, model: str) -> Any:
        """
        Placeholder for creating an OpenAI model instance for GitHub.
        
        In a real implementation, you would use your Python equivalent of
        the createOpenAI function from the TypeScript code.
        """
        # This is where you'd implement the actual model creation
        # using whatever API or library you're using to interface with GitHub's models
        from ..base_provider import get_openai_like_model
        return get_openai_like_model(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key,
            model=model
        )
