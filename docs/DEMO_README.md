# bAIt-Chat Demo with QServer Integration

This demo showcases bAIt-Chat integrated with a real Bluesky QServer running the test_instrument BITS setup, providing a complete beamline control simulation environment.

## 🎯 What's Included

- **Full QServer Integration**: Real Bluesky QueueServer with test instrument
- **BITS Test Instrument**: Complete instrument setup with simulated devices
- **LMStudio Support**: Local AI model integration for privacy
- **Interactive Chat Interface**: Streamlit-based UI for natural language queries
- **Real Device Discovery**: Automatic detection of available devices and plans

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies and prepare environment
python setup_demo_environment.py

# Make QServer script executable
chmod +x test_instrument/qserver/qs_host.sh
```

### 2. Run Complete Demo
```bash
# Start all services (QServer, Redis, Backend, Frontend)
python demo_with_qserver.py
```

### 3. Access the Interface
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **QServer**: http://localhost:60610
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Manual Setup (Alternative)

If you prefer to start services individually:

### Prerequisites
```bash
# Install Redis (Ubuntu/Debian)
sudo apt update && sudo apt install redis-server
sudo systemctl start redis-server

# Install Python packages
pip install bluesky-queueserver apsbits fastapi uvicorn streamlit aiohttp requests redis
```

### Start Services
```bash
# Terminal 1: Start QServer with test instrument
cd test_instrument/qserver
./qs_host.sh start

# Terminal 2: Start bAIt-Chat backend
python run_with_qserver.py

# Terminal 3: Start Streamlit frontend
streamlit run start_frontend.py --server.port 8501
```

## 🔧 Available Devices & Plans

The test instrument includes:

### Devices
- **sim_motor**: Simulated motor for positioning
- **sim_det**: Simulated noisy detector  
- **shutter**: Simulated APS PSS shutter

### Plans
- **count**: Take measurements at current position
- **scan**: Continuous motor scan with data collection
- **list_scan**: Scan through specific motor positions
- **rel_scan**: Relative scan from current position
- **grid_scan**: 2D scanning with two motors

## 💬 Demo Interactions

Try these example queries in the chat interface:

### Device Queries
- "What devices are available on this beamline?"
- "Tell me about the sim_motor"
- "How do I move the motor to position 5?"

### Plan Explanations
- "Explain the scan plan"
- "How do I run a count measurement?"
- "What's the difference between scan and rel_scan?"

### Operation Guidance
- "How do I set up a grid scan?"
- "What parameters does list_scan need?"
- "Show me an example of using the detector"

## 🖥️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   bAIt-Chat      │    │   QServer       │
│   Frontend      │◄──►│   Backend        │◄──►│   (BITS)        │
│   (Port 8501)   │    │   (Port 8000)    │    │   (Port 60610)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │              ┌─────────▼────────┐              │
         │              │    LMStudio      │              │
         │              │    (Port 1234)   │              │
         │              └──────────────────┘              │
         │                                                │
         └──────────────┐              ┌──────────────────┘
                        │              │
                 ┌──────▼──────┐ ┌─────▼─────┐
                 │   Redis     │ │   Test    │
                 │ (Port 6379) │ │Instrument │
                 └─────────────┘ └───────────┘
```

## 📊 Features Demonstrated

### Real QServer Integration
- **Live Device Discovery**: Automatically fetches available devices from QServer
- **Plan Information**: Real-time access to allowed scan plans and parameters
- **Status Monitoring**: QServer health and queue status
- **BITS Compatibility**: Uses actual BITS instrument configuration

### AI-Powered Assistance  
- **Context-Aware Responses**: AI knows about your specific devices and plans
- **Natural Language Interface**: Ask questions in plain English
- **Local Model Support**: Privacy-preserving AI with LMStudio
- **Fallback Explanations**: Works even without AI model running

### Interactive Web Interface
- **Real-Time Chat**: Persistent conversation with AI assistant
- **Device & Plan Browser**: Visual display of available resources
- **Connection Monitoring**: Live status of all services
- **Responsive Design**: Works on desktop and mobile

## 🔧 Configuration

### QServer Settings
- **Redis URL**: `localhost:6379` (configurable in `qs-config.yml`)
- **ZMQ Ports**: Control `60615`, Info `60625`, Publish console enabled
- **Startup Module**: `test_instrument.startup` (loads BITS devices)

### Backend Settings
- **QServer URL**: `http://localhost:60610` 
- **LMStudio URL**: `http://127.0.0.1:1234`
- **Auto-fallback**: Graceful degradation when services unavailable

### LMStudio Integration
1. Download LMStudio from [lmstudio.ai](https://lmstudio.ai)
2. Load a model (recommended: Mistral 7B Instruct)  
3. Start local server on port 1234
4. Backend automatically detects and uses the model

## 🛟 Troubleshooting

### QServer Won't Start
```bash
# Check if Redis is running
redis-cli ping

# Check QServer logs
cd test_instrument/qserver
./qs_host.sh status

# Restart QServer
./qs_host.sh restart
```

### Backend Connection Issues
```bash
# Test QServer direct access
curl http://localhost:60610/status

# Test backend health
curl http://localhost:8000/health

# Check backend logs
python run_with_qserver.py
```

### Redis Issues
```bash
# Install Redis (Ubuntu/Debian)
sudo apt install redis-server
sudo systemctl start redis-server

# Test Redis connection
redis-cli ping
# Should return: PONG
```

### Dependencies Missing
```bash
# Reinstall all packages
python setup_demo_environment.py

# Or install manually
pip install bluesky-queueserver apsbits fastapi uvicorn streamlit
```

## 🏗️ Extending the Demo

### Adding Custom Devices
1. Edit `test_instrument/test_instrument/configs/devices.yml`
2. Add your device configuration following BITS format
3. Restart QServer to load new devices

### Custom Plans
1. Add plans to `test_instrument/test_instrument/plans/`
2. Import in `startup.py`  
3. Restart QServer

### AI Enhancements
1. Modify system prompts in `run_with_qserver.py`
2. Add domain-specific knowledge
3. Integrate with vector databases for RAG

## 📚 Related Documentation

- [Bluesky Project](https://blueskyproject.io/)
- [QueueServer Documentation](https://blueskyproject.io/bluesky-queueserver/)
- [BITS Documentation](https://github.com/BCDA-APS/apsbits)
- [LMStudio Documentation](https://lmstudio.ai/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 🎉 Success Criteria

After running the demo, you should be able to:
- ✅ See QServer status as "connected" in the sidebar
- ✅ Browse real devices loaded from test_instrument
- ✅ View available scan plans from QServer
- ✅ Chat with AI about specific beamline operations
- ✅ Get context-aware responses about your devices
- ✅ Experience natural language interaction with beamline control

This demo provides a foundation for building production-ready AI assistants for synchrotron beamlines and scientific instruments.