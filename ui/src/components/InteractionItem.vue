<template>
  <div class="p-4 border-b border-base-300 hover:bg-base-200 transition-colors cursor-pointer" @click="handleClick">
    <div class="flex justify-between items-center gap-3">
      <div class="text-sm font-medium text-base-content truncate flex-1">{{ interaction.agent }}</div>
      <div class="text-xs text-primary font-mono whitespace-nowrap">{{ formatTime(interaction.timestamp) }}</div>
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

