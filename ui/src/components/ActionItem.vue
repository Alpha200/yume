<template>
  <div class="action-item item">
    <div class="action-text">{{ action.action }}</div>
    <div class="action-time">{{ formatTime(action.timestamp) }}</div>
  </div>
</template>

<script>
import { formatTime } from '../utils/formatters'

export default {
  name: 'ActionItem',
  props: {
    action: {
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
</style>

