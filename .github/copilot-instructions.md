# Yume Project - Copilot Instructions

## Project Overview

**Yume** (夢 - "dream" in Japanese) is an AI-powered personal assistant that integrates Matrix chat, Home Assistant, calendar events, public transport, and shopping list management. It features advanced memory management, intelligent scheduling, location-based triggers, and an AI agent architecture powered by langchain4j.

**Project Type**: Full-stack application (Spring Boot backend + Vue.js frontend)
**Size**: Medium (~3K lines Kotlin, ~500 lines Vue.js)
**Languages**: Kotlin, Vue.js, TypeScript
**Runtime**: Java 21, Node 24
**Frameworks**: Spring Boot 3.5.9, langchain4j 1.10.0, Trixnity (Matrix), Vite 5

## Build & Test Commands

### Prerequisites
- **Java 21 or later** (required for Kotlin 2.2.21 and Spring Boot 3.5.9)
- **Gradle 9.0.0** (via wrapper, no installation needed)
- **Node.js 24** (for frontend, or any version compatible with Vite 5)
- **MongoDB** (local or containerized)
- **PostgreSQL with pgvector** (for embeddings)

### Backend (Spring Boot / Kotlin)

**Location**: `yume-spring/` directory

**Build Steps** (in order):
```bash
cd yume-spring
./gradlew clean build --no-daemon
```
- **Always run `clean build` together** to avoid stale class files
- Use `--no-daemon` flag to avoid Gradle daemon memory issues
- Build time: ~30-60 seconds (first build may take longer for dependency download)
- Output: `yume-spring/build/libs/yume-0.0.1-SNAPSHOT.jar`

**Run Tests**:
```bash
cd yume-spring
./gradlew test --no-daemon
```
- Tests are JUnit 5-based with MockK for mocking
- Test files: `src/test/kotlin/eu/sendzik/yume/`
- Known tests: YumeApplicationTests, CalendarServiceTest, EfaToolsIntegrationTest

**Run Application**:
```bash
cd yume-spring
./gradlew bootRun
```
- Runs on `http://localhost:8079/api` (context path: `/api`)
- **Requires configuration**: Must have `application.properties` filled with API keys and credentials
- **Environment variables override properties**: Use `SPRING_DATA_MONGODB_HOST`, `LANGCHAIN4J_OPEN_AI_CHAT_MODEL_API_KEY`, etc.

**Check Version**:
```bash
cd yume-spring
./gradlew --version  # Shows Gradle 9.0.0 and Java 21
```

### Frontend (Vue.js / Vite)

**Location**: `ui/` directory

**Build Steps** (in order):
```bash
cd ui
npm install  # Always run before build if node_modules/ missing or package.json changed
npm run build
```
- **Always run `npm install` after pulling changes or modifying `package.json`**
- Build output: `ui/dist/` directory
- Build time: ~10-20 seconds
- Uses Vite 5 with Vue 3.4

**Development Server**:
```bash
cd ui
npm run dev
```
- Runs on `http://localhost:3000`
- Proxies `/api` requests to `http://localhost:8079`

**Preview Production Build**:
```bash
cd ui
npm run preview
```

### Docker

**Build Container** (multi-stage build):
```bash
docker build -t yume .
```
- Builds frontend (Node 24), backend (Gradle 8.5 + JDK 21), and packages with Nginx
- Build time: ~3-5 minutes
- Platforms: `linux/amd64` (specified in CI)

**Run with Docker Compose**:
```bash
docker-compose up -d  # Starts MongoDB, PostgreSQL, and optionally Yume
```
- **Note**: The main app is NOT in docker-compose.yml by default (only dependencies)
- MongoDB on `localhost:27017`
- PostgreSQL (pgvector) on `localhost:5432`

**Run Standalone Container**:
```bash
docker run -d --name yume -p 8079:8079 --env-file .env yume
```
- Requires `.env` file with all configuration variables
- Nginx serves frontend on port 8079, proxies `/api` to Spring Boot on port 8080

## Project Structure

### Root Directory Files
- `README.md` - Comprehensive project documentation
- `docker-compose.yml` - MongoDB 8.2 + PostgreSQL 18 with pgvector
- `Dockerfile` - Multi-stage build (Node 24 → Gradle 8.5 → Eclipse Temurin 21)
- `nginx.conf` - Reverse proxy config (serves frontend, proxies /api)
- `LICENSE` - MIT License
- `.gitignore` - Excludes build/, dist/, node_modules/, .env, .idea/, .vscode/

### Backend Architecture (`yume-spring/`)

