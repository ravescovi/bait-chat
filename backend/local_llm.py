"""
Local LLM clients for LMStudio and Ollama
Provides unified interface for local model inference
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List, AsyncGenerator
from abc import ABC, abstractmethod
from config.settings import settings

logger = logging.getLogger(__name__)


class LocalLLMClient(ABC):
    """Abstract base class for local LLM clients"""
    
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
    
    async def connect(self):
        """Initialize connection to local LLM server"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=settings.LOCAL_MODEL_TIMEOUT)
            )
            
            # Test connection
            health_url = await self._get_health_endpoint()
            if health_url:
                async with self.session.get(health_url) as response:
                    if response.status == 200:
                        self._connected = True
                        logger.info(f"Connected to {self.__class__.__name__} at {self.base_url}")
                        return True
            
            # If no health endpoint, try a simple model request
            if await self._test_connection():
                self._connected = True
                logger.info(f"Connected to {self.__class__.__name__} at {self.base_url}")
                return True
            else:
                logger.warning(f"Failed to connect to {self.__class__.__name__}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to {self.__class__.__name__}: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Close connection to local LLM server"""
        if self.session:
            await self.session.close()
            self._connected = False
            logger.info(f"Disconnected from {self.__class__.__name__}")
    
    def is_connected(self) -> bool:
        """Check if connected to local LLM server"""
        return self._connected
    
    @abstractmethod
    async def _get_health_endpoint(self) -> Optional[str]:
        """Get health check endpoint URL"""
        pass
    
    @abstractmethod
    async def _test_connection(self) -> bool:
        """Test connection with a simple request"""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion"""
        pass


class LMStudioClient(LocalLLMClient):
    """Client for LMStudio local LLM server"""
    
    def __init__(self, base_url: str = None, model_name: str = None):
        base_url = base_url or settings.LMSTUDIO_BASE_URL
        model_name = model_name or settings.LOCAL_MODEL_NAME
        super().__init__(base_url, model_name)
    
    async def _get_health_endpoint(self) -> Optional[str]:
        """LMStudio uses OpenAI-compatible API, so try models endpoint"""
        return f"{self.base_url}/models"
    
    async def _test_connection(self) -> bool:
        """Test connection by listing models"""
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    models = await response.json()
                    logger.info(f"LMStudio available models: {[m.get('id', 'unknown') for m in models.get('data', [])]}")
                    return True
        except Exception as e:
            logger.error(f"LMStudio connection test failed: {e}")
        return False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion using OpenAI-compatible API"""
        if not self._connected:
            await self.connect()
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", settings.LOCAL_MODEL_MAX_TOKENS),
                "temperature": kwargs.get("temperature", settings.LOCAL_MODEL_TEMPERATURE),
                "stream": False
            }
            
            async with self.session.post(
                f"{self.base_url}/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["text"].strip()
                else:
                    error_text = await response.text()
                    logger.error(f"LMStudio API error {response.status}: {error_text}")
                    return "Error generating response with LMStudio"
                    
        except Exception as e:
            logger.error(f"LMStudio generation error: {e}")
            return "Error generating response with LMStudio"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion using OpenAI-compatible API"""
        if not self._connected:
            await self.connect()
        
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", settings.LOCAL_MODEL_MAX_TOKENS),
                "temperature": kwargs.get("temperature", settings.LOCAL_MODEL_TEMPERATURE),
                "stream": False
            }
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    error_text = await response.text()
                    logger.error(f"LMStudio chat API error {response.status}: {error_text}")
                    return "Error generating chat response with LMStudio"
                    
        except Exception as e:
            logger.error(f"LMStudio chat error: {e}")
            return "Error generating chat response with LMStudio"


class OllamaClient(LocalLLMClient):
    """Client for Ollama local LLM server"""
    
    def __init__(self, base_url: str = None, model_name: str = None):
        base_url = base_url or settings.OLLAMA_BASE_URL
        model_name = model_name or settings.LOCAL_MODEL_NAME
        super().__init__(base_url, model_name)
    
    async def _get_health_endpoint(self) -> Optional[str]:
        """Ollama has a simple root endpoint that returns version info"""
        return f"{self.base_url}/api/version"
    
    async def _test_connection(self) -> bool:
        """Test connection by getting version info"""
        try:
            async with self.session.get(f"{self.base_url}/api/version") as response:
                if response.status == 200:
                    version_info = await response.json()
                    logger.info(f"Ollama version: {version_info.get('version', 'unknown')}")
                    return True
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
        return False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion using Ollama API"""
        if not self._connected:
            await self.connect()
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", settings.LOCAL_MODEL_TEMPERATURE),
                    "num_predict": kwargs.get("max_tokens", settings.LOCAL_MODEL_MAX_TOKENS),
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "").strip()
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error {response.status}: {error_text}")
                    return "Error generating response with Ollama"
                    
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return "Error generating response with Ollama"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion using Ollama chat API"""
        if not self._connected:
            await self.connect()
        
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", settings.LOCAL_MODEL_TEMPERATURE),
                    "num_predict": kwargs.get("max_tokens", settings.LOCAL_MODEL_MAX_TOKENS),
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("message", {}).get("content", "").strip()
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama chat API error {response.status}: {error_text}")
                    return "Error generating chat response with Ollama"
                    
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return "Error generating chat response with Ollama"
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models in Ollama"""
        if not self._connected:
            await self.connect()
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("models", [])
                else:
                    logger.error(f"Failed to list Ollama models: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model in Ollama"""
        if not self._connected:
            await self.connect()
        
        try:
            payload = {"name": model_name}
            
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully pulled model: {model_name}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to pull model {model_name}: {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False


class LocalLLMFactory:
    """Factory for creating local LLM clients"""
    
    @staticmethod
    def create_client(provider: str = None, **kwargs) -> LocalLLMClient:
        """Create a local LLM client based on provider"""
        provider = provider or settings.LLM_PROVIDER
        
        if provider == "lmstudio":
            return LMStudioClient(**kwargs)
        elif provider == "ollama":
            return OllamaClient(**kwargs)
        else:
            raise ValueError(f"Unsupported local LLM provider: {provider}")


class LocalLLMService:
    """High-level service for local LLM operations"""
    
    def __init__(self):
        self.client: Optional[LocalLLMClient] = None
        self._provider = settings.LLM_PROVIDER
    
    async def initialize(self):
        """Initialize the local LLM service"""
        if self._provider in ["lmstudio", "ollama"]:
            try:
                self.client = LocalLLMFactory.create_client(self._provider)
                connected = await self.client.connect()
                
                if connected:
                    logger.info(f"Local LLM service initialized with {self._provider}")
                    
                    # For Ollama, check if model exists and pull if needed
                    if self._provider == "ollama":
                        await self._ensure_ollama_model()
                    
                    return True
                else:
                    logger.warning(f"Failed to connect to {self._provider} service")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to initialize local LLM service: {e}")
                return False
        else:
            logger.info("Local LLM service not needed for cloud providers")
            return True
    
    async def _ensure_ollama_model(self):
        """Ensure the configured model exists in Ollama"""
        if isinstance(self.client, OllamaClient):
            models = await self.client.list_models()
            model_names = [m.get("name", "").split(":")[0] for m in models]
            
            if settings.LOCAL_MODEL_NAME not in model_names:
                logger.info(f"Model {settings.LOCAL_MODEL_NAME} not found, attempting to pull...")
                await self.client.pull_model(settings.LOCAL_MODEL_NAME)
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using local LLM"""
        if not self.client:
            return "Local LLM client not initialized"
        
        return await self.client.generate(prompt, **kwargs)
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat response using local LLM"""
        if not self.client:
            return "Local LLM client not initialized"
        
        return await self.client.chat(messages, **kwargs)
    
    async def cleanup(self):
        """Clean up local LLM service"""
        if self.client:
            await self.client.disconnect()


# Global service instance
local_llm_service = LocalLLMService()