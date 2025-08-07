# Changelog

All notable changes to bAIt-Chat will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-07

### 🚀 Major Features Added

#### Real-Time Instrument Introspection
- **Live Device Monitoring**: Real-time device positions, limits, and connection status
- **Smart Device Categorization**: Automatic classification (motors, detectors, shutters, slits)
- **Environment Status Integration**: QServer environment monitoring and health checks
- **Individual Device Inspection**: Detailed per-device analysis with `/instrument/devices/{device_name}/details` endpoint

#### Intelligent Plan Analysis System
- **Comprehensive Plan Discovery**: Analyze all available Bluesky plans with enhanced metadata
- **Parameter Intelligence**: 
  - Automatic type inference (float, int, list[Detector], Motor, etc.)
  - Validation rules and constraints
  - Smart parameter suggestions based on available devices
  - Required vs optional parameter detection
- **Complexity Assessment**: Automatic difficulty rating (low/medium/high)
- **Smart Recommendations**: Skill-level based plan suggestions (beginner/intermediate/advanced)
- **Execution Analysis**: Duration estimates and prerequisite detection
- **Related Plans Discovery**: Find similar or complementary plans
- **Smart Examples**: Context-aware usage examples with actual available devices

#### Enhanced User Interface
- **Multi-Tab Plan Interface**: 
  - **All Plans**: Filterable browser with complexity and category filters
  - **Recommendations**: Personalized suggestions by skill level and device type
  - **Analysis**: Visual analytics with charts and breakdowns
- **Color-Coded Complexity Indicators**: 🟢 Beginner | 🟡 Intermediate | 🔴 Advanced
- **Interactive Parameter Tables**: Type information, validation rules, and suggestions
- **Smart Filtering**: Filter by complexity, category, device type
- **Visual Analytics**: Bar charts for plan categories and complexity distribution

### 🛠️ Backend Enhancements

#### New API Endpoints
- `GET /instrument/devices/detailed` - Enhanced device information with real-time status
- `GET /instrument/devices/{device_name}/details` - Individual device inspection
- `GET /instrument/plans/detailed` - Comprehensive plan analysis
- `GET /instrument/plans/recommendations` - Smart plan recommendations
- `POST /instrument/plan/validate` - Plan parameter validation

#### Advanced Analysis Functions
- Parameter type inference and validation rule generation
- Device position reading and status monitoring
- Plan complexity assessment algorithms
- Smart recommendation engine with multiple strategies
- Usage pattern analysis and history summarization

### 🎨 Frontend Improvements
- Enhanced multi-tab instrument introspection interface
- Real-time status indicators and connection monitoring
- Interactive parameter tables with validation feedback
- Visual analytics dashboard with complexity and category charts
- Improved filtering and search capabilities
- Better error handling and user feedback

### 🔧 Technical Improvements
- **Modern Python Packaging**: Pure pyproject.toml configuration (removed setup.py)
- **Docker Containerization**: Complete Docker Compose setup with health checks
- **Enhanced Scripts**: Comprehensive shell scripts for all deployment scenarios
- **Improved Project Structure**: Organized package layout with tests moved to `bait_chat/tests/`
- **Better Error Handling**: Comprehensive exception handling and graceful degradation
- **Performance Optimization**: Efficient device status caching and batch operations

### ♻️ Refactoring & Cleanup
- **Removed Knowledge Base**: Pivoted from static knowledge to dynamic instrument introspection
- **Centralized Vector DB**: Moved `vector_db` into `bait_chat` package
- **Cleaned Project Structure**: Removed legacy files and organized codebase
- **Updated Dependencies**: Fixed Pydantic v2 compatibility issues
- **Enhanced Configuration**: Better environment variable handling with `pydantic-settings`

### 📚 Documentation
- **Comprehensive README**: Detailed feature documentation with usage examples
- **API Documentation**: Enhanced endpoint documentation with examples
- **Installation Guides**: Multiple installation options (local, Docker, package)
- **Feature Showcase**: Visual examples of introspection capabilities

### 🐛 Bug Fixes
- Fixed Pydantic v2 BaseSettings import issues
- Resolved environment variable validation conflicts
- Improved error handling for QServer connection failures
- Fixed import path issues after project restructuring

### 📋 Previous Versions

## [0.2.0] - 2024-12-XX
### Added
- QueueServer integration with real BITS test instrument
- LMStudio AI integration for local inference
- Docker support with compose.yml
- RESTful API with FastAPI backend
- Streamlit frontend interface

## [0.1.0] - 2024-12-XX
### Added
- Initial project structure
- Basic chat interface
- Mock device and plan support
- Core architecture setup

---

### Legend
- 🚀 Major Features
- 🛠️ Backend/API
- 🎨 Frontend/UI  
- 🔧 Technical/Infrastructure
- ♻️ Refactoring
- 🐛 Bug Fixes
- 📚 Documentation
- 📋 Maintenance