**Main Application**: `src/main/kotlin/eu/sendzik/yume/YumeApplication.kt`
- Entry point with `@SpringBootApplication`, `@EnableScheduling`, `@EnableAsync`

**Configuration**: `src/main/resources/application.properties`
- 100+ lines of config (OpenAI API keys, Matrix credentials, MongoDB, PostgreSQL, Home Assistant, Calendar, etc.)
- **CRITICAL**: Most properties are empty and MUST be filled for the app to work
- See lines 1-101 for complete list of required settings

**Package Structure**:
- `agent/` - AI agents (RequestRouterAgent, GenericChatAgent, MemoryManagerAgent, SchedulerAgent, DayPlanAgent, EfaAgent, KitchenOwlAgent, ConversationSummarizerAgent, MemorySummarizerAgent, EInkDisplayAgent)
- `service/` - Business logic (matrix/, memory/, scheduler/, dayplan/, conversation/, calendar/, weather/, efa/, kitchenowl/, provider/, interaction/, location/, router/, eink/)
- `tool/` - langchain4j tools (MemoryManagerTools, DayPlanTools, EfaTools, KitchenOwlTools, KitchenOwlReadTools)
- `component/` - Data models (conversation/, calendar/, weather/)
- `controller/` - REST endpoints (webhook handlers)
- `repository/` - MongoDB repositories (memory/)
- `configuration/` - Spring configuration classes
- `converter/` - Data converters
- `client/` - External API clients
- `utils/` - Utility classes (timezone handling)

**Key Dependencies** (from `build.gradle.kts`):
- Spring Boot 3.5.9 (web, data-mongodb, oauth2-resource-server, cache)
- Kotlin 2.2.21 (with serialization)
- langchain4j 1.10.0-beta18 (OpenAI, pgvector, Kotlin extensions)
- Trixnity 4.22.7 (Matrix client)
- Ktor 3.3.3 (HTTP client for Matrix)
- caldav4j 1.0.5 (calendar integration)
- Caffeine 3.2.3 (caching)
- MockK 1.14.7 (testing)

**Gradle Configuration**:
- Java toolchain: Java 21
- Kotlin compiler: JSR-305 strict mode, Java parameters enabled
- Test platform: JUnit 5

### Frontend Architecture (`ui/`)

**Entry Point**: `index.html` → `src/main.js` → `src/App.vue`

**Components** (`src/components/`):
- ActionItem.vue, DayPlanner.vue, DayPlannerItem.vue, InteractionDetailModal.vue, InteractionItem.vue, MemoryItem.vue, RefreshButton.vue, SchedulerRunItem.vue, SchedulerRunsPanel.vue, Section.vue, TaskItem.vue

**Services** (`src/services/`):
- `api.js` - Axios-based API client for backend communication

**Utils** (`src/utils/`):
- `formatters.js` - Date/time formatting utilities

**Vite Config** (`vite.config.js`):
- Dev server on port 3000
- Proxies `/api` to `http://localhost:8079`
- Build output: `dist/` directory

**Dependencies** (`package.json`):
- Vue 3.4.38
- Axios 1.12.2
- Vite 5.4.3

### Resource Files (`yume-spring/src/main/resources/`)

**Prompt Templates** (`prompt/` directory):
- 15+ system/user message templates for AI agents
- Examples: `chat-interaction-system-message.txt`, `memory-manager-system-message.txt`, `day-plan-system-message.txt`, `efa-system-message.txt`, `kitchenowl-system-message.txt`, `scheduler-system-message.txt`

**Configuration Files**:
- `application.properties` - Main Spring Boot configuration (101 lines)
- `ical4j.properties` - Calendar library settings

## CI/CD Pipeline

**GitHub Actions Workflow**: `.github/workflows/docker-build.yml`
- **Trigger**: Push to `main` branch, pull requests to `main`
- **Steps**:
  1. Checkout repository
  2. Login to GitHub Container Registry (ghcr.io)
  3. Extract metadata (tags: branch, PR, sha, latest)
  4. Set up Docker Buildx
  5. Build and push Docker image
- **Platform**: `linux/amd64` only
- **Cache**: GitHub Actions cache (`type=gha`)
- **Registry**: `ghcr.io/${{ github.repository }}`

**No automated tests run in CI** - only Docker build validation

## Configuration Requirements

**MUST be configured before running**:
1. **OpenAI API** (`langchain4j.open-ai.chat-model.api-key` and `base-url`)
2. **MongoDB** (host, port, database - defaults to localhost:27017)
3. **PostgreSQL pgvector** (host, port, database, username, password)
4. **Matrix Bot** (homeserver URL, room ID, user ID, password)
5. **OAuth2/OIDC** (issuer URI for web authentication)
6. **Basic Auth** (webhook username/password for Home Assistant integration)

