<template>
  <dialog v-if="interaction" class="modal modal-open" @click.self="$emit('close')">
    <div class="modal-box w-full max-w-4xl max-h-[90vh] overflow-auto">
      <form method="dialog" class="sticky top-0 bg-base-100 z-10 flex justify-between items-center mb-4">
        <h3 class="font-bold text-lg">{{ interaction.agent }}</h3>
        <button class="btn btn-sm btn-circle btn-ghost">✕</button>
      </form>
      <div class="space-y-4">
        <div>
          <div class="label">
            <span class="label-text font-semibold text-primary">Timestamp</span>
          </div>
          <div class="text-sm">{{ formatTime(interaction.timestamp) }}</div>
          <div class="text-xs text-base-content/50">{{ new Date(interaction.timestamp).toLocaleString() }}</div>
        </div>

        <div v-if="interaction.messages && interaction.messages.length">
          <div class="label">
            <span class="label-text font-semibold text-primary">Messages</span>
          </div>
          <div class="space-y-2">
            <div
              v-for="(message, index) in interaction.messages"
              :key="index"
              class="border-l-4 p-3 rounded bg-base-200"
              :class="getMessageBorderClass(message.role)"
            >
              <div class="font-semibold text-xs uppercase mb-2">{{ message.role }}</div>
              <div v-if="message.role === 'TOOL_CALL' && message.toolCall">
                <div class="font-bold text-success mb-2">{{ message.toolCall.name }}</div>
                <div v-if="message.toolCall.arguments" class="mb-2">
                  <div class="text-xs font-semibold text-success mb-1">Arguments:</div>
                  <pre class="bg-base-300 p-2 rounded text-xs overflow-x-auto">{{ formatJson(message.toolCall.arguments) }}</pre>
                </div>
                <div v-if="message.toolCall.response">
                  <div class="text-xs font-semibold text-success mb-1">Response:</div>
                  <pre class="bg-base-300 p-2 rounded text-xs overflow-x-auto">{{ message.toolCall.response }}</pre>
                </div>
              </div>
              <pre v-else-if="message.text" class="bg-base-300 p-2 rounded text-xs overflow-x-auto">{{ message.text }}</pre>
            </div>
          </div>
        </div>

        <div>
          <div class="label">
            <span class="label-text font-semibold text-primary">Response</span>
          </div>
          <pre class="bg-base-300 p-3 rounded text-xs overflow-x-auto">{{ interaction.response }}</pre>
        </div>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>
</template>

<script>
import { formatTime } from '../utils/formatters'

export default {
  name: 'InteractionDetailModal',
  props: {
    interaction: {
      type: Object,
      default: null
    }
  },
  emits: ['close'],
  methods: {
    formatTime,
    formatJson(jsonString) {
      try {
        return JSON.stringify(JSON.parse(jsonString), null, 2)
      } catch (e) {
        return jsonString
      }
    },
    getMessageBorderClass(role) {
      const classMap = {
        'USER': 'border-info',
        'SYSTEM': 'border-primary',
        'TOOL_CALL': 'border-success'
      }
      return classMap[role] || 'border-neutral'
    }
  }
}
</script>

