# Local LLM Setup Guide

This guide explains how to set up and use local LLM models with bAIt-Chat using LMStudio or Ollama.

## Overview

bAIt-Chat supports running with local LLM models for:
- **Privacy**: Keep all data processing local
- **Cost**: No API fees for model usage
- **Offline Operation**: Work without internet connectivity
- **Custom Models**: Use specialized or fine-tuned models

## Supported Providers

### 1. LMStudio
- **Best for**: Users who want a GUI for model management
- **Platform**: Windows, macOS, Linux
- **API**: OpenAI-compatible REST API
- **Website**: https://lmstudio.ai/

### 2. Ollama
- **Best for**: Command-line users and server deployments
- **Platform**: macOS, Linux, Windows (WSL)
- **API**: Native REST API
- **Website**: https://ollama.ai/

## Quick Start

### Option 1: LMStudio Setup

1. **Install LMStudio**
   ```bash
   # Download from https://lmstudio.ai/
   # Install and launch the application
   ```

2. **Download a Model**
   - Open LMStudio
   - Go to "Discover" tab
   - Search and download a model (e.g., "llama-2-7b-chat")
   - Wait for download to complete

3. **Start Local Server**
   - Go to "Local Server" tab
   - Select your downloaded model
   - Click "Start Server"
   - Note the server URL (usually http://localhost:1234)

4. **Configure bAIt-Chat**
   ```bash
   # Edit .env file
   LLM_PROVIDER=lmstudio
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   LOCAL_MODEL_NAME=your-model-name
   LOCAL_MODEL_TEMPERATURE=0.7
   ```

### Option 2: Ollama Setup

1. **Install Ollama**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows (WSL)
   # Download from https://ollama.ai/
   ```

2. **Download and Run a Model**
   ```bash
   # Download and run Llama 2
   ollama run llama2
   
   # Or try other models
   ollama run codellama
   ollama run mistral
   ```

3. **Configure bAIt-Chat**
   ```bash
   # Edit .env file
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   LOCAL_MODEL_NAME=llama2
   LOCAL_MODEL_TEMPERATURE=0.7
   ```

## Recommended Models

### For Scientific/Technical Use

| Model | Size | Best For | RAM Required |
|-------|------|----------|-------------|
| **llama2** | 7B | General science chat | 8GB |
| **codellama** | 7B | Code explanation | 8GB |
| **mistral** | 7B | Technical accuracy | 8GB |
| **llama2:13b** | 13B | Better reasoning | 16GB |
| **mixtral** | 8x7B | High performance | 48GB |

### Model Selection Guidelines

- **4GB RAM**: Use quantized 3B models (limited capability)
- **8GB RAM**: Use 7B models (good for most tasks)
- **16GB RAM**: Use 13B models (better reasoning)
- **32GB+ RAM**: Use larger models or multiple models

## Configuration Options

### Environment Variables

```bash
# Provider selection
LLM_PROVIDER=lmstudio  # or ollama

# LMStudio configuration
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LLM_MODEL=your-model-name

# Ollama configuration  
OLLAMA_BASE_URL=http://localhost:11434
LOCAL_MODEL_NAME=llama2

# Model parameters
LOCAL_MODEL_TEMPERATURE=0.7      # Creativity (0.0-1.0)
LOCAL_MODEL_MAX_TOKENS=4000      # Response length
LOCAL_MODEL_TIMEOUT=60           # Request timeout
```

### Performance Tuning

```bash
# For better performance
LOCAL_MODEL_TEMPERATURE=0.3      # More focused responses
LOCAL_MODEL_MAX_TOKENS=2000      # Shorter responses

# For more creative responses
LOCAL_MODEL_TEMPERATURE=0.8      # More creative
LOCAL_MODEL_MAX_TOKENS=8000      # Longer responses
```

## Docker Setup

### LMStudio with Docker

```yaml
# docker-compose.local-llm.yml
version: '3.8'
services:
  backend:
    environment:
      - LLM_PROVIDER=lmstudio
      - LMSTUDIO_BASE_URL=http://host.docker.internal:1234/v1
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### Ollama with Docker

```yaml
# docker-compose.local-llm.yml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    container_name: bait-chat-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    
  backend:
    environment:
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - LOCAL_MODEL_NAME=llama2
    depends_on:
      - ollama

volumes:
  ollama_data:
```

## Usage Examples

### Basic Setup

```bash
# 1. Start your local LLM server
ollama run llama2

# 2. Update environment
export LLM_PROVIDER=ollama
export LOCAL_MODEL_NAME=llama2

# 3. Start bAIt-Chat
make run-backend
```

### Development with Local Models

```bash
# Start with local model
LLM_PROVIDER=ollama make docker-up

# Check logs
docker logs bait-chat-backend

# Test the API
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"plan_name": "scan"}'
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   ```bash
   # Check if service is running
   curl http://localhost:11434/api/version  # Ollama
   curl http://localhost:1234/v1/models     # LMStudio
   ```

2. **Model Not Found**
   ```bash
   # List available models
   ollama list                              # Ollama
   # Check LMStudio GUI for loaded models
   ```

3. **Slow Responses**
   - Reduce `LOCAL_MODEL_MAX_TOKENS`
   - Use smaller models (7B instead of 13B)
   - Increase `LOCAL_MODEL_TIMEOUT`

4. **Out of Memory**
   - Use quantized models (Q4, Q8)
   - Reduce context size
   - Close other applications

### Performance Optimization

```bash
# Ollama optimizations
export OLLAMA_NUM_PARALLEL=2      # Parallel requests
export OLLAMA_MAX_LOADED_MODELS=1 # Memory usage
export OLLAMA_FLASH_ATTENTION=1   # Speed boost (if supported)
```

### Model Management

```bash
# Ollama commands
ollama list                 # List installed models
ollama rm model_name        # Remove model
ollama cp source dest       # Copy model
ollama show model_name      # Show model info

# Pull specific model versions
ollama pull llama2:7b-chat-q4_0
ollama pull codellama:13b-instruct
```

## Integration Testing

### Test Local LLM Setup

```python
# test_local_llm.py
import asyncio
from backend.local_llm import LocalLLMFactory

async def test_local_llm():
    client = LocalLLMFactory.create_client("ollama")
    await client.connect()
    
    response = await client.generate("Explain what a scan plan does in one sentence.")
    print(f"Response: {response}")
    
    await client.disconnect()

# Run test
asyncio.run(test_local_llm())
```

### API Testing

```bash
# Test explain endpoint
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "plan_source": "def scan(det, motor, start, stop, num): yield from scan_nd([det], motor, start, stop, num)"
  }'

