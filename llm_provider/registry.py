from .providers.anthropic import AnthropicProvider
from .providers.deepseek import DeepseekProvider
from .providers.google import GoogleProvider
from .providers.groq import GroqProvider
from .providers.openai import OpenAIProvider
from .providers.together import TogetherProvider
from .providers.github import GithubProvider
from .providers.openrouter import OpenRouterProvider
# Dictionary of all providers for easy access by name
PROVIDERS = {
    'anthropic': AnthropicProvider,
    'deepseek': DeepseekProvider,
    'google': GoogleProvider,
    'groq': GroqProvider,
    'openai': OpenAIProvider,
    'github': GithubProvider,
    'together': TogetherProvider,
    'openrouter': OpenRouterProvider,
}

__all__ = [
    'AnthropicProvider',
    'DeepseekProvider',
    'GoogleProvider',
    'GroqProvider',
    'OpenAIProvider',
    'OpenRouterProvider',
    'TogetherProvider',
    'GithubProvider',
    'PROVIDERS'
]
