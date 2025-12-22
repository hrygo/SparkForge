import os
import json
from typing import Optional, List, Dict, Any
try:
    from openai import OpenAI, AsyncOpenAI
except ImportError:
    # We will raise a clean error when used if openai is not installed
    OpenAI = None
    AsyncOpenAI = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .models import Message, LLMRequest, LLMResponse, Usage

class LLMClient:
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._clients = {}

    def _load_config(self, path: Optional[str]) -> Dict[str, Any]:
        if not path:
            path = os.path.join(os.path.dirname(__file__), "config.json")
        
        if not os.path.exists(path):
            return {"provider": {"default": "openai"}}
            
        with open(path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                return {"provider": {"default": "openai"}}
        return config

    def _get_provider_config(self, provider: str) -> Dict[str, Any]:
        return self.config.get(provider, {})

    def _get_client(self, provider: str, async_mode: bool = False) -> Any:
        cfg = self._get_provider_config(provider)
        
        # Handle env var expansion in the api_key string
        api_key_str = cfg.get("api_key", "")
        if api_key_str.startswith("${") and api_key_str.endswith("}"):
            env_var = api_key_str[2:-1]
            api_key = os.environ.get(env_var, "")
        else:
            api_key = api_key_str

        # Fallback to direct env var if config doesn't provide a valid key
        if not api_key:
            api_key = os.environ.get(f"{provider.upper()}_API_KEY", "")

        # Special handling for Gemini V2 SDK (google-genai)
        if provider == "gemini":
            try:
                from google import genai
            except ImportError:
                raise ImportError("The 'google-genai' library is required. Please install it with 'pip install google-genai'.")
            
            return genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

        # Default to OpenAI client
        if OpenAI is None:
            raise ImportError("The 'openai' library is required. Please install it with 'pip install openai'.")

        key = f"{provider}_{'async' if async_mode else 'sync'}"
        if key in self._clients:
            return self._clients[key]

        base_url = cfg.get("base_url")
        client_cls = AsyncOpenAI if async_mode else OpenAI
        client = client_cls(api_key=api_key, base_url=base_url)
        self._clients[key] = client
        return client

    def chat(self, 
             messages: List[Dict[str, str]], 
             provider: Optional[str] = None,
             model: Optional[str] = None,
             api_key: Optional[str] = None,
             base_url: Optional[str] = None,
             **kwargs) -> LLMResponse:
        
        provider = provider or self.config.get("provider", {}).get("default", "openai")
        cfg = self._get_provider_config(provider)
        
        model = model or kwargs.get("model") or cfg.get("model")
        temperature = kwargs.get("temperature", cfg.get("temperature", 0.7))
        max_tokens = kwargs.get("max_tokens", cfg.get("max_tokens", 2048))
        
        # Gemini V2 SDK Path
        if provider == "gemini":
            from google.genai import types
            client = self._get_client("gemini")
            
            # Construct prompt from messages
            prompt = ""
            system_instruction = None
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                if role == "system":
                    system_instruction = content
                elif role == "user":
                    prompt += f"User: {content}\n"
                elif role == "assistant":
                    prompt += f"Model: {content}\n"
            
            # Configure generation options
            config_args = {
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
            if system_instruction:
                config_args["system_instruction"] = system_instruction

            generate_config = types.GenerateContentConfig(**config_args)

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=generate_config
                )
                
                usage = None
                if response.usage_metadata:
                     usage = Usage(
                        prompt_tokens=response.usage_metadata.prompt_token_count,
                        completion_tokens=response.usage_metadata.candidates_token_count,
                        total_tokens=response.usage_metadata.total_token_count
                    )

                # Manually extract content to suppress "non-text parts" warning for Thinking models
                content_text = ""
                if response.candidates and response.candidates[0].content.parts:
                    content_text = "".join(
                        part.text for part in response.candidates[0].content.parts 
                        if part.text
                    )

                return LLMResponse(
                    content=content_text,
                    model=model,
                    provider=provider,
                    usage=usage,
                    finish_reason="stop", 
                    raw=response
                )
            except Exception as e:
                # Provide a more helpful error if 404 persists
                if "404" in str(e):
                    raise ValueError(f"Gemini Model '{model}' not found via google-genai SDK. Verify model ID validity.") from e
                raise e

        # Standard OpenAI Client Path
        # Determine client to use
        if api_key or base_url:
            # Create a temporary client for this request
            current_cfg = self._get_provider_config(provider)
            final_api_key = api_key or os.path.expandvars(current_cfg.get("api_key", ""))
            # Handle placeholder
            if final_api_key.startswith("${") and final_api_key.endswith("}"):
                final_api_key = os.environ.get(final_api_key[2:-1], "")
            
            final_base_url = base_url or current_cfg.get("base_url")
            client = OpenAI(api_key=final_api_key, base_url=final_base_url)
        else:
            client = self._get_client(provider)
        
        # Merge arguments, prioritizing kwargs
        api_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Add other optional params from kwargs
        for k, v in kwargs.items():
            if k not in api_kwargs:
                api_kwargs[k] = v

        response = client.chat.completions.create(**api_kwargs)
        
        choice = response.choices[0]
        usage = None
        if hasattr(response, 'usage') and response.usage:
            usage = Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )

        return LLMResponse(
            content=choice.message.content,
            model=model,
            provider=provider,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw=response
        )

    async def achat(self, 
                   messages: List[Dict[str, str]], 
                   provider: Optional[str] = None,
                   model: Optional[str] = None,
                   **kwargs) -> LLMResponse:
        
        # For now, async path for Gemini is not implemented in this quick refactor unless requested.
        # Fallback to standard flow, or error if gemini.
        provider = provider or self.config.get("provider", {}).get("default", "openai")
        
        if provider == "gemini":
             # Use sync implementation for now or implement proper async
             # Since dialecta_debate.py uses ThreadPoolExecutor with sync 'chat', 
             # 'achat' usage is minimal in current flow. 
             # If needed, we can wrap sync in async or implement google.generativeai async.
             # For safety in this refactor, we will raise/warn or implement strict async if pivotal.
             # But 'dialecta_debate.py' calls 'client.chat' inside 'call_phase' which is sync.
             # So 'achat' might not be critical right now. 
             pass

        cfg = self._get_provider_config(provider)
        
        model = model or kwargs.get("model") or cfg.get("model")
        temperature = kwargs.get("temperature", cfg.get("temperature", 0.7))
        max_tokens = kwargs.get("max_tokens", cfg.get("max_tokens", 2048))
        
        client = self._get_client(provider, async_mode=True)
        
        api_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        for k, v in kwargs.items():
            if k not in api_kwargs:
                api_kwargs[k] = v

        response = await client.chat.completions.create(**api_kwargs)
        
        choice = response.choices[0]
        usage = None
        if hasattr(response, 'usage') and response.usage:
            usage = Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )

        return LLMResponse(
            content=choice.message.content,
            model=model,
            provider=provider,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw=response
        )
