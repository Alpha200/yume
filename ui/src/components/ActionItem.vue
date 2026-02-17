<template>
  <div class="p-4 border-b border-base-300 hover:bg-base-200 transition-colors">
    <div class="flex justify-between items-start gap-3">
      <p class="text-sm text-base-content">{{ action.action }}</p>
      <div class="text-xs text-base-content/50 font-mono whitespace-nowrap">{{ formatTime(action.timestamp) }}</div>
    </div>
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

