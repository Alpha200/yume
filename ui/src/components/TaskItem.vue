<template>
  <div class="task-item item">
    <div class="task-header">
      <div class="task-name">{{ task.name }}</div>
      <div class="task-time">{{ formatTime(task.next_run_time) }}</div>
    </div>
    <div class="task-description">{{ task.description }}</div>
    <div v-if="task.topic" class="task-reason">Topic: {{ task.topic }}</div>
  </div>
</template>

<script>
import { formatTime } from '../utils/formatters'

export default {
  name: 'TaskItem',
  props: {
    task: {
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
</style>

