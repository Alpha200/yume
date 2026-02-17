<template>
  <div class="card border-l-4 bg-base-200 border border-base-300" :class="`border-l-${getStatusColor(run.status)}`">
    <div class="card-body gap-3">
      <div class="flex justify-between items-center">
        <h3 class="font-bold text-base">{{ run.topic }}</h3>
        <div class="badge" :class="`badge-${getStatusColor(run.status)}`">
          {{ formatStatus(run.status) }}
        </div>
      </div>
      <div class="divider my-0"></div>
      <div class="space-y-2 text-sm">
        <p><strong>Scheduled:</strong> {{ formatDateTime(run.scheduledTime) }}</p>
        <p v-if="run.actualExecutionTime"><strong>Executed:</strong> {{ formatDateTime(run.actualExecutionTime) }}</p>
        <p v-if="run.executionDurationMs"><strong>Duration:</strong> {{ run.executionDurationMs }}ms</p>
        <p v-if="run.details" class="break-words"><strong>Details:</strong> {{ run.details }}</p>
        <p v-if="run.errorMessage" class="text-error"><strong>Error:</strong> {{ run.errorMessage }}</p>
        <div v-if="run.aiResponse" class="bg-base-300 p-2 rounded text-xs overflow-x-auto">
          <strong>Response:</strong> {{ truncateResponse(run.aiResponse) }}
        </div>
      </div>
    </div>
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
      return typeof response === 'string' ? response : JSON.stringify(response)
    },
    getStatusColor(status) {
      const colorMap = {
        completed: 'success',
        failed: 'error',
        executing: 'info',
        scheduled: 'warning'
      }
      return colorMap[status] || 'neutral'
    }
  }
}
</script>