**Optional but commonly used**:
- Home Assistant (API URL and token)
- Calendar (iCalDAV URL, username, password)
- KitchenOwl (API URL, key, household ID)
- OpenWeatherMap (API key)
- EFA public transport (API URL)
- Location coordinates (home latitude/longitude)

## Known Issues & Workarounds

### TODOs in Codebase
1. **InteractionTrackerService.kt:100** - Failed interactions are not tracked yet
2. **MemoryManagerAgent.kt:20** - Memory retrieval passes all memories instead of filtering (planned migration to knowledge graph)
3. **DayPlanExecutorService.kt:57** - Weather forecast for specific days not yet implemented via tool
4. **RagMemoryRepository.kt:148** - More fields needed in repository

### Common Errors
- **Missing configuration**: App fails to start with NullPointerException if API keys/credentials are missing → Fill `application.properties` or set environment variables
- **MongoDB connection failed**: Ensure MongoDB is running on configured host/port
- **PostgreSQL connection failed**: Ensure PostgreSQL with pgvector extension is accessible
- **Matrix connection timeout**: Verify homeserver URL and network connectivity

### Docker-Specific
- **MongoDB must be externally accessible**: The Dockerfile doesn't include MongoDB, must be configured via `SPRING_DATA_MONGODB_HOST` env var
- **Nginx and Spring Boot run together**: Uses `tini` as init system, runs both processes with `wait -n` (exits if either dies)
- **Build requires Docker Buildx**: For multi-platform support and caching

## Development Guidelines

### Making Changes

**Kotlin/Spring Boot**:
1. Edit files in `yume-spring/src/main/kotlin/eu/sendzik/yume/`
2. For new agents: Extend appropriate base class, add to `agent/` package
3. For new tools: Implement in `tool/` package, annotate with `@Tool`
4. For new services: Add to `service/` package, inject dependencies
5. Always clean build: `./gradlew clean build --no-daemon`
6. Run tests: `./gradlew test --no-daemon`

**Vue.js/Frontend**:
1. Edit files in `ui/src/`
2. Components go in `ui/src/components/`
3. Always run `npm install` if dependencies change
4. Build with `npm run build` before testing in production mode
5. Test locally with `npm run dev`

**Configuration Changes**:
- Add new properties to `application.properties`
- Document required vs optional settings
- Use Spring Boot's `@ConfigurationProperties` for type-safe config

**Docker Changes**:
- Update `Dockerfile` for build process changes
- Update `nginx.conf` for routing changes
- Test with `docker build -t yume .` before committing

### Testing
- Backend tests use JUnit 5 + MockK
- No frontend tests currently configured
- Manual testing: Run app with `./gradlew bootRun` and verify in browser at `http://localhost:8079`

### Code Style
- Kotlin: Follow Kotlin conventions (camelCase, no semicolons)
- Vue.js: Follow Vue 3 Composition API conventions
- Indentation: Use IDE defaults (IntelliJ IDEA for Kotlin, VS Code for Vue.js)

## Important Notes for Agents

1. **Trust these instructions**: Only search for additional information if these instructions are incomplete or incorrect
2. **Always clean build**: Run `./gradlew clean build` together to avoid stale artifacts
3. **Check configuration**: Most runtime errors are due to missing config in `application.properties`
4. **MongoDB/PostgreSQL required**: Cannot run app without these dependencies
5. **Multi-module project**: Backend is in `yume-spring/`, frontend in `ui/`, root has Docker configs
6. **Environment variables**: Any property can be overridden with env vars (dots → underscores, uppercase)
7. **Gradle wrapper**: Always use `./gradlew`, not `gradle` (ensures version consistency)
8. **No shell scripts**: All build/test/run commands are Gradle tasks or npm scripts
9. **Docker multi-stage**: Full build happens in container (Node → Gradle → Runtime)
10. **Port 8079**: Unified port for Nginx (frontend + API proxy), Spring Boot internally on 8080

## Quick Reference

**Build everything**:
```bash
cd yume-spring && ./gradlew clean build --no-daemon
cd ../ui && npm install && npm run build
```

**Run locally** (with external MongoDB/PostgreSQL):
```bash
cd yume-spring && ./gradlew bootRun
# In another terminal:
cd ui && npm run dev
```

**Run with Docker**:
```bash
docker-compose up -d  # Start dependencies
docker build -t yume .
docker run -d -p 8079:8079 --env-file .env yume
```

**Check CI compliance**:
```bash
docker build -t yume .  # Should succeed without errors
```
