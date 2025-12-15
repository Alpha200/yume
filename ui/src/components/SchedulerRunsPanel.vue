<template>
  <div class="scheduler-runs-panel">
    <Section
      title="📊 Recent Scheduler Runs"
      :items="runs"
      :loading="loadingRuns"
      loadingMessage="Loading scheduler runs..."
      emptyMessage="No scheduler runs yet"
      @refresh="loadRuns"
    >
      <template #default="{ items }">
        <SchedulerRunItem 
          v-for="run in items" 
          :key="run.id" 
          :run="run"
          @select="showRunDetail"
        />
      </template>
    </Section>

    <!-- Failed Runs Section -->
    <Section
      v-if="failedRuns.length > 0"
      title="⚠️ Failed Runs"
      :items="failedRuns"
      :loading="loadingFailedRuns"
      loadingMessage="Loading failed runs..."
      emptyMessage="No failed runs"
      @refresh="loadFailedRuns"
    >
      <template #default="{ items }">
        <SchedulerRunItem 
          v-for="run in items" 
          :key="run.id" 
          :run="run"
          @select="showRunDetail"
        />
      </template>
    </Section>

    <!-- Statistics Section -->
    <div class="stats-container" v-if="statistics">
      <h3>Statistics (Last 7 Days)</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ statistics.total_runs }}</div>
          <div class="stat-label">Total Runs</div>
        </div>
        <div class="stat-card success">
          <div class="stat-value">{{ statistics.completed_runs }}</div>
          <div class="stat-label">Completed</div>
        </div>
        <div class="stat-card error">
          <div class="stat-value">{{ statistics.failed_runs }}</div>
          <div class="stat-label">Failed</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-value">{{ statistics.success_rate.toFixed(1) }}%</div>
          <div class="stat-label">Success Rate</div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">{{ statistics.average_execution_duration_ms }}ms</div>
          <div class="stat-label">Avg Duration</div>
        </div>
      </div>
    </div>

    <!-- Run Detail Modal -->
    <div v-if="selectedRun" class="modal-overlay" @click="closeRunDetail">
      <div class="modal" @click.stop>
        <button class="close-button" @click="closeRunDetail">✕</button>
        <h2>Scheduler Run Details</h2>
        <div class="run-details">
          <div class="detail-row">
            <strong>Run ID:</strong>
            <code>{{ selectedRun.id }}</code>
          </div>
          <div class="detail-row">
            <strong>Topic:</strong>
            <span>{{ selectedRun.topic }}</span>
          </div>
          <div class="detail-row">
            <strong>Status:</strong>
            <span class="status-badge" :class="selectedRun.status">{{ formatStatus(selectedRun.status) }}</span>
          </div>
          <div class="detail-row">
            <strong>Reason:</strong>
            <span>{{ selectedRun.reason }}</span>
          </div>
          <div class="detail-row">
            <strong>Scheduled Time:</strong>
            <span>{{ formatDateTime(selectedRun.scheduled_time) }}</span>
          </div>
          <div v-if="selectedRun.actual_execution_time" class="detail-row">
            <strong>Executed Time:</strong>
            <span>{{ formatDateTime(selectedRun.actual_execution_time) }}</span>
          </div>
          <div v-if="selectedRun.execution_duration_ms" class="detail-row">
            <strong>Duration:</strong>
            <span>{{ selectedRun.execution_duration_ms }}ms</span>
          </div>
          <div v-if="selectedRun.details" class="detail-row">
            <strong>Details:</strong>
            <pre>{{ selectedRun.details }}</pre>
          </div>
          <div v-if="selectedRun.error_message" class="detail-row error">
            <strong>Error Message:</strong>
            <pre>{{ selectedRun.error_message }}</pre>
          </div>
          <div v-if="selectedRun.ai_response" class="detail-row">
            <strong>AI Response:</strong>
            <pre class="response-text">{{ selectedRun.ai_response }}</pre>
          </div>
          <div class="detail-row">
            <strong>Created:</strong>
            <span>{{ formatDateTime(selectedRun.created_at) }}</span>
          </div>
          <div class="detail-row">
            <strong>Updated:</strong>
            <span>{{ formatDateTime(selectedRun.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { apiService } from '../services/api'
import Section from './Section.vue'
import SchedulerRunItem from './SchedulerRunItem.vue'

export default {
  name: 'SchedulerRunsPanel',
  components: {
    Section,
    SchedulerRunItem
  },
  data() {
    return {
      runs: [],
      failedRuns: [],
      statistics: null,
      selectedRun: null,
      loadingRuns: false,
      loadingFailedRuns: false,
      loadingStatistics: false
    }
  },
  methods: {
    async loadRuns() {
      this.loadingRuns = true
      try {
        this.runs = await apiService.getSchedulerRuns(20)
      } catch (error) {
        console.error('Error loading scheduler runs:', error)
      } finally {
        this.loadingRuns = false
      }
    },
    async loadFailedRuns() {
      this.loadingFailedRuns = true
      try {
        this.failedRuns = await apiService.getFailedSchedulerRuns(10)
      } catch (error) {
        console.error('Error loading failed runs:', error)
      } finally {
        this.loadingFailedRuns = false
      }
    },
    async loadStatistics() {
      this.loadingStatistics = true
      try {
        this.statistics = await apiService.getSchedulerRunStatistics(7)
      } catch (error) {
        console.error('Error loading statistics:', error)
      } finally {
        this.loadingStatistics = false
      }
    },
    async showRunDetail(runId) {
      try {
        this.selectedRun = await apiService.getSchedulerRun(runId)
      } catch (error) {
        console.error('Error loading run details:', error)
      }
    },
    closeRunDetail() {
      this.selectedRun = null
    },
    formatStatus(status) {
      return status.charAt(0).toUpperCase() + status.slice(1)
    },
    formatDateTime(dateTime) {
      if (!dateTime) return 'N/A'
      const date = new Date(dateTime)
      return date.toLocaleString()
    }
  },
  mounted() {
    this.loadRuns()
    this.loadFailedRuns()
    this.loadStatistics()
  }
}
</script>

<style scoped>
.scheduler-runs-panel {
  width: 100%;
}

.stats-container {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #3f3f3f;
}

.stats-container h3 {
  color: #e0e0e0;
  margin: 0 0 16px 0;
  font-size: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card.success {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
}

.stat-card.error {
  background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
}

.stat-card.warning {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
}

.stat-card.info {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 11px;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 24px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
  position: relative;
  border: 1px solid #3f3f3f;
}

.close-button {
  position: absolute;
  top: 12px;
  right: 12px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #888;
  transition: color 0.3s ease;
}

.close-button:hover {
  color: #e0e0e0;
}

.modal h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #e0e0e0;
  border-bottom: 2px solid #3f3f3f;
  padding-bottom: 12px;
}

.run-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-row strong {
  color: #e0e0e0;
  font-weight: 600;
  font-size: 14px;
}

.detail-row code {
  background-color: #2a2a2a;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  word-break: break-all;
  color: #b0b0b0;
}

.detail-row.error {
  background-color: #2a1f1f;
  padding: 12px;
  border-radius: 4px;
  border-left: 4px solid #f44336;
}

.detail-row pre {
  margin: 0;
  background-color: #2a2a2a;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #b0b0b0;
}

.detail-row .response-text {
  background-color: #1f2a3a;
  max-height: 200px;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  width: fit-content;
}

.status-badge.completed {
  background-color: #1b5e20;
  color: #4caf50;
}

.status-badge.failed {
  background-color: #b71c1c;
  color: #ff8a80;
}

.status-badge.executing {
  background-color: #01579b;
  color: #64b5f6;
}

.status-badge.scheduled {
  background-color: #e65100;
  color: #ffe0b2;
}
</style>
