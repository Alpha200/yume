<template>
  <div class="max-w-4xl mx-auto">
    <div class="card bg-base-200 border border-base-300 mb-6">
      <div class="card-body">
        <h2 class="card-title">Day Planner</h2>
        <div class="flex items-center gap-3">
          <button @click="previousDay" class="btn btn-square btn-sm" title="Previous Day">
            ‹
          </button>
          <div class="flex-1 text-center">
            <div class="text-lg font-semibold">{{ formattedDate }}</div>
            <div class="text-sm text-base-content/60">{{ formattedDayOfWeek }}</div>
          </div>
          <button @click="nextDay" class="btn btn-square btn-sm" title="Next Day">
            ›
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="mt-4">Loading day plan...</p>
    </div>

    <div v-else-if="error" class="alert alert-soft alert-error">
      <span>{{ error }}</span>
      <button @click="loadPlan" class="btn btn-sm">Retry</button>
    </div>

    <div v-else-if="!plan || !plan.items || plan.items.length === 0" class="alert alert-soft alert-info">
      <span>No Plan for This Day - There's no plan created for {{ formattedDate }} yet.</span>
    </div>

    <div v-else class="space-y-6">
      <div v-if="plan.summary" class="card bg-base-200 border border-base-300">
        <div class="card-body">
          <span>{{ plan.summary }}</span>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-4">
        <div class="stat bg-base-200 border border-base-300 rounded-lg text-center">
          <div class="stat-value text-primary">{{ plan.items.length }}</div>
          <div class="stat-desc">Activities</div>
        </div>
        <div class="stat bg-base-200 border border-base-300 rounded-lg text-center">
          <div class="stat-value text-primary">{{ scheduledCount }}</div>
          <div class="stat-desc">Scheduled</div>
        </div>
        <div class="stat bg-base-200 border border-base-300 rounded-lg text-center">
          <div class="stat-value text-primary">{{ confirmedCount }}</div>
          <div class="stat-desc">Confirmed</div>
        </div>
      </div>

      <div class="space-y-3">
        <DayPlannerItem
          v-for="item in sortedItems"
          :key="item.id"
          :item="item"
        />
      </div>

      <div class="text-xs text-base-content/50 text-center pt-4 border-t border-base-300">
        Last updated: {{ formatDateTime(plan.updatedAt) }}
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
        if (a.startTime && !b.startTime) return -1
        if (!a.startTime && b.startTime) return 1
        
        // Both have times - sort by time
        if (a.startTime && b.startTime) {
          return new Date(a.startTime) - new Date(b.startTime)
        }
        
        // Neither has time - sort by confidence
        const order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        return order[b.confidence] - order[a.confidence]
      })
    },
    scheduledCount() {
      if (!this.plan || !this.plan.items) return 0
      return this.plan.items.filter(item => item.startTime).length
    },
    confirmedCount() {
      if (!this.plan || !this.plan.items) return 0
      return this.plan.items.filter(item => item.confidence === 'HIGH').length
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
    formatDate,
    formatDateTime
  },
  mounted() {
    this.loadPlan()
  }
}
</script>
