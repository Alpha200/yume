<template>
  <div class="container">
    <div class="header">
      <h1>🌙 Yume Dashboard</h1>
      <p>AI Actions & Memory Management</p>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <!-- Tabs Navigation -->
    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'memories' }"
        @click="switchTab('memories')"
      >
        🧠 Memory Store
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'actions' }"
        @click="switchTab('actions')"
      >
        ⚡ AI Actions
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'logs' }"
        @click="switchTab('logs')"
      >
        📋 System Logs
      </button>
    </div>

    <!-- Memory Section -->
    <div v-if="activeTab === 'memories'" class="section">
      <div class="section-header">
        <h2>🧠 Memory Store</h2>
        <button
          class="refresh-btn"
          @click="loadMemories"
          :disabled="loadingMemories"
          title="Refresh memories"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
            <path d="M3 21v-5h5"/>
          </svg>
        </button>
      </div>
      <div class="section-content">
        <div v-if="loadingMemories" class="loading">
          Loading memories...
        </div>
        <div v-else-if="memories.length === 0" class="empty">
          No memories stored yet
        </div>
        <div v-else>
          <div
            v-for="memory in memories"
            :key="memory.id"
            class="item memory-item"
          >
            <div class="memory-header">
              <div class="memory-content">{{ memory.content }}</div>
              <div class="memory-type" :class="memory.type">
                {{ formatMemoryType(memory.type) }}
              </div>
            </div>
            <div class="memory-meta">
              <div v-if="memory.place">📍 {{ memory.place }}</div>
              <div>🕒 Created: {{ formatTime(memory.created_at) }}</div>
              <div v-if="memory.observation_date">👁️ Observed: {{ formatTime(memory.observation_date) }}</div>
              <div v-if="memory.reminder_options">
                🔔
                <span v-if="memory.reminder_options.datetime_value">
                  Remind at: {{ formatTime(memory.reminder_options.datetime_value) }}
                </span>
                <span v-if="memory.reminder_options.time_value">
                  Daily at: {{ memory.reminder_options.time_value }}
                </span>
                <span v-if="memory.reminder_options.days_of_week">
                  Days: {{ memory.reminder_options.days_of_week.join(', ') }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Actions Section -->
    <div v-if="activeTab === 'actions'">
      <!-- Scheduled Tasks Section -->
      <div class="section">
        <div class="section-header">
          <h2>📅 Next Scheduled Tasks</h2>
          <button
            class="refresh-btn"
            @click="loadScheduledTasks"
            :disabled="loadingScheduledTasks"
            title="Refresh scheduled tasks"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M3 21v-5h5"/>
            </svg>
          </button>
        </div>
        <div class="section-content">
          <div v-if="loadingScheduledTasks" class="loading">
            Loading scheduled tasks...
          </div>
          <div v-else-if="scheduledTasks.length === 0" class="empty">
            No scheduled tasks
          </div>
          <div v-else>
            <div
              v-for="task in scheduledTasks"
              :key="task.id"
              class="item task-item"
            >
              <div class="task-header">
                <div class="task-name">{{ task.name }}</div>
                <div class="task-time">{{ formatTime(task.next_run_time) }}</div>
              </div>
              <div class="task-description">{{ task.description }}</div>
              <div v-if="task.topic" class="task-reason">Topic: {{ task.topic }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent AI Actions Section -->
      <div class="section">
        <div class="section-header">
          <h2>⚡ Recent AI Actions</h2>
          <button
            class="refresh-btn"
            @click="loadActions"
            :disabled="loadingActions"
            title="Refresh actions"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M3 21v-5h5"/>
            </svg>
          </button>
        </div>
        <div class="section-content">
          <div v-if="loadingActions" class="loading">
            Loading actions...
          </div>
          <div v-else-if="actions.length === 0" class="empty">
            No actions recorded yet
          </div>
          <div v-else>
            <div
              v-for="action in actions"
              :key="action.timestamp"
              class="item action-item"
            >
              <div class="action-text">{{ action.action }}</div>
              <div class="action-time">{{ formatTime(action.timestamp) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- System Logs Section -->
    <div v-if="activeTab === 'logs'" class="section">
      <div class="section-header">
        <h2>📋 System Logs</h2>
        <button
          class="refresh-btn"
          @click="loadLogs"
          :disabled="loadingLogs"
          title="Refresh logs"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
            <path d="M3 21v-5h5"/>
          </svg>
        </button>
      </div>
      <div class="section-content">
        <div v-if="loadingLogs" class="loading">
          Loading logs...
        </div>
        <div v-else-if="logs.length === 0" class="empty">
          No logs available
        </div>
        <div v-else>
          <div
            v-for="log in logs"
            :key="log.timestamp"
            class="item log-item"
          >
            <div class="log-header">
              <div class="log-level" :class="log.level.toLowerCase()">{{ log.level }}</div>
              <div class="log-time">{{ formatTime(log.timestamp) }}</div>
            </div>
            <div class="log-message">{{ log.message }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      activeTab: 'memories',
      actions: [],
      memories: [],
      logs: [],
      scheduledTasks: [],
      loadingActions: false,
      loadingMemories: false,
      loadingLogs: false,
      loadingScheduledTasks: false,
      error: null
    }
  },
  methods: {
    async loadActions() {
      this.loadingActions = true
      this.error = null
      try {
        const response = await axios.get('/api/actions')
        this.actions = response.data.reverse() // Show newest first
      } catch (error) {
        this.error = 'Failed to load actions: ' + error.message
        console.error('Error loading actions:', error)
      } finally {
        this.loadingActions = false
      }
    },
    async loadMemories() {
      this.loadingMemories = true
      this.error = null
      try {
        const response = await axios.get('/api/memories')
        this.memories = response.data.sort((a, b) =>
          new Date(b.modified_at) - new Date(a.modified_at)
        ) // Show newest first
      } catch (error) {
        this.error = 'Failed to load memories: ' + error.message
        console.error('Error loading memories:', error)
      } finally {
        this.loadingMemories = false
      }
    },
    async loadLogs() {
      this.loadingLogs = true
      this.error = null
      try {
        const response = await axios.get('/api/logs')
        this.logs = response.data // Already sorted newest first from API
      } catch (error) {
        this.error = 'Failed to load logs: ' + error.message
        console.error('Error loading logs:', error)
      } finally {
        this.loadingLogs = false
      }
    },
    async loadScheduledTasks() {
      this.loadingScheduledTasks = true
      this.error = null
      try {
        const response = await axios.get('/api/scheduled-tasks')
        this.scheduledTasks = response.data.sort((a, b) => {
          if (!a.next_run_time) return 1
          if (!b.next_run_time) return -1
          return new Date(a.next_run_time) - new Date(b.next_run_time)
        }) // Sort by next run time
      } catch (error) {
        this.error = 'Failed to load scheduled tasks: ' + error.message
        console.error('Error loading scheduled tasks:', error)
      } finally {
        this.loadingScheduledTasks = false
      }
    },
    formatTime(timestamp) {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = Math.abs(now - date)
      const diffHours = diffMs / (1000 * 60 * 60)
      const diffDays = diffMs / (1000 * 60 * 60 * 24)
      const isFuture = date > now

      if (diffHours < 1) {
        const diffMinutes = Math.floor(diffMs / (1000 * 60))
        if (diffMinutes < 1) {
          return isFuture ? 'Starting soon' : 'Just now'
        }
        return isFuture ? `in ${diffMinutes}m` : `${diffMinutes}m ago`
      } else if (diffHours < 24) {
        const hours = Math.floor(diffHours)
        return isFuture ? `in ${hours}h` : `${hours}h ago`
      } else if (diffDays < 7) {
        const days = Math.floor(diffDays)
        return isFuture ? `in ${days}d` : `${days}d ago`
      } else {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit'
        })
      }
    },
    formatMemoryType(type) {
      const typeMap = {
        'user_preference': 'Preference',
        'user_observation': 'Observation',
        'reminder': 'Reminder'
      }
      return typeMap[type] || type
    },
    async loadAll() {
      await Promise.all([
        this.loadActions(),
        this.loadMemories()
      ])
    },
    switchTab(tab) {
      this.activeTab = tab
      if (tab === 'memories' && this.memories.length === 0) {
        this.loadMemories()
      } else if (tab === 'actions') {
        if (this.actions.length === 0) {
          this.loadActions()
        }
        if (this.scheduledTasks.length === 0) {
          this.loadScheduledTasks()
        }
      } else if (tab === 'logs' && this.logs.length === 0) {
        this.loadLogs()
      }
    }
  },
  async mounted() {
    // Load memories by default since that's the default tab
    await this.loadMemories()
  }
}
</script>

