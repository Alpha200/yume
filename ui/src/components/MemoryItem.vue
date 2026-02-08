<template>
  <div class="memory-item item">
    <div class="memory-header">
      <div class="memory-content">{{ memory.content }}</div>
      <div class="memory-type" :class="getMemoryTypeClass(memory.type)">
        {{ formatMemoryType(memory.type) }}
      </div>
    </div>
    <div class="memory-meta">
      <div v-if="memory.place">📍 {{ memory.place }}</div>
      <div>✨ Created: {{ formatMemoryDateTime(memory.createdAt) }}</div>
      <div>🕒 Updated: {{ formatMemoryDateTime(memory.modifiedAt) }}</div>
      <div v-if="memory.observationDate">👁️ Observed: {{ formatMemoryDateTime(memory.observationDate) }}</div>
      <div v-if="memory.reminderOptions">
        🔔
        <span v-if="memory.reminderOptions.datetimeValue">
          Remind at: {{ formatTime(memory.reminderOptions.datetimeValue) }}
        </span>
        <span v-if="memory.reminderOptions.timeValue">
          Daily at: {{ memory.reminderOptions.timeValue }}
        </span>
        <span v-if="memory.reminderOptions.daysOfWeek">
          Days: {{ memory.reminderOptions.daysOfWeek.join(', ') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { formatMemoryDateTime, formatMemoryType } from '../utils/formatters'

export default {
  name: 'MemoryItem',
  props: {
    memory: {
      type: Object,
      required: true
    }
  },
  methods: {
    formatMemoryDateTime,
    formatMemoryType,
    getMemoryTypeClass(type) {
      const classMap = {
        'user_preference': 'preference',
        'user_observation': 'observation',
        'reminder': 'reminder'
      }
      return classMap[type] || 'default'
    }
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

.memory-type.preference {
  background: #3b82f6;
}

.memory-type.observation {
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

