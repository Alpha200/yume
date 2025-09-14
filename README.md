# Yume 🌙

<div align="center">
  <img src="assets/yume.jpg" alt="Yume AI Assistant" width="400" />
</div>

**Yume** (夢 - "dream" in Japanese) is an intelligent AI assistant that integrates with Matrix chat and Home Assistant to provide contextual responses, memory management, automated scheduling capabilities, and location-based triggers.

## Features

- 🤖 **Matrix Chat Integration**: Responds to messages in Matrix rooms with AI-powered responses
- 🏠 **Home Assistant Integration**: Fetches weather forecasts, calendar events, and user location data
- 📍 **Geofence Events**: Triggers AI responses when entering or leaving locations via API endpoints
- 🧠 **Advanced Memory System**: Persistent memory with user preferences, observations, and reminders
- ⏰ **Smart Scheduling**: Automated memory reminders and background task processing
- 🌐 **Context-Aware**: Combines conversation history, weather, calendar, and location data for intelligent responses
- 📊 **FastAPI Web Interface**: RESTful API for monitoring, control, and triggering location events
- 🎯 **Vue.js Dashboard**: Real-time monitoring of memories, actions, scheduled tasks, and system logs
- 🚀 **Optimized Performance**: Background processing for faster response times

## Architecture

Yume is built with a modular architecture consisting of several key components:

### Core Services

- **AI Engine** (`services/ai_engine.py`): Unified AI agent that handles both decision-making and response generation using the OpenAI Agents framework
- **Matrix Bot** (`services/matrix_bot.py`): Matrix protocol client for chat integration
- **AI Scheduler** (`services/ai_scheduler.py`): Background task scheduling with APScheduler
- **Context Manager** (`services/context_manager.py`): Aggregates data from multiple sources into unified context
- **Memory Manager** (`services/memory_manager.py`): Persistent memory storage with support for user preferences, observations, and reminders
- **Home Assistant** (`services/home_assistant.py`): Integration with Home Assistant API

### AI Agents

- **Memory Manager** (`aiagents/memory_manager.py`): Handles memory operations and intelligent cleanup
- **AI Scheduler** (`aiagents/ai_scheduler.py`): Determines optimal timing for memory-based reminders

### Memory System

The memory system supports three types of entries:
- **User Preferences**: Settings and preferences (e.g., "User prefers morning reminders")
- **User Observations**: Observations with dates (e.g., "User's birthday is 2023-12-15")
- **Reminders**: One-time or recurring reminders with scheduling options

### Tools Integration

- **Memory Tools** (`tools/memory.py`): Function tools for memory operations including search and CRUD operations
- **Home Assistant Tools** (`tools/home_assistant.py`): Integration tools for smart home control

### Components

- **Conversation** (`components/conversation.py`): Message history data structures
- **Calendar & Weather** (`components/calendar.py`, `components/weather.py`): Data models for external services
- **Logging Manager** (`components/logging_manager.py`): Centralized logging system
- **Agent Hooks** (`components/agent_hooks.py`): Custom hooks for AI agent behavior

## Performance Optimizations

- **Background Processing**: Memory updates and scheduling run asynchronously for faster response times
- **Unified AI Agent**: Single agent handles both decision-making and response generation, reducing API calls by 50%
- **Efficient Memory Access**: Formatted memory retrieval with consistent formatting across the application

## Installation

### Prerequisites

- Python 3.13+
- Poetry (for dependency management)
- Matrix account and room
- Home Assistant instance (optional)
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd yume
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Configure environment variables**
   Create a `.env` file or set the following environment variables:

   ```bash
   # Matrix Configuration
   MATRIX_HOMESERVER=https://matrix.example.com
   MATRIX_USER_ID=@botname:example.com
   MATRIX_PASSWORD=your_bot_password
   MATRIX_ROOM_ID=!roomid:example.com
   MATRIX_SYSTEM_USERNAME=botname

   # Home Assistant Configuration (Optional)
   HA_URL=http://localhost:8123
   HA_TOKEN=your_ha_token
   HA_DEVICE_TRACKER_ENTITY=device_tracker.phone
   HA_WEATHER_ENTITY=weather.forecast_home
   HA_CALENDAR_ENTITY=calendar.personal
   HA_TIMEZONE=Europe/Berlin

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   
   # User Configuration
   USER_LANGUAGE=en  # Language for AI responses
   ```

