from typing import Dict, List, Optional, Any, Set, TypeVar, Type, cast
import logging
from .base_provider import BaseProvider
from .types import ModelInfo, ProviderInfo
import importlib
import inspect
import sys
import os
from pathlib import Path

# Create scoped logger
logger = logging.getLogger("LLMManager")

class LLMManager:
    _instance = None
    
    def __init__(self, env: Dict[str, str] = None):
        self._providers: Dict[str, BaseProvider] = {}
        self._model_list: List[ModelInfo] = []
        self._env: Dict[str, Any] = env or {}
        self._register_providers_from_directory()
    
    @classmethod
    def get_instance(cls, env: Dict[str, str] = None) -> 'LLMManager':
        if cls._instance is None:
            cls._instance = LLMManager(env)
        return cls._instance
    
    @property
    def env(self):
        return self._env
    
    def _register_providers_from_directory(self):
        try:
            # Import all providers from the registry
            from . import registry
            
            # Look for exported classes that extend BaseProvider
            for name in dir(registry):
                exported_item = getattr(registry, name)
                if (inspect.isclass(exported_item) and 
                    issubclass(exported_item, BaseProvider) and 
                    exported_item != BaseProvider):
                    
                    try:
                        provider = exported_item()
                        self.register_provider(provider)
                    except Exception as error:
                        logger.warning(f"Failed To Register Provider: {name}, error: {str(error)}")
        except Exception as error:
            logger.error(f"Error registering providers: {error}")
    
    def register_provider(self, provider: BaseProvider):
        if provider.name in self._providers:
            logger.warning(f"Provider {provider.name} is already registered. Skipping.")
            return
        
        logger.info(f"Registering Provider: {provider.name}")
        self._providers[provider.name] = provider
        self._model_list.extend(provider.static_models)
    
    def get_provider(self, name: str) -> Optional[BaseProvider]:
        return self._providers.get(name)
    
    def get_all_providers(self) -> List[BaseProvider]:
        return list(self._providers.values())
    
    def get_model_list(self) -> List[ModelInfo]:
        return self._model_list
    
    async def update_model_list(self, options: Dict[str, Any]) -> List[ModelInfo]:
        api_keys = options.get("api_keys", {})
        provider_settings = options.get("provider_settings", {})
        server_env = options.get("server_env", {})
        
        enabled_providers = [p.name for p in self._providers.values()]
        
        if provider_settings and len(provider_settings) > 0:
            enabled_providers = [p for p in enabled_providers if provider_settings.get(p, {}).get("enabled", False)]
        
        # Get dynamic models from all providers that support them
        dynamic_models = []
        for provider in self._providers.values():
            if provider.name not in enabled_providers:
                continue
                
            if not hasattr(provider, "get_dynamic_models"):
                continue
                
            cached_models = provider.get_models_from_cache(options)
            if cached_models:
                dynamic_models.extend(cached_models)
                continue
            
            try:
                provider_models = await provider.get_dynamic_models(
                    api_keys, 
                    provider_settings.get(provider.name), 
                    server_env
                )
                logger.info(f"Caching {len(provider_models)} dynamic models for {provider.name}")
                provider.store_dynamic_models(options, provider_models)
                dynamic_models.extend(provider_models)
            except Exception as err:
                logger.error(f"Error getting dynamic models {provider.name}: {err}")
        
        static_models = []
        for provider in self._providers.values():
            static_models.extend(provider.static_models or [])
        
        dynamic_model_keys = set(f"{m['name']}-{m['provider']}" for m in dynamic_models)
        filtered_static_models = [m for m in static_models 
                                if f"{m['name']}-{m['provider']}" not in dynamic_model_keys]
        
        # Combine static and dynamic models
        model_list = dynamic_models + filtered_static_models
        model_list.sort(key=lambda m: m["name"])
        self._model_list = model_list
        
        return model_list
    
    def get_static_model_list(self):
        return [m for p in self._providers.values() for m in (p.static_models or [])]
    
    async def get_model_list_from_provider(self, provider_arg: BaseProvider, options: Dict[str, Any]) -> List[ModelInfo]:
        provider = self._providers.get(provider_arg.name)
        
        if not provider:
            raise ValueError(f"Provider {provider_arg.name} not found")
        
        static_models = provider.static_models or []
        
        if not hasattr(provider, "get_dynamic_models"):
            return static_models
        
        api_keys = options.get("api_keys", {})
        provider_settings = options.get("provider_settings", {})
        server_env = options.get("server_env", {})
        
        cached_models = provider.get_models_from_cache({
            "api_keys": api_keys,
            "provider_settings": provider_settings,
            "server_env": server_env
        })
        
        if cached_models:
            logger.info(f"Found {len(cached_models)} cached models for {provider.name}")
            return cached_models + static_models
        
        logger.info(f"Getting dynamic models for {provider.name}")
        
        try:
            dynamic_models = await provider.get_dynamic_models(
                api_keys, 
                provider_settings.get(provider.name), 
                server_env
            )
            logger.info(f"Got {len(dynamic_models)} dynamic models for {provider.name}")
            provider.store_dynamic_models(options, dynamic_models)
        except Exception as err:
            logger.error(f"Error getting dynamic models {provider.name}: {err}")
            dynamic_models = []
        
        dynamic_models_names = [d["name"] for d in dynamic_models]
        filtered_static_list = [m for m in static_models if m["name"] not in dynamic_models_names]
        model_list = dynamic_models + filtered_static_list
        model_list.sort(key=lambda m: m["name"])
        
        return model_list
    
    def get_static_model_list_from_provider(self, provider_arg: BaseProvider) -> List[ModelInfo]:
        provider = self._providers.get(provider_arg.name)
        
        if not provider:
            raise ValueError(f"Provider {provider_arg.name} not found")
        
        return list(provider.static_models or [])
    
    def get_default_provider(self) -> BaseProvider:
        if not self._providers:
            raise ValueError("No providers registered")
        
        return next(iter(self._providers.values()))
