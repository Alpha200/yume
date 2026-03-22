# AGENTS.md — Yume Project

**Yume** (夢, "dream") is an AI-powered personal assistant. Spring Boot (Kotlin) backend + Vue.js frontend in a monorepo.

---

## Build & Test Commands

### Backend — `yume-spring/`

```bash
# Full build (always run clean + build together)
cd yume-spring && ./gradlew clean build --no-daemon

# Run all tests
cd yume-spring && ./gradlew test --no-daemon

# Run a single test class
cd yume-spring && ./gradlew test --tests "eu.sendzik.yume.service.calendar.CalendarServiceTest" --no-daemon

# Run a single test method (use full class path + method name)
cd yume-spring && ./gradlew test --tests "eu.sendzik.yume.tool.EfaToolsIntegrationTest.test get station departures" --no-daemon

# Run all tests in a package
cd yume-spring && ./gradlew test --tests "eu.sendzik.yume.service.*" --no-daemon

# Run application
cd yume-spring && ./gradlew bootRun
```

- Always use `./gradlew` (wrapper), never bare `gradle`
- Always add `--no-daemon` to avoid daemon memory issues
- Build output: `yume-spring/build/libs/yume-0.0.1-SNAPSHOT.jar`
- App runs on `http://localhost:8079/api` (context path: `/api`)
- **Requires `application.properties`** with API keys/credentials to start

### Frontend — `ui/`

```bash
npm install        # Run after pulling changes or modifying package.json
npm run build      # Production build → ui/dist/
npm run dev        # Dev server on http://localhost:3000 (proxies /api → http://localhost:8079)
npm run preview    # Preview production build
```

No lint or test scripts are configured on the frontend.

### Docker

```bash
docker build -t yume .              # Multi-stage: Node 24 → Gradle/JDK21 → Temurin 21 + Nginx
docker-compose up -d                # Start MongoDB 8.2 + PostgreSQL 18 (pgvector) dependencies
docker run -d -p 8079:8079 --env-file .env yume
```

---

## Project Structure

```
yume/
├── yume-spring/          # Spring Boot / Kotlin backend
│   └── src/main/kotlin/eu/sendzik/yume/
│       ├── agent/        # langchain4j AI agent interfaces
│       ├── service/      # Business logic (memory, scheduler, calendar, strava, etc.)
│       ├── tool/         # @Tool implementations for AI agents
│       ├── controller/   # REST controllers
│       ├── repository/   # MongoDB + pgvector repositories
│       ├── configuration/
│       ├── client/       # External HTTP clients
│       └── component/    # Cross-cutting components (JWT, logging)
├── ui/                   # Vue.js 3 frontend
│   └── src/
│       ├── components/   # Reusable UI components
│       ├── pages/        # Route-level page components
│       ├── services/     # api.js (Axios + PKCE OAuth2)
│       └── utils/        # formatters.js
├── Dockerfile
├── docker-compose.yml
└── nginx.conf
```

---

## Kotlin Code Style

### Naming

- Classes/interfaces: `PascalCase`
- Functions/properties: `camelCase`
- Constants/enum values: `SCREAMING_SNAKE_CASE`
- Test methods: backtick-quoted descriptive strings — `` `test get calendar entries` ``
- Packages: all-lowercase with dots (`eu.sendzik.yume.service.memory`)
- One public class per file, filename matches class name

### Error Handling — `runCatching` is canonical

```kotlin
// Always use runCatching — never manually wrap Result.success/failure
// ❌ Wrong:
try { Result.success(doSomething()) } catch (e: Exception) { Result.failure(e) }

// ✅ Correct:
runCatching { doSomething() }

// Chain combinators — never check result.isSuccess imperatively
runCatching { fetch() }
    .onFailure { e -> logger.error(e) { "Failed: ${e.message}" } }
    .getOrElse { "Error: ${it.message}" }

// For String-returning @Tool methods:
fun getThing(): String = runCatching {
    // happy path
}.getOrElse {
    logger.error(it) { "Error in getThing" }
    "Error: ${it.message}"
}
```

### String Building

Use `buildString { appendLine(...) }` — never string concatenation with `+` for multi-line LLM context strings.

```kotlin
// ✅ Correct:
buildString {
    appendLine("Header")
    items.forEach { appendLine("- $it") }
}
```

### Dependency Injection

Constructor injection universally. `KLogger` is injected as a Spring prototype bean — no companion objects or static loggers.

```kotlin
@Service
class MyService(private val logger: KLogger, private val otherService: OtherService)
```

Logging uses lambda syntax: `logger.info { "message $var" }`. Exceptions always as first arg: `logger.error(e) { "message" }`.

### Spring Annotations

