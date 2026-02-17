<template>
  <DayPlanner @error="handleError" />
</template>

<script>
import DayPlanner from '../components/DayPlanner.vue'

export default {
  name: 'DayPlannerPage',
  components: {
    DayPlanner
  },
  methods: {
    handleError(error) {
      this.$emit('error', error)
    }
  }
}
</script>
