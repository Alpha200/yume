<template>
  <div class="card bg-base-200 border border-base-300 mb-6">
    <div class="card-body border-b border-base-300 pb-0 mb-0 flex flex-row items-center justify-between">
      <h2 class="card-title">{{ title }}</h2>
      <div class="card-actions justify-end">
        <RefreshButton
          :loading="loading"
          :title="`Refresh ${title}`"
          @click="$emit('refresh')"
        />
      </div> 
    </div>
    <div>
      <div v-if="loading" class="text-center py-8 text-base-content/60">
        {{ loadingMessage }}
      </div>
      <div v-else-if="items.length === 0" class="text-center py-8 text-base-content/60 italic">
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

