# Yume 🌙

<div align="center">
  <img src="assets/yume.jpg" alt="Yume AI Assistant" width="400" />
</div>

**Yume** (夢 - "dream" in Japanese) is an intelligent AI assistant that integrates with Matrix chat and Home Assistant to provide contextual responses, memory management, automated scheduling capabilities, and location-based triggers.

## Features

- 🤖 **Matrix Chat Integration**: AI-powered responses to messages in Matrix rooms
- 🏠 **Home Assistant Integration**: Location and proximity data integration
- 📅 **Calendar Integration**: iCalDAV-based calendar events and scheduling
- 🌤️ **Weather Integration**: Real-time weather data via OpenWeatherMap
- 📍 **Geofence Events**: Location-based triggers with distance context from proximity sensors
- 🚌 **Public Transport Departures**: Real-time transit information via EFA (Elektronisches Fahrplanauskun ftssystem) API with dynamic station lookup and line/direction filtering
- 🛒 **KitchenOwl Integration**: Manage shopping lists and recipes with intelligent duplicate handling
- 🏃 **Strava Integration**: Automatic cycling activity logging and analysis with webhook support
- 💪 **Garmin Health Metrics**: Daily health insights including training load, sleep quality, and fitness status via Garmin Connect
- 📱 **E-Ink Display Support**: Summarized daily briefings rendered for e-paper displays with optimal readability
- 🧠 **Advanced Memory System**: Persistent storage with preferences, observations, and reminders
- 📅 **AI-Powered Day Planner**: Automatic daily planning based on calendar and memories with high-confidence updates
- ⏰ **Intelligent AI Scheduler**: Context-aware scheduling with deferred execution and adaptive re-evaluation
- 📊 **Vue.js Dashboard**: Real-time monitoring of memories, schedules, plans, and interactions with Strava connection management
- 🔐 **OpenID Connect Authentication**: Secure access to web interface

## Architecture

Yume is built with a modular architecture consisting of several key components:

### Core Services

- **Matrix Bot Service** (`service/matrix/`): Matrix protocol client for chat integration
- **Memory Manager Service** (`service/memory/`): MongoDB-backed persistent storage for user preferences, observations, and reminders
- **Scheduler Service** (`service/scheduler/`): Background task scheduling with Spring's TaskScheduler
- **Context Manager** (`service/`): Aggregates data from multiple sources (Home Assistant, calendar, weather)
- **Home Assistant Service** (`service/provider/`): Integration with Home Assistant API
- **Calendar & Weather Services** (`service/calendar/`, `service/weather/`): External service integrations
- **Conversation Service** (`service/conversation/`): Message history and conversation management
- **Strava Integration Service** (`service/strava/`): OAuth 2.0 authentication and webhook handling for Strava cycling activities
- **Garmin Connect Service** (`service/garminconnect/`): Health metrics fetcher via Model Context Protocol (MCP)
- **E-Ink Display Service** (`service/eink/`): Generates optimized content for e-paper displays

### AI Agents (langchain4j-powered)

- **RequestRouterAgent** (`agent/RequestRouterAgent.kt`): Routes incoming requests to appropriate agents based on context
- **GenericChatAgent** (`agent/GenericChatAgent.kt`): Main conversational AI for handling general interactions
- **MemoryManagerAgent** (`agent/MemoryManagerAgent.kt`): Handles memory operations including intelligent cleanup and archival
- **ConversationSummarizerAgent** (`agent/ConversationSummarizerAgent.kt`): Condenses conversation history into concise, detail-preserving summaries for optimized AI context
- **DayPlanAgent** (`agent/DayPlanAgent.kt`): AI agent that creates daily activity predictions using calendar, memories, and context. Makes high-confidence updates to plans via tools.
- **SchedulerAgent** (`agent/SchedulerAgent.kt`): Intelligent scheduling with deferred execution, automatic re-evaluation, and dual-approach timing optimization (deterministic + AI-powered). Receives execution summaries from scheduled/geofence events for improved future scheduling decisions.
- **EfaAgent** (`agent/EfaAgent.kt`): Specialized agent for querying public transport departures. Parses natural language queries to extract station names, line numbers, and destination directions.
- **KitchenOwlAgent** (`agent/KitchenOwlAgent.kt`): Manages shopping lists and recipes with autonomous decision-making. Intelligently handles duplicate items by checking the list before adding.
- **SportsActivityAgent** (`agent/SportsActivityAgent.kt`): Analyzes cycling activities from Strava, tracks performance metrics, and provides personalized fitness insights. Triggered by Strava webhooks and scheduled events.
- **EInkDisplayAgent** (`agent/EInkDisplayAgent.kt`): Generates concise, visually optimized summaries for e-ink display devices with support for Tailwind CSS styling and responsive layouts.

Event-triggered agent methods (`handleScheduledEvent`, `handleGeofenceEvent`) re-evaluate current context before acting, ensuring actions remain relevant and avoiding unnecessary messages.

### Memory System

