<template>
  <div class="scheduler-runs-panel">
    <Section
      title="Recent Scheduler Runs"
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
        />
      </template>
    </Section>

    <!-- Failed Runs Section -->
    <Section
      v-if="failedRuns.length > 0"
      title="Failed Runs"
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
    }
  },
  mounted() {
    this.loadRuns()
    this.loadFailedRuns()
  }
}
</script>
