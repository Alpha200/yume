<template>
  <div class="scheduler-run-item" :class="statusClass">
    <div class="header">
      <h3>{{ run.topic }}</h3>
      <span class="status-badge" :class="run.status">{{ formatStatus(run.status) }}</span>
    </div>
    <div class="details">
      <p><strong>Scheduled:</strong> {{ formatDateTime(run.scheduledTime) }}</p>
      <p v-if="run.actualExecutionTime"><strong>Executed:</strong> {{ formatDateTime(run.actualExecutionTime) }}</p>
      <p v-if="run.executionDurationMs"><strong>Duration:</strong> {{ run.executionDurationMs }}ms</p>
      <p v-if="run.details" class="details-text"><strong>Details:</strong> {{ run.details }}</p>
      <p v-if="run.errorMessage" class="error-message"><strong>Error:</strong> {{ run.errorMessage }}</p>
      <p v-if="run.aiResponse" class="response"><strong>Response:</strong> {{ truncateResponse(run.aiResponse) }}</p>
    </div>
    <button v-if="run.id" @click="showDetails" class="details-button">View Details</button>
  </div>
</template>

<script>
export default {
  name: 'SchedulerRunItem',
  props: {
    run: {
      type: Object,
      required: true
    }
  },
  computed: {
    statusClass() {
      return `status-${this.run.status}`
    }
  },
  methods: {
    formatStatus(status) {
      return status.charAt(0).toUpperCase() + status.slice(1)
    },
    formatDateTime(dateTime) {
      if (!dateTime) return 'N/A'
      const date = new Date(dateTime)
      return date.toLocaleString()
    },
    truncateResponse(response) {
      if (!response) return 'N/A'
      const str = typeof response === 'string' ? response : JSON.stringify(response)
      return str.length > 100 ? str.substring(0, 100) + '...' : str
    },
    showDetails() {
      this.$emit('select', this.run.id)
    }
  }
}
</script>

<style scoped>
.scheduler-run-item {
  border: 1px solid #3f3f3f;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  background-color: #1e1e1e;
  transition: all 0.3s ease;
}

.scheduler-run-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  background-color: #2a2a2a;
}

.scheduler-run-item.status-completed {
  border-left: 4px solid #4caf50;
}

.scheduler-run-item.status-failed {
  border-left: 4px solid #f44336;
  background-color: #2a1f1f;
}

.scheduler-run-item.status-executing {
  border-left: 4px solid #2196f3;
  background-color: #1f2a3a;
}

.scheduler-run-item.status-scheduled {
  border-left: 4px solid #ff9800;
  background-color: #2a2620;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header h3 {
  margin: 0;
  font-size: 18px;
  color: #e0e0e0;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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

.details {
  margin-bottom: 12px;
}

.details p {
  margin: 6px 0;
  font-size: 14px;
  color: #b0b0b0;
}

.details-text {
  background-color: #2a2a2a;
  padding: 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #c0c0c0;
  white-space: pre-wrap;
  word-break: break-word;
}

.details strong {
  color: #e0e0e0;
  font-weight: 600;
}

.error-message {
  color: #ff8a80;
  background-color: #2a1f1f;
  padding: 8px;
  border-radius: 4px;
  font-size: 13px;
  border-left: 3px solid #f44336;
}

.response {
  background-color: #2a2a2a;
  padding: 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  overflow-x: auto;
  color: #b0b0b0;
}

.details-button {
  background-color: #2196f3;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s ease;
}

.details-button:hover {
  background-color: #1976d2;
}

.details-button:active {
  background-color: #1565c0;
}
</style>
