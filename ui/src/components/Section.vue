<template>
  <div class="mb-6">
    <!-- Header Card -->
    <div class="card bg-base-200 border border-base-300 mb-6">
      <div class="card-body flex flex-row items-center justify-between">
        <h2 class="card-title">{{ title }}</h2>
        <div class="card-actions justify-end">
          <RefreshButton
            :loading="loading"
            :title="`Refresh ${title}`"
            @click="$emit('refresh')"
          />
        </div> 
      </div>
    </div>

    <!-- Content List -->
    <div v-if="loading" class="text-center py-12 text-base-content/60">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="mt-4">{{ loadingMessage }}</p>
    </div>
    <div v-else-if="items.length === 0" class="alert alert-soft alert-info">
      <span>{{ emptyMessage }}</span>
    </div>
    <div v-else class="space-y-3">
      <slot :items="items" />
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

