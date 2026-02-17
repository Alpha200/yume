<template>
  <div class="p-4 border-b border-base-300 hover:bg-base-200 transition-colors">
    <div class="flex justify-between items-start gap-3 mb-2">
      <h3 class="text-sm font-medium text-base-content flex-1">{{ task.name }}</h3>
      <div class="text-xs text-primary font-mono whitespace-nowrap">{{ formatTime(task.next_run_time) }}</div>
    </div>
    <p class="text-xs text-base-content/60 mb-1">{{ task.description }}</p>
    <p v-if="task.topic" class="text-xs text-base-content/50">Topic: {{ task.topic }}</p>
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

