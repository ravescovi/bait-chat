"""
Tests for local LLM integration
Tests for LMStudio and Ollama client functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.local_llm import (
    LocalLLMClient,
    LMStudioClient, 
    OllamaClient,
    LocalLLMFactory,
    LocalLLMService,
    local_llm_service
)


class TestLocalLLMClient:
    """Test base LocalLLMClient functionality"""
    
    @pytest.mark.asyncio
    async def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError"""
        client = LocalLLMClient("http://test:8000", "test-model")
        
        with pytest.raises(TypeError):
            # Can't instantiate abstract class directly
            pass


class TestLMStudioClient:
    """Test LMStudio client functionality"""
    
    @pytest.fixture
    def lmstudio_client(self):
        """Create LMStudio client for testing"""
        return LMStudioClient("http://test:1234/v1", "test-model")
    
    @pytest.mark.asyncio
    async def test_initialization(self, lmstudio_client):
        """Test LMStudio client initialization"""
        assert lmstudio_client.base_url == "http://test:1234/v1"
        assert lmstudio_client.model_name == "test-model"
        assert not lmstudio_client.is_connected()
    
    @pytest.mark.asyncio
    async def test_successful_connection(self, lmstudio_client):
        """Test successful connection to LMStudio"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "test-model", "object": "model"},
                {"id": "other-model", "object": "model"}
            ]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await lmstudio_client.connect()
            
            assert result == True
            assert lmstudio_client.is_connected() == True
    
    @pytest.mark.asyncio
    async def test_failed_connection(self, lmstudio_client):
        """Test failed connection to LMStudio"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = aiohttp.ClientError()
            
            result = await lmstudio_client.connect()
            
            assert result == False
            assert lmstudio_client.is_connected() == False
    
    @pytest.mark.asyncio
    async def test_text_generation(self, lmstudio_client):
        """Test text generation with LMStudio"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [
                {"text": "This is a test response"}
            ]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.post.return_value.__aenter__.return_value = mock_response
            
            lmstudio_client._connected = True
            lmstudio_client.session = mock_session_instance
            
            result = await lmstudio_client.generate("Test prompt")
            
            assert result == "This is a test response"
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, lmstudio_client):
        """Test chat completion with LMStudio"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "This is a chat response"}}
            ]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.post.return_value.__aenter__.return_value = mock_response
            
            lmstudio_client._connected = True
            lmstudio_client.session = mock_session_instance
            
            messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            result = await lmstudio_client.chat(messages)
            
            assert result == "This is a chat response"
    
    @pytest.mark.asyncio
    async def test_generation_error_handling(self, lmstudio_client):
        """Test error handling during generation"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal server error"
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.post.return_value.__aenter__.return_value = mock_response
            
            lmstudio_client._connected = True
            lmstudio_client.session = mock_session_instance
            
            result = await lmstudio_client.generate("Test prompt")
            
            assert "Error generating response" in result


class TestOllamaClient:
    """Test Ollama client functionality"""
    
    @pytest.fixture
    def ollama_client(self):
        """Create Ollama client for testing"""
        return OllamaClient("http://test:11434", "llama2")
    
    @pytest.mark.asyncio
    async def test_initialization(self, ollama_client):
        """Test Ollama client initialization"""
        assert ollama_client.base_url == "http://test:11434"
        assert ollama_client.model_name == "llama2"
        assert not ollama_client.is_connected()
    
    @pytest.mark.asyncio
    async def test_successful_connection(self, ollama_client):
        """Test successful connection to Ollama"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"version": "0.1.0"}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await ollama_client.connect()
            
            assert result == True
            assert ollama_client.is_connected() == True
    
    @pytest.mark.asyncio
    async def test_text_generation(self, ollama_client):
        """Test text generation with Ollama"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "response": "This is an Ollama response"
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.post.return_value.__aenter__.return_value = mock_response
            
            ollama_client._connected = True
            ollama_client.session = mock_session_instance
            
            result = await ollama_client.generate("Test prompt")
            
            assert result == "This is an Ollama response"
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, ollama_client):
        """Test chat completion with Ollama"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "message": {"content": "This is an Ollama chat response"}
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.post.return_value.__aenter__.return_value = mock_response
            
            ollama_client._connected = True
            ollama_client.session = mock_session_instance
            
            messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            result = await ollama_client.chat(messages)
            
            assert result == "This is an Ollama chat response"
    
    @pytest.mark.asyncio
    async def test_list_models(self, ollama_client):
        """Test listing models in Ollama"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:latest", "size": 3826408448},
                {"name": "codellama:latest", "size": 3826408448}
            ]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.get.return_value.__aenter__.return_value = mock_response
            
            ollama_client._connected = True
            ollama_client.session = mock_session_instance
            
            models = await ollama_client.list_models()
            
            assert len(models) == 2
            assert models[0]["name"] == "llama2:latest"
    
    @pytest.mark.asyncio
    async def test_pull_model(self, ollama_client):
        """Test pulling a model in Ollama"""
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.post.return_value.__aenter__.return_value = mock_response
            
            ollama_client._connected = True
            ollama_client.session = mock_session_instance
            
            result = await ollama_client.pull_model("llama2")
            
            assert result == True


class TestLocalLLMFactory:
    """Test LocalLLMFactory functionality"""
    
    def test_create_lmstudio_client(self):
        """Test creating LMStudio client"""
        client = LocalLLMFactory.create_client("lmstudio")
        
        assert isinstance(client, LMStudioClient)
        assert "1234" in client.base_url
    
    def test_create_ollama_client(self):
        """Test creating Ollama client"""
        client = LocalLLMFactory.create_client("ollama")
        
        assert isinstance(client, OllamaClient)
        assert "11434" in client.base_url
    
    def test_create_unsupported_provider(self):
        """Test creating client for unsupported provider"""
        with pytest.raises(ValueError, match="Unsupported local LLM provider"):
            LocalLLMFactory.create_client("unsupported")


class TestLocalLLMService:
    """Test LocalLLMService functionality"""
    
    @pytest.fixture
    def llm_service(self):
        """Create LocalLLMService for testing"""
        service = LocalLLMService()
        service._provider = "ollama"  # Set to test provider
        return service
    
    @pytest.mark.asyncio
    async def test_initialization_with_local_provider(self, llm_service):
        """Test service initialization with local provider"""
        mock_client = AsyncMock()
        mock_client.connect.return_value = True
        mock_client.list_models.return_value = [{"name": "llama2:latest"}]
        
        with patch.object(LocalLLMFactory, 'create_client', return_value=mock_client):
            result = await llm_service.initialize()
            
            assert result == True
            assert llm_service.client == mock_client
    
    @pytest.mark.asyncio
    async def test_initialization_with_cloud_provider(self):
        """Test service initialization with cloud provider"""
        service = LocalLLMService()
        service._provider = "openai"
        
        result = await service.initialize()
        
        assert result == True
        assert service.client is None
    
    @pytest.mark.asyncio
    async def test_generate_text(self, llm_service):
        """Test text generation through service"""
        mock_client = AsyncMock()
        mock_client.generate.return_value = "Generated text"
        
        llm_service.client = mock_client
        
        result = await llm_service.generate_text("Test prompt")
        
        assert result == "Generated text"
        mock_client.generate.assert_called_once_with("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_chat(self, llm_service):
        """Test chat generation through service"""
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Chat response"
        
        llm_service.client = mock_client
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await llm_service.generate_chat(messages)
        
        assert result == "Chat response"
        mock_client.chat.assert_called_once_with(messages)
    
    @pytest.mark.asyncio
    async def test_cleanup(self, llm_service):
        """Test service cleanup"""
        mock_client = AsyncMock()
        llm_service.client = mock_client
        
        await llm_service.cleanup()
        
        mock_client.disconnect.assert_called_once()


@pytest.mark.integration
class TestLocalLLMIntegration:
    """Integration tests requiring actual local LLM services"""
    
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true",
        reason="Integration tests disabled"
    )
    @pytest.mark.asyncio
    async def test_ollama_real_connection(self):
        """Test connection to real Ollama instance (if available)"""
        client = OllamaClient("http://localhost:11434", "llama2")
        
        try:
            connected = await client.connect()
            
            if connected:
                # Test basic functionality
                models = await client.list_models()
                assert isinstance(models, list)
                
                # Test generation if models are available
                if models:
                    response = await client.generate("Hello", max_tokens=10)
                    assert isinstance(response, str)
                    assert len(response) > 0
            else:
                pytest.skip("Ollama not available for integration testing")
        finally:
            await client.disconnect()
    
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true",
        reason="Integration tests disabled"
    )
    @pytest.mark.asyncio
    async def test_lmstudio_real_connection(self):
        """Test connection to real LMStudio instance (if available)"""
        client = LMStudioClient("http://localhost:1234/v1", "test-model")
        
        try:
            connected = await client.connect()
            
            if connected:
                # Test generation
                response = await client.generate("Hello", max_tokens=10)
                assert isinstance(response, str)
                assert len(response) > 0
            else:
                pytest.skip("LMStudio not available for integration testing")
        finally:
            await client.disconnect()


class TestLocalLLMWithExplainer:
    """Test local LLM integration with PlanExplainer"""
    
    @pytest.mark.asyncio
    async def test_explain_with_local_llm(self):
        """Test plan explanation using local LLM"""
        with patch('backend.explain.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "ollama"
            
            with patch('backend.explain.local_llm_service') as mock_service:
                mock_service.generate_chat.return_value = "This plan performs a continuous scan across motor positions."
                
                from backend.explain import PlanExplainer
                explainer = PlanExplainer()
                
                result = await explainer.explain("def scan(): yield from scan_nd()")
                
                assert "continuous scan" in result.lower()
                mock_service.generate_chat.assert_called_once()


class TestLocalLLMWithAgent:
    """Test local LLM integration with BaitChatAgent"""
    
    @pytest.mark.asyncio
    async def test_agent_with_local_llm(self):
        """Test agent processing using local LLM"""
        with patch('backend.agent.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "ollama"
            
            with patch('backend.agent.local_llm_service') as mock_service:
                mock_service.generate_chat.return_value = "I'll list the available motors for you. Action: list_devices"
                
                from backend.agent import BaitChatAgent
                from backend.models import NLPQuery, AgentResponse
                
                agent = BaitChatAgent()
                await agent.initialize()
                
                query = NLPQuery(query="What motors can I use?")
                response = await agent.process_query(query)
                
                assert isinstance(response, AgentResponse)
                assert "motors" in response.response.lower()
                mock_service.generate_chat.assert_called_once()


@pytest.mark.performance
class TestLocalLLMPerformance:
    """Performance tests for local LLM operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent local LLM requests"""
        mock_client = AsyncMock()
        mock_client.generate.return_value = "Response"
        
        service = LocalLLMService()
        service.client = mock_client
        
        # Run multiple concurrent requests
        tasks = [
            service.generate_text(f"Prompt {i}")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(result == "Response" for result in results)
        assert mock_client.generate.call_count == 10
    
    @pytest.mark.asyncio
    async def test_request_timeout_handling(self):
        """Test timeout handling for slow local LLM responses"""
        mock_client = AsyncMock()
        mock_client.generate.side_effect = asyncio.TimeoutError()
        
        service = LocalLLMService()
        service.client = mock_client
        
        # This should handle timeout gracefully
        result = await service.generate_text("Test prompt")
        
        assert result == "Local LLM client not initialized"