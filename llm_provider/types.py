from typing import Dict, List, Optional, Protocol, Callable, Any

class ModelInfo:
    name: str
    label: str
    provider: str
    max_token_allowed: int  # Converting camelCase to snake_case

class LanguageModelV1(Protocol):
    # This is a placeholder for the actual LanguageModelV1 interface
    pass

class IProviderSetting(Protocol):
    # This is a placeholder for the actual IProviderSetting interface
    pass

class ProviderInfo:
    name: str
    static_models: List[ModelInfo]  # Converting camelCase to snake_case
    get_dynamic_models: Optional[Callable[[Optional[Dict[str, str]], Optional[IProviderSetting], Optional[Dict[str, str]]], Any]]  # Converting camelCase to snake_case
    get_model_instance: Callable[[Dict[str, Any]], LanguageModelV1]  # Converting camelCase to snake_case
    get_api_key_link: Optional[str]  # Converting camelCase to snake_case
    label_for_get_api_key: Optional[str]  # Converting camelCase to snake_case
    icon: Optional[str]

class ProviderConfig:
    base_url_key: Optional[str]  # Converting camelCase to snake_case
    base_url: Optional[str]  # Converting camelCase to snake_case
    api_token_key: Optional[str]  # Converting camelCase to snake_case
