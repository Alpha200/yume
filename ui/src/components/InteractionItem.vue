<template>
  <div class="card bg-base-200 border border-base-300 hover:border-base-400 transition-colors cursor-pointer" @click="handleClick">
    <div class="card-body py-3">
      <div class="flex justify-between items-center gap-3">
        <div class="text-sm font-medium text-base-content truncate flex-1">{{ interaction.agent }}</div>
        <div class="text-xs text-primary font-mono whitespace-nowrap">{{ formatTime(interaction.timestamp) }}</div>
      </div>
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

