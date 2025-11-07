<template>
  <div class="log-item item">
    <div class="log-header">
      <div class="log-level" :class="log.level.toLowerCase()">{{ log.level }}</div>
      <div class="log-time">{{ formatTime(log.timestamp) }}</div>
    </div>
    <div class="log-message">{{ log.message }}</div>
  </div>
</template>

<script>
import { formatTime } from '../utils/formatters'

export default {
  name: 'LogItem',
  props: {
    log: {
      type: Object,
      required: true
    }
  },
  methods: {
    formatTime
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

