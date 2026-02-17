<template>
  <Section
    title="Agent Interactions"
    :items="interactions"
    :loading="loading"
    loadingMessage="Loading interactions..."
    emptyMessage="No interactions recorded yet"
    @refresh="loadInteractions"
  >
    <template #default="{ items }">
      <InteractionItem
        v-for="interaction in items"
        :key="interaction.id"
        :interaction="interaction"
      />
    </template>
  </Section>
</template>

<script>
import { apiService } from '../services/api'
import Section from '../components/Section.vue'
import InteractionItem from '../components/InteractionItem.vue'

export default {
  name: 'InteractionsPage',
  components: {
    Section,
    InteractionItem
  },
  data() {
    return {
      interactions: [],
      loading: false,
      error: null
    }
  },
  methods: {
    async loadInteractions() {
      this.loading = true
      this.error = null
      try {
        this.interactions = await apiService.getInteractions()
      } catch (error) {
        this.error = 'Failed to load interactions: ' + error.message
        this.$emit('error', this.error)
        console.error('Error loading interactions:', error)
      } finally {
        this.loading = false
      }
    }
  },
  mounted() {
    this.loadInteractions()
  }
}
</script>
