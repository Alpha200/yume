<template>
  <div class="plan-item" :class="sourceClass">
    <div class="item-header">
      <span class="item-time" v-if="item.start_time">
        {{ formatTime(item.start_time) }}
        <span v-if="item.end_time"> - {{ formatTime(item.end_time) }}</span>
      </span>
      <span class="item-time all-day" v-else>All Day</span>
      <span class="confidence-badge" :class="confidenceClass">
        {{ confidenceLabel }}
      </span>
    </div>
    <h3 class="item-title">{{ item.title }}</h3>
    <p class="item-description" v-if="item.description">{{ item.description }}</p>
    <div class="item-details">
      <span class="detail-badge" v-if="item.location">
        📍 {{ item.location }}
      </span>
      <span class="detail-badge source-badge">
        {{ sourceIcon }} {{ sourceLabel }}
      </span>
      <span class="detail-badge tag" v-for="tag in item.tags" :key="tag">
        {{ tag }}
      </span>
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
    sourceClass() {
      return `source-${this.item.source}`
    },
    sourceLabel() {
      const labels = {
        memory: 'Memory',
        calendar: 'Calendar',
        user_input: 'User Input'
      }
      return labels[this.item.source] || this.item.source
    },
    sourceIcon() {
      const icons = {
        memory: '🧠',
        calendar: '📅',
        user_input: '💬'
      }
      return icons[this.item.source] || '📌'
    },
    confidenceClass() {
      return this.item.confidence.toLowerCase()
    },
    confidenceLabel() {
      const labels = {'high': 'Confirmed', 'medium': 'Likely', 'low': 'Possible'}
      return labels[this.item.confidence.toLowerCase()] || 'Maybe'
    }
  },
  methods: {
    formatTime
  }
}
</script>

<style scoped>
.plan-item {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  transition: all 0.2s ease;
  border-left: 4px solid var(--accent-color);
}

.plan-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.plan-item.source-calendar {
  border-left-color: #4CAF50;
}

.plan-item.source-memory {
  border-left-color: #2196F3;
}

.plan-item.source-user_input {
  border-left-color: #FF9800;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.item-time {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--accent-color);
}

.item-time.all-day {
  color: var(--text-secondary);
}

.confidence-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.confidence-badge.high {
  background: #E8F5E9;
  color: #2E7D32;
}

.confidence-badge.medium {
  background: #FFF3E0;
  color: #E65100;
}

.confidence-badge.low {
  background: #F3E5F5;
  color: #6A1B9A;
}

.item-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
}

.item-description {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0 0 0.75rem 0;
  line-height: 1.5;
}

.item-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.detail-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  color: var(--text-secondary);
}

.detail-badge.source-badge {
  font-weight: 500;
}

.detail-badge.tag {
  background: var(--accent-light);
  color: var(--accent-color);
  font-weight: 500;
}
</style>
