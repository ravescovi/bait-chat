# Using LMStudio with OpenAI-OSS Models

LMStudio provides excellent support for running OpenAI-compatible models locally, offering both privacy and offline capabilities for bAIt-Chat.

## Quick Setup

1. **Download and Install LMStudio**
   - Visit [lmstudio.ai](https://lmstudio.ai) and download for your platform
   - Install and launch the application

2. **Configure Your Environment**
   ```bash
   # Copy and edit your .env file
   cp .env.example .env
   ```

   Add these settings to your `.env`:
   ```env
   # Use LMStudio as the LLM provider
   LLM_PROVIDER=lmstudio
   
   # LMStudio server configuration
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   LMSTUDIO_MODEL_NAME=gpt-3.5-turbo
   LMSTUDIO_CONTEXT_LENGTH=4096
   LMSTUDIO_GPU_LAYERS=-1
   
   # Model generation settings
   LOCAL_MODEL_TEMPERATURE=0.7
   LOCAL_MODEL_MAX_TOKENS=4000
   LOCAL_MODEL_TIMEOUT=60
   ```

## Recommended OpenAI-OSS Models

### For Chat and General Tasks
- **Mistral 7B Instruct**: Excellent for conversational AI
- **Llama 2 7B Chat**: Good balance of performance and resource usage
- **CodeLlama 7B Instruct**: Specialized for code understanding
- **Phi-2**: Compact but powerful for reasoning tasks

### For Scientific/Technical Tasks
- **Llama 2 13B Chat**: Better understanding of complex technical concepts
- **CodeLlama 13B Instruct**: Enhanced code comprehension for beamline plans
- **WizardCoder**: Optimized for code generation and explanation

## Step-by-Step Configuration

### 1. Download a Model in LMStudio
1. Open LMStudio
2. Go to the "Search" tab
3. Search for "mistral-7b-instruct" or "llama-2-7b-chat"
4. Click download on your preferred model
5. Wait for download to complete

### 2. Start the Local Server
1. Go to the "Local Server" tab in LMStudio
2. Select your downloaded model
3. Configure settings:
   - **Context Length**: 4096 (adjust based on model)
   - **GPU Layers**: -1 (use all available GPU)
   - **Temperature**: 0.7
4. Click "Start Server"
5. Note the server URL (typically `http://localhost:1234`)

### 3. Test the Connection
```bash
# Test if LMStudio is running
curl http://localhost:1234/v1/models

# Test chat completion
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

### 4. Start bAIt-Chat
```bash
# Start the backend
make run-backend

# In another terminal, start the frontend
make run-frontend

# Or use Docker
make docker-up
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | Set to `lmstudio` for local inference |
| `LMSTUDIO_BASE_URL` | `http://localhost:1234/v1` | LMStudio server endpoint |
| `LMSTUDIO_MODEL_NAME` | `gpt-3.5-turbo` | Model identifier in requests |
| `LMSTUDIO_CONTEXT_LENGTH` | `4096` | Maximum context window |
| `LMSTUDIO_GPU_LAYERS` | `-1` | GPU acceleration (-1 = auto) |
| `LOCAL_MODEL_TEMPERATURE` | `0.7` | Response randomness (0.0-1.0) |
| `LOCAL_MODEL_MAX_TOKENS` | `4000` | Maximum response length |
| `LOCAL_MODEL_TIMEOUT` | `60` | Request timeout in seconds |

## Model-Specific Configurations

### Mistral 7B Instruct
```env
LMSTUDIO_MODEL_NAME=mistral-7b-instruct-v0.1
LMSTUDIO_CONTEXT_LENGTH=8192
LOCAL_MODEL_TEMPERATURE=0.7
LOCAL_MODEL_MAX_TOKENS=4000
```

### Llama 2 7B Chat
```env
LMSTUDIO_MODEL_NAME=llama-2-7b-chat
LMSTUDIO_CONTEXT_LENGTH=4096
LOCAL_MODEL_TEMPERATURE=0.8
LOCAL_MODEL_MAX_TOKENS=3000
```

### CodeLlama 7B Instruct
```env
LMSTUDIO_MODEL_NAME=codellama-7b-instruct
LMSTUDIO_CONTEXT_LENGTH=4096
LOCAL_MODEL_TEMPERATURE=0.3
LOCAL_MODEL_MAX_TOKENS=2000
```

## Performance Tips

### Hardware Requirements
- **Minimum**: 8GB RAM, CPU-only inference
- **Recommended**: 16GB+ RAM, NVIDIA GPU with 6GB+ VRAM
- **Optimal**: 32GB+ RAM, NVIDIA RTX 3080/4080 or better

### Optimization Settings
```env
# For better performance on limited hardware
LMSTUDIO_CONTEXT_LENGTH=2048
LOCAL_MODEL_MAX_TOKENS=1000
LOCAL_MODEL_TIMEOUT=120

# For high-end hardware
LMSTUDIO_CONTEXT_LENGTH=8192
LOCAL_MODEL_MAX_TOKENS=4000
LMSTUDIO_GPU_LAYERS=-1  # Use all GPU layers
```

### Memory Management
- **7B models**: ~4-6GB VRAM
- **13B models**: ~8-10GB VRAM
- **CPU fallback**: Uses system RAM instead

## Troubleshooting

### Common Issues

**1. Connection Refused**
```bash
# Check if LMStudio server is running
curl http://localhost:1234/v1/models
```
- Solution: Start the local server in LMStudio

**2. Model Not Found**
- Ensure `LMSTUDIO_MODEL_NAME` matches the model loaded in LMStudio
- LMStudio typically uses `gpt-3.5-turbo` as the default model name

**3. Slow Response Times**
- Reduce context length and max tokens
- Enable GPU acceleration if available
- Consider using a smaller model (7B instead of 13B)

**4. Out of Memory**
- Reduce `LMSTUDIO_GPU_LAYERS` to use less VRAM
- Lower `LMSTUDIO_CONTEXT_LENGTH`
- Close other GPU-intensive applications

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
make run-backend
```

## Integration with bAIt-Chat Features

### Plan Explanation
Local models excel at explaining Bluesky scan plans:
```python
# Example: scan([pilatus], motor_x, 0, 5, 51)
# LMStudio Response: "This plan performs a continuous scan of motor_x from 0 to 5 mm, collecting 51 data points with the Pilatus detector..."
```

### Device Queries
Ask about beamline devices naturally:
```
User: "What detectors are available?"
LMStudio: "Based on your beamline configuration, you have: Pilatus 300K area detector, Ion chambers (i0, i1), and a photodiode detector available."
```

### Error Analysis
Get help with scan failures:
```
User: "My scan failed with 'motor limit reached'"
LMStudio: "This error indicates the motor tried to move beyond its configured limits. Check the scan parameters and motor limit settings."
```

## Privacy and Security Benefits

- **Complete Privacy**: No data sent to external servers
- **Offline Operation**: Works without internet connection
- **Custom Models**: Use domain-specific models if available
- **Data Retention**: All conversations stay on your system
- **Compliance**: Meets strict data governance requirements

## Next Steps

1. **Download LMStudio**: Get it from [lmstudio.ai](https://lmstudio.ai)
2. **Choose a Model**: Start with Mistral 7B Instruct for best balance
3. **Configure Environment**: Update your `.env` file with LMStudio settings
4. **Test Integration**: Run `make test-local-llm` to verify functionality
5. **Monitor Performance**: Use `make check-services` to monitor system health

For additional help, see the main [LOCAL_MODELS.md](LOCAL_MODELS.md) documentation or check the troubleshooting section in the project README.