<style scoped>
.container {
  max-width: 100%;
  padding: 1rem;
  margin: 0 auto;
}

@media (min-width: 768px) {
  .container {
    max-width: 768px;
    padding: 2rem;
  }
}

.header {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #27272a;
}

.header h1 {
  color: #a855f7;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

@media (min-width: 768px) {
  .header h1 {
    font-size: 2rem;
  }
}

.header p {
  color: #71717a;
  font-size: 0.875rem;
}

.tabs {
  display: flex;
  margin-bottom: 2rem;
  background: #18181b;
  border-radius: 0.75rem;
  border: 1px solid #27272a;
  overflow: hidden;
}

.tab {
  flex: 1;
  padding: 1rem;
  background: transparent;
  border: none;
  color: #71717a;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border-right: 1px solid #27272a;
}

.tab:last-child {
  border-right: none;
}

.tab:hover {
  background: #1c1c1e;
  color: #e4e4e7;
}

.tab.active {
  background: #a855f7;
  color: white;
}

.section {
  margin-bottom: 2rem;
  background: #18181b;
  border-radius: 0.75rem;
  border: 1px solid #27272a;
  overflow: hidden;
}

.section-header {
  background: #1c1c1e;
  padding: 1rem;
  border-bottom: 1px solid #27272a;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h2 {
  color: #f4f4f5;
  font-size: 1.125rem;
  margin: 0;
}

.section-content {
  padding: 0;
  max-height: 500px;
  overflow-y: auto;
}

.section-content::-webkit-scrollbar {
  width: 4px;
}

.section-content::-webkit-scrollbar-track {
  background: #27272a;
}

.section-content::-webkit-scrollbar-thumb {
  background: #52525b;
  border-radius: 2px;
}

.item {
  padding: 1rem;
  border-bottom: 1px solid #27272a;
  transition: background 0.2s;
}

.item:last-child {
  border-bottom: none;
}

.item:hover {
  background: #1c1c1e;
}

.action-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-text {
  color: #e4e4e7;
  font-size: 0.875rem;
}

.action-time {
  color: #71717a;
  font-size: 0.75rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
}

.memory-item {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.memory-type {
  background: #a855f7;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.memory-type.user_preference {
  background: #3b82f6;
}

.memory-type.user_observation {
  background: #10b981;
}

.memory-type.reminder {
  background: #f59e0b;
}

.memory-content {
  color: #e4e4e7;
  font-size: 0.875rem;
  word-break: break-word;
}

.memory-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: #71717a;
  font-size: 0.75rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #71717a;
}

.error {
  background: #dc2626;
  color: white;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.empty {
  text-align: center;
  padding: 2rem;
  color: #71717a;
  font-style: italic;
}

.refresh-btn {
  background: #27272a;
  color: #a1a1aa;
  border: none;
  padding: 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.refresh-btn:hover:not(:disabled) {
  background: #3f3f46;
  color: #e4e4e7;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-btn svg {
  animation: none;
}

.refresh-btn:disabled svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Scheduled Tasks Styles */
.task-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.task-name {
  color: #e4e4e7;
  font-size: 0.875rem;
  font-weight: 500;
}

.task-time {
  color: #a855f7;
  font-size: 0.75rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  white-space: nowrap;
}

.task-description, .task-reason {
  color: #71717a;
  font-size: 0.75rem;
  line-height: 1.4;
}

/* Log Styles */
.log-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.log-level {
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.log-level.info {
  background: #1e40af;
  color: #dbeafe;
}

.log-level.warning {
  background: #d97706;
  color: #fed7aa;
}

.log-level.error {
  background: #dc2626;
  color: #fecaca;
}

.log-level.debug {
  background: #6b7280;
  color: #f3f4f6;
}

.log-time {
  color: #71717a;
  font-size: 0.75rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  white-space: nowrap;
}

.log-message {
  color: #e4e4e7;
  font-size: 0.8rem;
  line-height: 1.5;
  word-break: break-word;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
}
</style>