## Usage

### Running the Application

```bash
# Using Poetry
poetry run python main.py

# Or directly with Python
python main.py
```

The application will start:
- FastAPI server on `http://0.0.0.0:8200`
- Matrix bot connecting to your configured room
- AI scheduler with automatic memory management
- Background processing for optimal performance

### Memory Management

Yume automatically manages memories with the following features:

- **Automatic Categorization**: Messages are analyzed and relevant information is stored as preferences, observations, or reminders
- **Smart Reminders**: The system determines optimal timing for reminders based on content and user behavior
- **Background Processing**: Memory updates happen asynchronously to maintain fast response times
- **Formatted Retrieval**: Consistent memory formatting across all system components

### API Endpoints

The FastAPI interface provides several endpoints for monitoring and control:

- `GET /` - Health check and system status
- `GET /api/memories` - Retrieve all stored memories with formatted data
- `GET /api/actions` - Get recent AI actions and responses
- `GET /api/scheduled-tasks` - View next scheduled tasks and reminders
- `GET /api/logs` - Access system logs with filtering capabilities
- `POST /api/geofence-event` - Trigger geofence events (enter/leave locations)
- `POST /webhook` - Webhook endpoint for external integrations

#### Geofence Event API

Trigger location-based AI responses by posting to the geofence endpoint:

```bash
# Example: User enters home location
curl -X POST http://localhost:8200/api/geofence-event \
  -H "Content-Type: application/json" \
  -d '{
    "geofence_name": "Home", 
    "event_type": "enter"
  }'

# Example: User leaves work location  
curl -X POST http://localhost:8200/api/geofence-event \
  -H "Content-Type: application/json" \
  -d '{
    "geofence_name": "Office", 
    "event_type": "leave"
  }'
```

The API validates that `event_type` is either "enter" or "leave" and returns a response indicating success or failure along with any AI-generated message.

### Vue.js Dashboard

Access the web dashboard at `http://localhost:8200` to monitor:

- **Memory Store**: View all stored memories with type categorization and timestamps
- **AI Actions**: Recent actions taken by the AI including messages and events
- **Scheduled Tasks**: Next scheduled memory reminders and system tasks
- **System Logs**: Real-time system logs with level filtering

The dashboard automatically refreshes and provides an intuitive interface for understanding Yume's current state and activity.

### Docker Deployment

```bash
# Build the image
docker build -t yume .

# Run with automatic volume for data persistence
docker run -d --name yume -p 8200:8200 --env-file .env yume

# Or specify a named volume for easier management
docker run -d --name yume -p 8200:8200 -v yume-data:/app/data --env-file .env yume

# View logs
docker logs -f yume

# Backup memory data
docker run --rm -v yume-data:/data -v $(pwd):/backup alpine tar czf /backup/yume-data-backup.tar.gz -C /data .
```

**Important**: The `/app/data` directory is configured as a Docker volume to persist memory data across container restarts. Without a named volume or bind mount, data will be lost when the container is removed.

## Configuration

### Memory System

The memory system can be configured through the following parameters:

- **Data Directory**: Default `./data` - stores `memories.json`
- **Memory Types**: Support for user_preference, user_observation, and reminder entries
- **Automatic Cleanup**: Configurable memory retention and cleanup policies

### AI Behavior

- **Response Style**: Conversational, natural language with emoji support
- **Language Support**: Configurable user language via `USER_LANGUAGE` environment variable
- **Context Integration**: Automatic inclusion of weather, calendar, location, and memory data

## Development

### Project Structure

```
yume/
├── main.py                 # Application entry point
├── services/              # Core business logic
├── aiagents/             # AI-specific modules
├── components/           # Shared components and data models
├── tools/               # Function tools for AI agents
├── data/               # Persistent data storage
└── README.md           # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with the OpenAI Agents framework
- Matrix SDK for Python
- FastAPI for web interface
- APScheduler for background tasks
