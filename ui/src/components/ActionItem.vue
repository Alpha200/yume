<template>
  <div class="card bg-base-200 border border-base-300 hover:border-base-400 transition-colors">
    <div class="card-body py-3">
      <div class="flex justify-between items-start gap-3">
        <p class="text-sm text-base-content flex-1">{{ action.action }}</p>
        <div class="text-xs text-base-content/50 font-mono whitespace-nowrap">{{ formatTime(action.timestamp) }}</div>
      </div>
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