The memory system stores three types of entries:
- **User Preferences**: Settings and preferences (e.g., "User prefers morning reminders")
- **User Observations**: Observations with optional dates (e.g., "User's birthday is 2023-12-15")
- **Reminders**: Time-based, recurring, or location-based reminders

Reminders use dual-approach scheduling: deterministic (explicitly scheduled) + AI-powered (pattern-based). The AI Scheduler runs after every interaction with a 60-second debounce.

### Tool Integration

langchain4j-powered tools for AI agents:
- **Memory Tools**: Memory operations (search, CRUD) with MongoDB
- **Day Planner Tools**: Get and update daily plans  
- **Home Assistant Tools**: Smart home control and sensor data
- **EFA Tools**: Public transport departure queries with optional line and direction filtering
- **KitchenOwl Tools**: Shopping list management and recipe access with batch operations
- **Strava Activity Tools**: Fetch recent cycling activities and performance metrics

### Data Management

- **MongoDB Storage**: Persistent storage for memories, conversations, interactions, scheduler runs, and geofence events
- **Spring Cache (Caffeine)**: In-memory caching for frequently accessed data
- **Vector Embeddings**: langchain4j with pgvector for semantic search capabilities

### Components

- **Conversation Models** (`component/conversation/`): Message history data structures
- **Calendar & Weather Models** (`component/calendar/`, `component/weather/`): External service models
- **Timezone Utils** (`utils/`): Timezone-aware datetime handling

### Interaction Tracking

Yume tracks all AI agent interactions and events for debugging:
- **Agent Type**: Records which agent executed the interaction
- **Input/Output**: Stores full data for each interaction
- **Metadata**: Captures scheduling information, topic, and system instructions
- **Scheduler Runs**: Logs scheduled task executions with outcomes for scheduler feedback
- **Geofence Events**: Tracks location-based triggers with execution summaries
- **Storage**: Persisted in MongoDB

## Performance Optimizations

- **Async Background Processing**: Memory updates, summarization, and scheduling run asynchronously using Spring's @Async
- **Conversation Summarization**: Automatically condenses conversation history into optimized summaries after each update, reducing token usage while preserving critical details
- **Efficient Memory Access**: Summarized memory retrieval with consistent formatting; falls back to full memory if summaries unavailable
- **In-Memory Caching**: Caffeine cache for frequently accessed data
- **Vector Search**: langchain4j pgvector integration for semantic search on memories and conversations

## Installation

### Prerequisites

- Java 21 or later
- Spring Boot 3.5+
- MongoDB instance (local or cloud)
- Matrix account and room
- Home Assistant instance
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd yume
   ```

2. **Build the project**
   ```bash
   cd yume-spring
   ./gradlew build
   ```

3. **Configure application properties**
   
   All configuration is managed through Spring Boot's `application.properties` file located at `yume-spring/src/main/resources/application.properties`.

   Review the configuration file and fill in all required properties for your environment:
   - Matrix bot credentials and connection details
   - MongoDB connection settings
   - OpenAI API key and model configuration
   - Home Assistant integration (if applicable)
   - KitchenOwl integration (if applicable)
   - EFA public transport API settings
   - OIDC authentication provider settings
   - Basic Auth credentials for webhook endpoints

   For Docker deployments, you can override properties using environment variables. Property names follow Spring's convention: replace dots with underscores and uppercase (e.g., `matrix.homeserver` → `MATRIX_HOMESERVER`).

## Usage

### Running the Application

#### From command line:
```bash
cd yume-spring
./gradlew bootRun
```

#### With Docker:
```bash
docker-compose up
```

The application will start:
- Spring Boot server on `http://0.0.0.0:8080`
- Nginx on port 8079 serving the Vue.js frontend
- Matrix bot connecting to your configured room
- AI scheduler with automatic memory management
- Background processing for optimal performance

### Authentication

Yume uses OpenID Connect (OIDC) authentication to secure the web interface. Configure your OIDC provider details in the application properties.

### Memory Management

- **Automatic Categorization**: Messages analyzed and stored as preferences, observations, or reminders
- **Intelligent Reminder Scheduling**: One-time, recurring, or location-based reminders with adaptive scheduling
- **Adaptive Scheduling**: Re-evaluates when new interactions occur (chat, geofence, or reminder)
- **Automatic Cleanup**: Memory Janitor runs once a day to archive and clean up old entries
- **Conversation Summarization**: After each conversation update, an AI summarizer automatically:
  - Condenses conversation history into concise summaries
  - Preserves all critical details while removing redundancy
  - Reduces token usage by providing condensed conversation representations

#### Geofence Webhook

Home Assistant can trigger geofence events via the `/api/webhook/geofence-event` endpoint:

```bash
# Example: User enters home location
curl -X POST http://localhost:8079/webhook/geofence-event \
  -u "homeassistant:your_password" \
  -H "Content-Type: application/json" \
  -d '{
    "geofenceName": "Home", 
    "eventType": "enter"
  }'

# Example: User leaves work location  
curl -X POST http://localhost:8079/webhook/geofence-event \
  -u "homeassistant:your_password" \
  -H "Content-Type: application/json" \
  -d '{
    "geofenceName": "Office", 
    "eventType": "leave"
  }'
```

