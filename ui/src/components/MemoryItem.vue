<template>
  <div class="memory-item item">
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
</template>

<script>
import { formatTime, formatMemoryType } from '../utils/formatters'

export default {
  name: 'MemoryItem',
  props: {
    memory: {
      type: Object,
      required: true
    }
  },
  methods: {
    formatTime,
    formatMemoryType
  }
}
</script>

<style scoped>
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
</style>

