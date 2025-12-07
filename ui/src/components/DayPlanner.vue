<template>
  <div class="day-planner">
    <div class="planner-header">
      <h2>📅 Day Planner</h2>
      <div class="date-navigation">
        <button @click="previousDay" class="nav-button" title="Previous Day">
          ‹
        </button>
        <div class="date-display">
          <div class="date-main">{{ formattedDate }}</div>
          <div class="date-sub">{{ formattedDayOfWeek }}</div>
        </div>
        <button @click="nextDay" class="nav-button" title="Next Day">
          ›
        </button>
        <button @click="goToToday" class="today-button" :disabled="isToday">
          Today
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading day plan...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button @click="loadPlan" class="retry-button">Retry</button>
    </div>

    <div v-else-if="!plan || !plan.items || plan.items.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>No Plan for This Day</h3>
      <p>There's no plan created for {{ formattedDate }} yet.</p>
    </div>

    <div v-else class="plan-content">
      <div class="plan-summary" v-if="plan.summary">
        <div class="summary-icon">💡</div>
        <p>{{ plan.summary }}</p>
      </div>

      <div class="plan-stats">
        <div class="stat">
          <span class="stat-value">{{ plan.items.length }}</span>
          <span class="stat-label">Activities</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ scheduledCount }}</span>
          <span class="stat-label">Scheduled</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ confirmedCount }}</span>
          <span class="stat-label">Confirmed</span>
        </div>
      </div>

      <div class="items-list">
        <DayPlannerItem
          v-for="item in sortedItems"
          :key="item.id"
          :item="item"
        />
      </div>

      <div class="plan-footer">
        <p class="update-time">
          Last updated: {{ formatDateTime(plan.updated_at) }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { apiService } from '../services/api'
import DayPlannerItem from './DayPlannerItem.vue'
import { formatDate, formatDateTime } from '../utils/formatters'

export default {
  name: 'DayPlanner',
  components: {
    DayPlannerItem
  },
  data() {
    return {
      currentDate: new Date(),
      plan: null,
      loading: false,
      error: null
    }
  },
  computed: {
    dateString() {
      const year = this.currentDate.getFullYear()
      const month = String(this.currentDate.getMonth() + 1).padStart(2, '0')
      const day = String(this.currentDate.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    formattedDate() {
      return formatDate(this.currentDate.toISOString())
    },
    formattedDayOfWeek() {
      return this.currentDate.toLocaleDateString('en-US', { weekday: 'long' })
    },
    isToday() {
      const today = new Date()
      return (
        this.currentDate.getDate() === today.getDate() &&
        this.currentDate.getMonth() === today.getMonth() &&
        this.currentDate.getFullYear() === today.getFullYear()
      )
    },
    sortedItems() {
      if (!this.plan || !this.plan.items) return []
      
      return [...this.plan.items].sort((a, b) => {
        // Items with start times first
        if (a.start_time && !b.start_time) return -1
        if (!a.start_time && b.start_time) return 1
        
        // Both have times - sort by time
        if (a.start_time && b.start_time) {
          return new Date(a.start_time) - new Date(b.start_time)
        }
        
        // Neither has time - sort by confidence
        return b.confidence - a.confidence
      })
    },
    scheduledCount() {
      if (!this.plan || !this.plan.items) return 0
      return this.plan.items.filter(item => item.start_time).length
    },
    confirmedCount() {
      if (!this.plan || !this.plan.items) return 0
      return this.plan.items.filter(item => item.confidence >= 0.9).length
    }
  },
  methods: {
    async loadPlan() {
      this.loading = true
      this.error = null
      
      try {
        this.plan = await apiService.getDayPlan(this.dateString)
      } catch (error) {
        if (error.response && error.response.status === 404) {
          this.plan = null
        } else {
          this.error = 'Failed to load day plan: ' + error.message
          console.error('Error loading day plan:', error)
        }
      } finally {
        this.loading = false
      }
    },
    previousDay() {
      const newDate = new Date(this.currentDate)
      newDate.setDate(newDate.getDate() - 1)
      this.currentDate = newDate
      this.loadPlan()
    },
    nextDay() {
      const newDate = new Date(this.currentDate)
      newDate.setDate(newDate.getDate() + 1)
      this.currentDate = newDate
      this.loadPlan()
    },
    goToToday() {
      this.currentDate = new Date()
      this.loadPlan()
    },
    formatDate,
    formatDateTime
  },
  mounted() {
    this.loadPlan()
  }
}
</script>

<style scoped>
.day-planner {
  max-width: 900px;
  margin: 0 auto;
  padding: 1rem;
}

.planner-header {
  margin-bottom: 2rem;
}

.planner-header h2 {
  font-size: 1.75rem;
  margin: 0 0 1rem 0;
  color: var(--text-primary);
}

.date-navigation {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--card-bg);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.nav-button {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-button:hover {
  background: var(--accent-light);
  border-color: var(--accent-color);
}

.date-display {
  flex: 1;
  text-align: center;
}

.date-main {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.date-sub {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.today-button {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--accent-color);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.today-button:hover:not(:disabled) {
  background: var(--accent-dark);
}

.today-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state,
.empty-state {
  text-align: center;
  padding: 3rem;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.error-icon,
.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-state h3,
.empty-state h3 {
  font-size: 1.25rem;
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
}

.error-state p,
.empty-state p {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.retry-button {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 0.5rem;
  background: var(--accent-color);
  color: white;
}

.retry-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.plan-content {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 1.5rem;
}

.plan-summary {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--accent-light);
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.summary-icon {
  font-size: 1.5rem;
}

.plan-summary p {
  margin: 0;
  line-height: 1.6;
  color: var(--text-primary);
}

.plan-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat {
  text-align: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent-color);
}

.stat-label {
  display: block;
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.items-list {
  margin-bottom: 1.5rem;
}

.plan-footer {
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.update-time {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}
</style>
