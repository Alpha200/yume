<template>
  <div class="interaction-item item" @click="handleClick">
    <div class="interaction-header">
      <div class="interaction-agent">{{ interaction.agent }}</div>
      <div class="interaction-time">{{ formatTime(interaction.timestamp) }}</div>
    </div>
  </div>
</template>

<script>
import { formatTime } from '../utils/formatters'

export default {
  name: 'InteractionItem',
  props: {
    interaction: {
      type: Object,
      required: true
    }
  },
  emits: ['select'],
  methods: {
    formatTime,
    handleClick() {
      this.$emit('select', this.interaction.id)
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

.interaction-item {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.interaction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.interaction-agent {
  color: #e4e4e7;
  font-size: 0.875rem;
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.interaction-time {
  color: #a855f7;
  font-size: 0.75rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  white-space: nowrap;
}
</style>