**Home Assistant Automation Example:**

```yaml
automation:
  - alias: "Yume Geofence Notification"
    trigger:
      - platform: zone
        entity_id: device_tracker.phone
        zone: zone.home
        event: enter
    action:
      - service: rest_command.yume_geofence
        data:
          geofence_name: "Home"
          event_type: "enter"

rest_command:
  yume_geofence:
    url: "http://your-yume-server:8079/api/webhook/geofence-event"
    method: POST
    headers:
      Authorization: "Basic {{ 'homeassistant:your_password' | base64_encode }}"
      Content-Type: "application/json"
    payload: '{"geofenceName": "{{ geofence_name }}", "eventType": "{{ event_type }}"}'
```

The API validates that `eventType` is either "enter" or "leave" and returns a response indicating success or failure along with any AI-generated message.

#### Strava Integration

Yume can automatically fetch and analyze your Strava cycling activities through webhook integration:

**Setup:**

1. Configure Strava OAuth credentials in `application.properties`:
   ```properties
   yume.strava.enabled=true
   yume.strava.client-id=YOUR_CLIENT_ID
   yume.strava.client-secret=YOUR_CLIENT_SECRET
   yume.strava.webhook-verify-token=YOUR_VERIFY_TOKEN
   yume.strava.webhook-url=http://your-yume-server:8079/api/strava/webhook
   yume.strava.oauth-redirect-url=http://localhost:3000/api/strava/oauth/callback
   ```

2. Connect your Strava account via the web dashboard (Preferences → Strava Integration)

3. Yume will automatically register webhooks with Strava for activity creation events

**Features:**
- Automatic cycling activity logging and analysis
- Activity performance metrics (distance, duration, elevation, power, heart rate)
- AI-powered fitness insights and personalized feedback
- Strava connection management in the web dashboard
- Webhook endpoint: `POST /api/strava/webhook`

#### Garmin Connect Integration

Yume fetches daily health metrics from Garmin Connect via Model Context Protocol (MCP):

**Setup:**

1. Configure Garmin MCP server URL in `application.properties`:
   ```properties
   yume.garmin-connect.mcp-server-url=http://localhost:60380
   ```

2. Ensure the Garmin Connect MCP server is running and authenticated

**Health Metrics Provided:**
- **Training Balance**: Daily training load feedback and balance status
- **Training Status**: Current training condition and acute training load
- **Sleep Quality**: Sleep score, duration, stages (deep/light/REM), and nap data with timestamps
- **Daily Activity**: Step count, intensity minutes, and body battery measurements
- **Heart Rate Variability**: HRV status for recovery assessment

These metrics are automatically populated into the user context for memory management and scheduling decisions.

#### E-Ink Display Endpoint

Yume generates optimized summaries for e-ink display devices:

**Endpoint:** `GET /api/e-ink-display/content` (produces `text/plain`)

**Response Format:** Plain HTML with Tailwind CSS styling, optimized for small, low-resolution displays

**Features:**
- Automatic content compilation from multiple sources:
  - Current date/time
  - User preferences and language
  - Weather forecast
  - Today's and tomorrow's day plan
  - User observations and preferences summary
- AI-powered text generation with formatting rules:
  - Maximum 5-7 lines of text for readability from 1 meter distance
  - black & white only (no colors or shades)
  - Natural language date/time formatting
  - Concise, high-priority information only
  - Long-term relevance (no real-time updates)

**Integration Example** (for e-ink display device):

```bash
# Fetch display content periodically (e.g., update once or twice daily)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8079/api/e-ink-display/content
```

The response is ready-to-render HTML that your e-ink device can display immediately.

### Vue.js Dashboard

Access at `http://localhost:8079` to monitor:

- **Memory Store**: All stored memories with type, timestamps, and reminder details
- **Day Planner**: Calendar-based daily activity predictions with navigation
- **Scheduled Tasks**: Next scheduled memory reminders
- **Interaction Details**: Debugging view of agent interactions with input/output/instructions
- **System Logs**: Real-time logs with level filtering

### Docker Deployment

The project includes a multi-stage Dockerfile that builds both the Vue.js frontend and Spring Boot backend:

```bash
# Build the image
docker build -t yume .

# Run with automatic volume for data persistence
docker run -d --name yume -p 8079:8079 --env-file .env yume

# Or use docker-compose
docker-compose up -d

# View logs
docker logs -f yume
```

**Note**: MongoDB must be accessible from the container. Configure `SPRING_DATA_MONGODB_URI` to point to your MongoDB instance.

## Configuration

Configuration can be set via environment variables or `application.properties`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Spring Boot 3.5+
- langchain4j for AI agent orchestration
- Trixnity for Matrix protocol support
- Vue.js for the frontend dashboard
- Nginx as reverse proxy and static file server
- OpenWeatherMap for weather data
