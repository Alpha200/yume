<template>
  <div class="card bg-base-200 border border-l-4 border-base-300" :class="`border-l-${getSourceColor(item.source)}`">
    <div class="card-body p-4 gap-2">
      <div class="flex justify-between items-start gap-3">
        <div>
          <h3 class="font-bold text-base">{{ item.title }}</h3>
          <p v-if="item.description" class="text-sm text-base-content/70 mt-1">{{ item.description }}</p>
        </div>
        <div class="badge badge-soft" :class="`badge-${getConfidenceColor(item.confidence)}`">
          {{ confidenceLabel }}
        </div>
      </div>
      <div class="flex gap-2 items-baseline">
        <span v-if="item.startTime" class="text-sm font-semibold text-primary">
          {{ formatTime(item.startTime) }}
          <span v-if="item.endTime"> - {{ formatTime(item.endTime) }}</span>
        </span>
        <span v-else class="text-sm text-base-content/50">All Day</span>
      </div>
      <div class="flex flex-wrap gap-2 mt-2">
        <div v-if="item.location" class="badge badge-soft badge-secondary">{{ item.location }}</div>
        <div class="badge badge-soft badge-secondary">{{ sourceLabel }}</div>
        <div v-for="tag in item.tags" :key="tag" class="badge badge-soft badge-primary">{{ tag }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatTime } from '../utils/formatters'

export default {
  name: 'DayPlannerItem',
  props: {
    item: {
      type: Object,
      required: true
    }
  },
  computed: {
    sourceLabel() {
      const labels = {
        MEMORY: 'Memory',
        CALENDAR: 'Calendar',
        USER_INPUT: 'User Input',
        GUESS: 'Guess'
      }
      return labels[this.item.source] || this.item.source
    },
    confidenceLabel() {
      const labels = {'high': 'Confirmed', 'medium': 'Likely', 'low': 'Possible'}
      return labels[this.item.confidence.toLowerCase()] || 'Maybe'
    }
  },
  methods: {
    formatTime,
    getSourceColor(source) {
      const colorMap = {
        calendar: 'success',
        memory: 'info',
        user_input: 'warning'
      }
      return colorMap[source] || 'primary'
    },
    getConfidenceColor(confidence) {
      const colorMap = {
        'HIGH': 'success',
        'MEDIUM': 'warning',
        'LOW': 'error'
      }
      return colorMap[confidence] || 'neutral'
    }
  }
}
</script>
