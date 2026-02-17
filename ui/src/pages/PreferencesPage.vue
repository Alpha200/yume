<template>
  <PreferencesPane @error="handleError" />
</template>

<script>
import PreferencesPane from '../components/PreferencesPane.vue'

export default {
  name: 'PreferencesPage',
  components: {
    PreferencesPane
  },
  methods: {
    handleError(error) {
      this.$emit('error', error)
    }
  }
}
</script>
