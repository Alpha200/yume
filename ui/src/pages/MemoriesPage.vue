<template>
  <Section
    title="Memory Store"
    :items="memories"
    :loading="loading"
    loadingMessage="Loading memories..."
    emptyMessage="No memories stored yet"
    @refresh="loadMemories"
  >
    <template #default="{ items }">
      <MemoryItem v-for="memory in items" :key="memory.id" :memory="memory" />
    </template>
  </Section>
</template>

<script>
import { apiService } from '../services/api'
import Section from '../components/Section.vue'
import MemoryItem from '../components/MemoryItem.vue'

export default {
  name: 'MemoriesPage',
  components: {
    Section,
    MemoryItem
  },
  data() {
    return {
      memories: [],
      loading: false,
      error: null
    }
  },
  methods: {
    async loadMemories() {
      this.loading = true
      this.error = null
      try {
        this.memories = await apiService.getMemories()
      } catch (error) {
        this.error = 'Failed to load memories: ' + error.message
        this.$emit('error', this.error)
        console.error('Error loading memories:', error)
      } finally {
        this.loading = false
      }
    }
  },
  mounted() {
    this.loadMemories()
  }
}
</script>
