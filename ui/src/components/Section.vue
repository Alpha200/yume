<template>
  <div class="section">
    <div class="section-header">
      <h2>{{ title }}</h2>
      <RefreshButton
        :loading="loading"
        :title="`Refresh ${title}`"
        @click="$emit('refresh')"
      />
    </div>
    <div class="section-content">
      <div v-if="loading" class="loading">
        {{ loadingMessage }}
      </div>
      <div v-else-if="items.length === 0" class="empty">
        {{ emptyMessage }}
      </div>
      <div v-else>
        <slot :items="items" />
      </div>
    </div>
  </div>
</template>

<script>
import RefreshButton from './RefreshButton.vue'

export default {
  name: 'Section',
  components: {
    RefreshButton
  },
  props: {
    title: {
      type: String,
      required: true
    },
    items: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    loadingMessage: {
      type: String,
      default: 'Loading...'
    },
    emptyMessage: {
      type: String,
      default: 'No items found'
    }
  },
  emits: ['refresh']
}
</script>

<style scoped>
.section {
  margin-bottom: 2rem;
  background: #18181b;
  border-radius: 0.75rem;
  border: 1px solid #27272a;
  overflow: hidden;
}

.section-header {
  background: #1c1c1e;
  padding: 1rem;
  border-bottom: 1px solid #27272a;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h2 {
  color: #f4f4f5;
  font-size: 1.125rem;
  margin: 0;
}

.section-content {
  padding: 0;
  max-height: 500px;
  overflow-y: auto;
}

.section-content::-webkit-scrollbar {
  width: 4px;
}

.section-content::-webkit-scrollbar-track {
  background: #27272a;
}

.section-content::-webkit-scrollbar-thumb {
  background: #52525b;
  border-radius: 2px;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #71717a;
}

.empty {
  text-align: center;
  padding: 2rem;
  color: #71717a;
  font-style: italic;
}
</style>

