from abc import ABC, abstractmethod
import os
from typing import Dict, Any, Optional, List, Union


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass
    
    @abstractmethod
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from a conversation."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo"):
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with 'pip install openai'")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it as OPENAI_API_KEY environment variable or pass it directly.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response.choices[0].message.content
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response.choices[0].message.content
    
    @property
    def provider_name(self) -> str:
        return "OpenAI"


class TogetherAIProvider(LLMProvider):
    """Together AI provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "togethercomputer/llama-2-70b-chat"):
        try:
            import together
        except ImportError:
            raise ImportError("Together AI package not installed. Install with 'pip install together'")
        
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("Together AI API key is required. Set it as TOGETHER_API_KEY environment variable or pass it directly.")
        
        together.api_key = self.api_key
        self.together = together
        self.model = model
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.together.Completion.create(
            model=kwargs.get("model", self.model),
            prompt=prompt,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response['output']['choices'][0]['text']
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Format messages for Together AI chat completion
        formatted_messages = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return self.generate_text(formatted_messages, **kwargs)
    
    @property
    def provider_name(self) -> str:
        return "Together AI"


class GeminiProvider(LLMProvider):
    """Google Gemini AI provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Install with 'pip install google-generativeai'")
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set it as GOOGLE_API_KEY environment variable or pass it directly.")
        
        genai.configure(api_key=self.api_key)
        self.genai = genai
        self.model = model
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        model = self.genai.GenerativeModel(kwargs.get("model", self.model))
        response = model.generate_content(prompt)
        return response.text
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        model = self.genai.GenerativeModel(kwargs.get("model", self.model))
        chat = model.start_chat()
        
        # Add all but the last message to the chat history
        for msg in messages[:-1]:
            if msg["role"] == "user":
                chat.send_message(msg["content"])
            # Skip assistant messages as they'll be generated responses
        
        # Send the last message and get the response
        last_msg = messages[-1]
        if last_msg["role"] == "user":
            response = chat.send_message(last_msg["content"])
            return response.text
        return ""
    
    @property
    def provider_name(self) -> str:
        return "Google Gemini"


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with 'pip install anthropic'")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set it as ANTHROPIC_API_KEY environment variable or pass it directly.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        message = self.client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", 1000),
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Convert to Anthropic message format
        anthropic_messages = []
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})
        
        message = self.client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", 1000),
            messages=anthropic_messages
        )
        return message.content[0].text
    
    @property
    def provider_name(self) -> str:
        return "Anthropic Claude"


class GroqProvider(LLMProvider):
    """Groq AI provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama2-70b-4096"):
        try:
            import groq
        except ImportError:
            raise ImportError("Groq package not installed. Install with 'pip install groq'")
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set it as GROQ_API_KEY environment variable or pass it directly.")
        
        self.client = groq.Client(api_key=self.api_key)
        self.model = model
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response.choices[0].message.content
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response.choices[0].message.content
    
    @property
    def provider_name(self) -> str:
        return "Groq"


def get_llm_provider(provider_name: str, api_key: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    """
    Factory function to get an instance of the requested LLM provider.
    
    Args:
        provider_name: Name of the provider (case insensitive)
        api_key: Optional API key (will use environment variables if not provided)
        model: Optional model name (will use provider default if not specified)
    
    Returns:
        An instance of the requested LLM provider
    
    Raises:
        ValueError: If the provider is not supported
    """
    provider_name = provider_name.lower()
    
    if provider_name == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4-turbo")
    elif provider_name == "togetherai":
        return TogetherAIProvider(api_key=api_key, model=model or "togethercomputer/llama-2-70b-chat")
    elif provider_name == "gemini":
        return GeminiProvider(api_key=api_key, model=model or "gemini-pro")
    elif provider_name == "claude":
        return ClaudeProvider(api_key=api_key, model=model or "claude-3-opus-20240229")
    elif provider_name == "groq":
        return GroqProvider(api_key=api_key, model=model or "llama2-70b-4096")
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}. Supported providers are: openai, togetherai, gemini, claude, groq")
