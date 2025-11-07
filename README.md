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
- ⏰ **Intelligent AI Scheduler**: AI-powered scheduling agent that analyzes memories, preferences, and calendar events to determine optimal timing for reminders and interactions
- 🌐 **Context-Aware**: Combines conversation history, weather, calendar, location data, and memory context for intelligent responses
- 📊 **FastAPI Web Interface**: RESTful API for monitoring, control, and triggering location events
- 🎯 **Vue.js Dashboard**: Real-time monitoring of memories, actions, scheduled tasks, executed reminders, and system logs
- 🚀 **Optimized Performance**: Background processing with async operations for faster response times
- 📈 **Interaction Tracking**: Detailed tracking of all agent interactions with input/output data for debugging and optimization

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
- **AI Scheduler** (`aiagents/ai_scheduler.py`): Intelligent scheduling agent that analyzes stored memories, user preferences, calendar events, and recent interactions to determine optimal timing for the next reminder or user engagement. Prioritizes reliability and respects user preferences while maintaining contextual awareness.

### Memory System

The memory system supports three types of entries:
- **User Preferences**: Settings and preferences (e.g., "User prefers morning reminders")
- **User Observations**: Observations with optional dates (e.g., "User's birthday is 2023-12-15")
- **Reminders**: One-time or recurring reminders with intelligent scheduling options:
  - **One-time Reminders**: Scheduled for a specific datetime (exact timing)
  - **Recurring Reminders**: Scheduled by time of day (HH:MM) with optional days of the week filter (e.g., "09:00 on Monday and Friday")

The AI Scheduler intelligently determines the optimal next interaction time using a dual-approach strategy:
1. **Deterministic Scheduling**: Explicitly scheduled reminders are prioritized to ensure no scheduled reminders are missed
2. **AI-Powered Scheduling**: When no explicit reminders exist, the AI agent analyzes context to suggest optimal timing based on calendar events, user patterns, and preferences
3. **Conflict Resolution**: The scheduler chooses whichever approach results in the earliest suitable next interaction time

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

Yume includes comprehensive interaction tracking to monitor and debug AI agent behavior:
- **Agent Type Tracking**: Records which agent executed the interaction (e.g., ai_scheduler, ai_engine)
- **Input/Output Capture**: Stores full input data and generated output for each interaction
- **Metadata Storage**: Captures interaction metadata including next_run_time and topic for schedulers
- **System Instructions**: Logs the system instructions used by each agent for transparency and debugging
- **Persistent History**: Interaction history is persisted to `data/interactions.json` for analysis

This enables detailed debugging, performance optimization, and understanding of how agents make decisions.

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

Yume automatically manages memories with the following features:

- **Automatic Categorization**: Messages are analyzed and relevant information is stored as preferences, observations, or reminders
- **Intelligent Reminder Scheduling**: Create one-time or recurring reminders with flexible scheduling options
  - Set specific dates and times for one-time reminders
  - Create daily reminders at specific times
  - Schedule recurring reminders for specific days of the week
- **AI-Powered Timing**: The AI Scheduler analyzes calendar events, user preferences, and interaction patterns to determine optimal timing for reminders
- **Smart Reminders**: The system determines optimal timing based on content and user behavior, considering:
  - Upcoming calendar events (schedules reminders 15-30 minutes before meetings)
  - User preferences and communication frequency
  - Recent interactions to avoid repetition
  - Time of day and day of week patterns
- **Background Processing**: Memory updates and scheduling happen asynchronously to maintain fast response times
- **Formatted Retrieval**: Consistent memory formatting across all system components
- **Automatic Cleanup**: The Memory Janitor runs every 12 hours to archive and clean up old memories

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

## AI Scheduler Agent

The AI Scheduler is the intelligent timing engine that determines when Yume should next interact with the user. It uses a sophisticated analysis of memories, calendar events, and user preferences to optimize engagement timing.

### Core Principles

1. **Reliability**: Never misses scheduled reminders or important events. When in doubt, schedules earlier rather than later.
2. **User Preferences**: Always prioritizes and respects stored user preferences about timing and frequency.
3. **Engagement**: Considers the user's emotional state, routine patterns, and recent interactions to provide timely, helpful engagement.
4. **Context Awareness**: Factors in time of day, day of week, recent activity, upcoming calendar events, and seasonal patterns.
5. **Calendar Intelligence**: Schedules interactions at appropriate times before calendar events (15-30 minutes before meetings, morning of all-day events).

### Interaction Priority

The scheduler prioritizes interactions in the following order:

1. **Explicit Reminders** (highest priority): One-time reminders with specific datetime values - NEVER missed
2. **Calendar Event Reminders**: Scheduled 15-30 minutes before timed events or morning of all-day events
3. **Recurring Reminders**: Recurring reminders with time_value and days_of_week patterns
4. **User Preference-Based Check-ins**: Daily summaries, weekly planning, or preference-specified interactions
5. **Contextual Engagement**: Based on user observations and identified patterns
6. **Wellness Check-ins**: Every few hours during active hours if no other interactions are scheduled

### Timing Guidelines

- **Minimum Gap**: At least 15 minutes from current time (only 15 minutes for urgent items)
- **Maximum Gap**: Never more than 4 hours during active hours without some form of check-in
- **Context Sensitivity**: Weekend timing differs from weekday timing
- **Frequency Adaptation**: Respects user preferences for brief frequent check-ins vs. fewer longer interactions

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
├── main.py             # Application entry point
├── services/           # Core business logic
├── aiagents/           # AI-specific modules
├── components/         # Shared components and data models
├── tools/              # Function tools for AI agents
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
