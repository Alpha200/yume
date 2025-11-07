# Yume 🌙

<div align="center">
  <img src="assets/yume.jpg" alt="Yume AI Assistant" width="400" />
</div>

**Yume** (夢 - "dream" in Japanese) is an intelligent AI assistant that integrates with Matrix chat and Home Assistant to provide contextual responses, memory management, automated scheduling capabilities, and location-based triggers.

## Features

- 🤖 **Matrix Chat Integration**: AI-powered responses to messages in Matrix rooms
- 🏠 **Home Assistant Integration**: Weather, calendar, and location data integration
- 📍 **Geofence Events**: Location-based triggers for user interactions
- 🧠 **Advanced Memory System**: Persistent storage with preferences, observations, and reminders
- ⏰ **Intelligent AI Scheduler**: Context-aware scheduling with deferred execution and adaptive re-evaluation
- 📊 **FastAPI Web Interface & Vue.js Dashboard**: Real-time monitoring and control
- 🚀 **Async Processing**: Background operations for optimal performance

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

- **Memory Manager** (`aiagents/memory_manager.py`): Handles memory operations including intelligent cleanup and archival
- **AI Scheduler** (`aiagents/ai_scheduler.py`): Intelligent scheduling agent that analyzes stored memories, user preferences, calendar events, conversation history, and recent interactions to determine optimal timing for the next reminder or user engagement. Features include:
  - Deferred execution with 60-second debounce to consolidate multiple scheduling triggers
  - Automatic re-evaluation of existing schedules based on current context
  - Triggered after every user interaction (chat messages, geofence events, memory reminders)
  - Dual-approach scheduling combining deterministic reminders and AI-powered timing optimization

### Memory System

The memory system supports three types of entries:
- **User Preferences**: Settings and preferences (e.g., "User prefers morning reminders")
- **User Observations**: Observations with optional dates (e.g., "User's birthday is 2023-12-15")
- **Reminders**: One-time or recurring reminders with intelligent scheduling

The AI Scheduler uses a dual-approach strategy:
1. **Deterministic Scheduling**: Explicitly scheduled reminders are prioritized first
2. **AI-Powered Scheduling**: Analyzes calendar events, patterns, and preferences for optimal timing
3. **Conflict Resolution**: Chooses whichever approach results in the earliest suitable interaction time

### Tools Integration

- **Memory Tools** (`tools/memory.py`): Function tools for memory operations including search and CRUD operations
- **Home Assistant Tools** (`tools/home_assistant.py`): Integration tools for smart home control

### Components

- **Conversation** (`components/conversation.py`): Message history data structures
- **Calendar & Weather** (`components/calendar.py`, `components/weather.py`): Data models for external services
- **Logging Manager** (`components/logging_manager.py`): Centralized logging system with recent log tracking
- **Agent Hooks** (`components/agent_hooks.py`): Custom hooks for AI agent behavior customization
- **Timezone Utils** (`components/timezone_utils.py`): Timezone-aware datetime handling for user context

### Interaction Tracking

Yume tracks all AI agent interactions to enable debugging and optimization:
- **Agent Type**: Records which agent executed the interaction (ai_scheduler, ai_engine, etc.)
- **Input/Output**: Stores full input data and generated output for each interaction
- **Metadata**: Captures next_run_time, topic, system instructions, and execution details
- **Persistent History**: Stored in `data/interactions.json` for analysis

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
   
   # AI Model Configuration (Optional)
   AI_ASSISTANT_MODEL=gpt-4o-mini  # Model for main chat assistant (defaults to AI_MODEL)
   AI_SCHEDULER_MODEL=gpt-5-mini  # Model for scheduling agent (defaults to AI_MODEL)
   AI_MEMORY_MODEL=gpt-5-mini  # Model for memory manager agent (defaults to AI_MODEL)
   AI_ENDPOINT_URL=  # Optional: Custom OpenAI API endpoint URL (leave empty for default)
   
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

- **Automatic Categorization**: Messages are analyzed and stored as preferences, observations, or reminders
- **Intelligent Reminder Scheduling**: Create one-time reminders (specific datetime) or recurring reminders (time of day with optional day filter)
- **Adaptive Scheduling**: Re-evaluates existing schedules whenever a new interaction occurs (chat, geofence, or reminder) to adjust timing based on current context
- **Deferred Execution**: 60-second debounce consolidates multiple triggers into a single evaluation, preventing rapid rescheduling
- **Automatic Cleanup**: Memory Janitor runs every 12 hours to archive and clean up old memories

### API Endpoints

The FastAPI interface provides several endpoints for monitoring and control:

- `GET /health` - Health check endpoint for Docker deployments
- `GET /api/memories` - Retrieve all stored memories with full details including reminder scheduling options
- `GET /api/actions` - Get recent AI actions and responses
- `GET /api/scheduled-tasks` - View next scheduled tasks including memory reminders and janitor tasks with topics
- `GET /api/logs` - Access system logs with filtering capabilities
- `GET /api/interactions` - Get summary of recent agent interactions for debugging
- `GET /api/interactions/<id>` - Get detailed information about a specific interaction including input/output and system instructions
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

- **Memory Store**: View all stored memories with type categorization, timestamps, and reminder scheduling details
- **AI Actions**: Recent actions taken by the AI including messages and events
- **Scheduled Tasks**: Next scheduled memory reminders and system tasks with topics and execution timing
- **Executed Reminders**: History of recently executed memory reminder jobs with topics and timestamps
- **Interaction Details**: Detailed view of agent interactions including input data, output, and system instructions for debugging
- **System Logs**: Real-time system logs with level filtering (INFO, DEBUG, WARNING, ERROR)

The dashboard automatically refreshes and provides an intuitive interface for understanding Yume's current state, activity, and decision-making process.

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

### AI Models

Configure which AI models to use:

- `AI_ASSISTANT_MODEL`: Main chat assistant (default: gpt-4o-mini)
- `AI_SCHEDULER_MODEL`: Scheduling agent (default: gpt-5-mini)
- `AI_MEMORY_MODEL`: Memory manager agent (default: gpt-5-mini)

### Other Settings

- `USER_LANGUAGE`: Language for AI responses (default: en)
- Data directory: `./data` (contains memories and interactions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with the OpenAI Agents framework
- Matrix SDK for Python
- FastAPI for web interface
- APScheduler for background tasks
