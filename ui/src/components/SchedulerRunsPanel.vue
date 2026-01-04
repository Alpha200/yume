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
      selectedRun: null,
      loadingRuns: false,
      loadingFailedRuns: false
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
  }
}
</script>

<style scoped>
.scheduler-runs-panel {
  width: 100%;
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
