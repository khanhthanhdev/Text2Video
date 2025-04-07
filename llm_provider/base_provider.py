from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar, Generic, Union
import json
import os

# These would be imported from your project's types
# You'll need to define these types in your Python project
from .types import ProviderInfo, ProviderConfig, ModelInfo

class BaseProvider(ABC, ProviderInfo):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def static_models(self) -> List[ModelInfo]:
        pass
    
    @property
    @abstractmethod
    def config(self) -> ProviderConfig:
        pass
    
    def __init__(self):
        self.cached_dynamic_models = None
        self.get_api_key_link = None
        self.label_for_get_api_key = None
        self.icon = None
    
    def get_provider_base_url_and_key(self, options: Dict[str, Any]) -> Dict[str, str]:
        api_keys = options.get("api_keys", {})
        provider_settings = options.get("provider_settings", {})
        server_env = options.get("server_env", {})
        default_base_url_key = options.get("default_base_url_key")
        default_api_token_key = options.get("default_api_token_key")
        
        settings_base_url = provider_settings.get("base_url") if provider_settings else None
        
        # Importing here to avoid circular import
        from .manager import LLMManager
        manager = LLMManager.get_instance()
        
        if settings_base_url and len(settings_base_url) == 0:
            settings_base_url = None
        
        base_url_key = self.config.get("base_url_key") or default_base_url_key
        
        # Try to get the base URL from various sources
        base_url = (
            settings_base_url or
            server_env.get(base_url_key) if server_env else None or
            os.environ.get(base_url_key) or
            manager.env.get(base_url_key) if manager.env else None or
            self.config.get("base_url")
        )
        
        if base_url and base_url.endswith('/'):
            base_url = base_url[:-1]
        
        api_token_key = self.config.get("api_token_key") or default_api_token_key
        
        # Try to get the API key from various sources
        api_key = (
            api_keys.get(self.name) if api_keys else None or
            server_env.get(api_token_key) if server_env else None or
            os.environ.get(api_token_key) or
            manager.env.get(api_token_key) if manager.env else None
        )
        
        return {
            "base_url": base_url,
            "api_key": api_key
        }
    
    def get_models_from_cache(self, options: Dict[str, Any]) -> Optional[List[ModelInfo]]:
        if not self.cached_dynamic_models:
            return None
        
        cache_key = self.cached_dynamic_models.get("cache_id")
        generated_cache_key = self.get_dynamic_models_cache_key(options)
        
        if cache_key != generated_cache_key:
            self.cached_dynamic_models = None
            return None
        
        return self.cached_dynamic_models.get("models")
    
    def get_dynamic_models_cache_key(self, options: Dict[str, Any]) -> str:
        api_keys = options.get("api_keys", {})
        provider_settings = options.get("provider_settings", {})
        server_env = options.get("server_env", {})
        
        cache_data = {
            "api_keys": api_keys.get(self.name) if api_keys else None,
            "provider_settings": provider_settings.get(self.name) if provider_settings else None,
            "server_env": server_env
        }
        
        return json.dumps(cache_data)
    
    def store_dynamic_models(self, options: Dict[str, Any], models: List[ModelInfo]) -> None:
        cache_id = self.get_dynamic_models_cache_key(options)
        
        self.cached_dynamic_models = {
            "cache_id": cache_id,
            "models": models
        }
    
    # This method is optional in subclasses
    def get_dynamic_models(self, api_keys=None, settings=None, server_env=None) -> List[ModelInfo]:
        """
        Optional method that can be implemented by subclasses to fetch dynamic models
        """
        return []
    
    @abstractmethod
    def get_model_instance(self, options: Dict[str, Any]) -> Any:
        """
        Get a model instance based on the provided options
        
        Args:
            options: Dictionary containing model details and configuration
                - model: The model name/ID to instantiate
                - server_env: Environment variables from the server
                - api_keys: API keys for various providers
                - provider_settings: Settings for various providers
                
        Returns:
            A language model instance
        """
        pass


def get_openai_like_model(base_url: str, api_key: Optional[str], model: str) -> Any:
    """
    Creates an OpenAI-compatible model instance
    
    Note: This is a placeholder function that would need to be replaced with your 
    actual implementation using whatever OpenAI-compatible library you're using in Python
    """
    # This would depend on your Python implementation equivalent to createOpenAI
    # For example with the openai Python package:
    from openai import OpenAI
    client = OpenAI(base_url=base_url, api_key=api_key)
    return client.chat.completions.create(model=model)
    raise NotImplementedError("This function needs to be implemented with your OpenAI client library")