# Expected: Detailed explanation using local LLM
```

## Best Practices

### Model Selection
1. **Start small**: Begin with 7B models
2. **Test thoroughly**: Validate responses for scientific accuracy
3. **Monitor resources**: Watch RAM and CPU usage
4. **Backup models**: Keep multiple model options

### Performance
1. **Warm up models**: Keep models loaded between requests
2. **Batch requests**: Process multiple queries together when possible
3. **Cache responses**: Implement response caching for common queries
4. **Monitor latency**: Track response times

### Security
1. **Network isolation**: Run models on isolated networks if needed
2. **Resource limits**: Set appropriate CPU/memory limits
3. **Model validation**: Verify model sources and integrity
4. **Access control**: Limit access to model APIs

## Migration Guide

### From Cloud to Local

```bash
# 1. Backup current configuration
cp .env .env.cloud-backup

# 2. Install local LLM service
# Follow installation instructions above

# 3. Update configuration
LLM_PROVIDER=ollama  # or lmstudio
# Comment out API keys
# OPENAI_API_KEY=...

# 4. Test functionality
make test-unit
```

### Between Local Providers

```bash
# Switch from LMStudio to Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LOCAL_MODEL_NAME=llama2

# Or vice versa
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
```

## Advanced Configuration

### Custom Models

```bash
# Ollama: Import custom model
ollama create my-model -f Modelfile

# LMStudio: Load custom GGUF files
# Use the GUI to load custom .gguf files
```

### Multiple Models

```bash
# Run different models for different tasks
export EXPLANATION_MODEL=codellama
export CHAT_MODEL=llama2
export ANALYSIS_MODEL=mistral
```

### Performance Monitoring

```python
# Add to local_llm.py for monitoring
import time

async def timed_generate(self, prompt: str, **kwargs) -> str:
    start_time = time.time()
    response = await self.generate(prompt, **kwargs)
    end_time = time.time()
    
    logger.info(f"LLM generation took {end_time - start_time:.2f}s")
    return response
```

## Support

- **LMStudio**: https://lmstudio.ai/docs
- **Ollama**: https://github.com/jmorganca/ollama
- **Model Hub**: https://huggingface.co/models
- **Performance Issues**: Check system resources and model size compatibility