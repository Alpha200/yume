<template>
  <div class="card bg-base-200 border border-base-300 hover:border-base-400 transition-colors">
    <div class="card-body">
      <div class="flex justify-between items-start gap-3 mb-3">
        <p class="text-sm text-base-content flex-1 break-words">{{ memory.content }}</p>
        <div class="badge badge-soft" :class="getMemoryTypeClass(memory.type)">
          {{ formatMemoryType(memory.type) }}
        </div>
      </div>
      <div class="space-y-1 text-xs text-base-content/70 font-mono">
        <div v-if="memory.place">{{ memory.place }}</div>
        <div>Created: {{ formatMemoryDateTime(memory.createdAt) }}</div>
        <div>Updated: {{ formatMemoryDateTime(memory.modifiedAt) }}</div>
        <div v-if="memory.observationDate">Observed: {{ formatMemoryDateTime(memory.observationDate) }}</div>
        <div v-if="memory.reminderOptions">
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
        'user_preference': 'badge-info',
        'user_observation': 'badge-success',
        'reminder': 'badge-warning'
      }
      return classMap[type] || 'badge-neutral'
    }
  }
}
</script>