- `@Service`, `@Repository`, `@Component`, `@Configuration`, `@RestController` on classes
- `@Bean`, `@PostConstruct`, `@Scheduled`, `@Async`, `@Cacheable` on methods
- `@ConfigurationProperties` for grouped config — avoid `@Value` for grouped settings
- `@AiService` on agent interfaces; `@SystemMessage(fromResource = "prompt/...")` for prompt templates
- `@Tool` on tool methods; `@P` to document parameters for the LLM; return type always `String`

### Data Modeling

- `data class` for value objects
- `sealed class` for polymorphic domain hierarchies
- Agent result types use plain `open class` (not data class) to allow subclassing
- All agent results include consistent fields: `messageToUser`, `reasoning`, `executionSummary`, optional `memoryUpdateTask`, `dayPlannerUpdateTask`

### Kotlin Idioms

- Null safety: `?.let { }`, `?:`, `.isNullOrBlank()`, `.orElse(null)` for Java Optional bridging
- Collections: `.joinToString`, `.filterIsInstance<T>()`, `.mapNotNull`, `.groupBy`, `.chunked`, `.asSequence()`
- Thread safety: `ReentrantLock` with `kotlin.concurrent.withLock`
- `runBlocking { }` when blocking on suspend functions from non-coroutine context

---

## Vue.js Code Style

### Component API Style

Use **Options API exclusively** — no Composition API (`setup()`, `ref`, `reactive`).

```js
export default {
  name: 'MyComponent',
  components: { SubComponent },
  props: { item: { type: Object, required: true } },
  data() { return { loading: false, error: null } },
  async mounted() { await this.loadData() },
  methods: {
    async loadData() {
      try { /* ... */ } catch (e) { this.error = e.message }
    }
  }
}
```

### Architecture: Pages vs. Components

- **Pages** (`pages/`) fetch data via `apiService`, manage `loading`/`error` state, load in `mounted()`
- **Components** (`components/`) receive data via props and render — no direct API calls
- All list-based pages use `Section.vue` wrapper (handles loading, empty state, refresh)
- No Vuex/Pinia — state is local to each page; auth state lives in `App.vue` + `localStorage`

### Styling

- **Tailwind CSS utilities only** — no `<style>` blocks, no scoped CSS
- **DaisyUI components** for UI elements: `card`, `btn`, `alert`, `badge`, `modal`, `collapse`, `navbar`, `tabs`, `stat`
- **Mobile-first**: design for mobile first, use responsive prefixes (`sm:`, `md:`, `lg:`) to enhance
- Active Dracula dark theme defined in `ui/src/style.css` with OKLCH tokens

### Imports

```js
import { apiService } from '../services/api'       // API client first
import MyComponent from '../components/MyComponent.vue'  // Then components
import { formatDate } from '../utils/formatters'    // Then utilities
```

Relative imports only. Props typed (`type: Object`) with `required: true` or `default`.

---

## Testing

- **Framework**: JUnit 5 + MockK (`@ExtendWith(MockKExtension::class)`)
- **Assertions**: AssertJ (`assertThat(...)`) or JUnit 5 (`Assertions.*`)
- **Test location**: `yume-spring/src/test/kotlin/eu/sendzik/yume/` (mirrors main tree)
- **Naming**: `<ClassName>Test.kt`; test methods use backtick-quoted descriptive strings
- `CalendarServiceTest` is `@Disabled` (requires live CalDAV); `EfaToolsIntegrationTest` hits real external API
- No frontend tests configured

---

## Key Notes for Agents

1. **Always `clean build`** — run `./gradlew clean build` together to avoid stale class files
2. **`./gradlew` only** — never use bare `gradle`
3. **Configuration required** — app fails without `application.properties` credentials (MongoDB, PostgreSQL, OpenAI API key, Matrix)
4. **Prompt templates** live in `yume-spring/src/main/resources/prompt/` as `.txt` files — keep logic out of source
5. **`runCatching` is mandatory** — do not use manual `try { Result.success(...) } catch`
6. **`buildString` for multi-line strings** — never `+` concatenation for LLM context
7. **No linting tooling** — style maintained by convention (IntelliJ for Kotlin, VS Code for Vue.js)
8. **Port 8079** — Nginx serves frontend + proxies `/api` to Spring Boot on internal port 8080
9. **Environment variables** override any property (dots → underscores, uppercase): e.g., `LANGCHAIN4J_OPEN_AI_CHAT_MODEL_API_KEY`
10. **New agents**: `interface` in `agent/`, annotated `@AiService`, prompt loaded from `prompt/*.txt`
11. **New tools**: `@Component` class in `tool/`, methods annotated `@Tool`, always return `String`, always use `runCatching`
