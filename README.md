# Yume 🌙

**Yume** (夢 - "dream" in Japanese) is an intelligent AI assistant that integrates with Matrix chat and Home Assistant to provide contextual responses, memory management, and automated scheduling capabilities.

## Features

- 🤖 **Matrix Chat Integration**: Responds to messages in Matrix rooms with AI-powered responses
- 🏠 **Home Assistant Integration**: Fetches weather forecasts, calendar events, and user location data
- 🧠 **Memory Management**: Persistent memory system with automatic cleanup and reminders
- ⏰ **Smart Scheduling**: Automated memory reminders and maintenance tasks
- 🌐 **Context-Aware**: Combines conversation history, weather, calendar, and location data for intelligent responses
- 📊 **FastAPI Web Interface**: RESTful API for monitoring and control

## Architecture

Yume is built with a modular architecture consisting of several key components:

### Core Services

- **AI Engine** (`services/ai_engine.py`): Central intelligence using OpenAI Agents framework
- **Matrix Bot** (`services/matrix_bot.py`): Matrix protocol client for chat integration
- **AI Scheduler** (`services/ai_scheduler.py`): Background task scheduling with APScheduler
- **Context Manager** (`services/context_manager.py`): Aggregates data from multiple sources into unified context
- **Memory Manager** (`services/memory_manager.py`): Persistent memory storage and retrieval
- **Home Assistant** (`services/home_assistant.py`): Integration with Home Assistant API

### AI Agents

- **Answer Machine** (`aiagents/answer_machine.py`): Generates contextual responses
- **Memory Manager** (`aiagents/memory_manager.py`): Handles memory operations and cleanup

### Components

- **Conversation** (`components/conversation.py`): Message history data structures
- **Calendar & Weather** (`components/calendar.py`, `components/weather.py`): Data models for external services
- **Logging Manager** (`components/logging_manager.py`): Centralized logging system

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

### Docker Deployment

```bash
# Build the image
docker build -t yume .

# Run with environment variables
docker run -d --name yume \
  --env-file .env \
  -p 8200:8200 \
  yume
```

## Key Features Explained

### Context-Aware Responses

Yume builds comprehensive context from multiple sources:
- **Recent conversation history** from Matrix chat
- **Weather forecasts** for the next 24 hours
- **Calendar events** for the next 48 hours  
- **User location** from device tracker
- **Current date and time**

This context is automatically included in AI responses to provide more relevant and helpful answers.

### Memory System

- **Automatic Memory Reminders**: Scheduled 15 minutes after startup and can be rescheduled based on AI decisions
- **Memory Janitor**: Runs every 12 hours to clean up old or irrelevant memories
- **Persistent Storage**: Memories are stored and retrieved across sessions

### Smart Scheduling

The AI scheduler manages:
- One-time memory reminder tasks
- Recurring memory maintenance (every 12 hours)
- Custom scheduled events based on AI decisions

## API Endpoints

The FastAPI application provides a web interface at `http://localhost:8200` with automatic API documentation available at `/docs`.

## Configuration

### Matrix Setup

1. Create a Matrix account for your bot
2. Join the bot to your desired room
3. Get the room ID (usually starts with `!`)
4. Configure the environment variables

### Home Assistant Setup

1. Create a Long-Lived Access Token in Home Assistant
2. Configure entity IDs for:
   - Device tracker (for location)
   - Weather service
   - Calendar integration
3. Set your timezone for proper date/time handling

## Development

### Project Structure

```
yume/
├── main.py                 # Application entry point
├── services/               # Core services
├── aiagents/              # AI agent implementations  
├── components/            # Reusable components
├── tools/                 # Utility tools
└── data/                  # Data storage
```

### Adding New Features

1. **New AI Agents**: Add to `aiagents/` directory
2. **External Integrations**: Add to `services/` directory
3. **Data Models**: Add to `components/` directory
4. **Utility Functions**: Add to `tools/` directory

## Troubleshooting

### Common Issues

1. **Matrix Connection Failed**
   - Verify homeserver URL and credentials
   - Check network connectivity
   - Ensure bot account has proper permissions

2. **Home Assistant Integration Issues**
   - Verify HA_URL and HA_TOKEN
   - Check entity IDs exist in your Home Assistant instance
   - Ensure Home Assistant is accessible from Yume

3. **Memory Issues**
   - Check file permissions in data directory
   - Verify disk space availability
   - Review memory janitor logs

### Logging

Yume uses comprehensive logging. Check the console output for detailed information about:
- Service startup and shutdown
- Message processing
- API calls to external services
- Scheduled task execution
- Error conditions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [OpenAI Agents](https://github.com/pydantic/openai-agents) framework
- Uses [matrix-nio](https://github.com/poljar/matrix-nio) for Matrix protocol support
- Powered by [FastAPI](https://fastapi.tiangolo.com/) for the web interface
- Scheduling provided by [APScheduler](https://apscheduler.readthedocs.io/)
