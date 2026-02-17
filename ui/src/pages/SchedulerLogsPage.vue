<template>
  <SchedulerRunsPanel @error="handleError" />
</template>

<script>
import SchedulerRunsPanel from '../components/SchedulerRunsPanel.vue'

export default {
  name: 'SchedulerLogsPage',
  components: {
    SchedulerRunsPanel
  },
  methods: {
    handleError(error) {
      this.$emit('error', error)
    }
  }
}
</script>
