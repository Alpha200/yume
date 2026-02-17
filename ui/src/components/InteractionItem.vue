<template>
  <details class="collapse border border-base-300 bg-base-200">
    <summary class="collapse-title font-semibold">
      <div class="text-sm font-medium text-base-content truncate flex-1">{{ interaction.agent }}</div>
      <div class="text-xs text-primary font-mono whitespace-nowrap">{{ formatTime(interaction.timestamp) }}</div>
    </summary>
    <div class="collapse-content">
      <div class="space-y-4 pt-4 border-t border-base-300">
        <!-- Timestamp -->
        <div>
          <div class="text-xs font-semibold text-primary uppercase mb-1">Timestamp</div>
          <div class="text-sm">{{ formatTime(interaction.timestamp) }}</div>
          <div class="text-xs text-base-content/50">{{ new Date(interaction.timestamp).toLocaleString() }}</div>
        </div>

        <!-- Messages -->
        <div v-if="interaction.messages && interaction.messages.length">
          <div class="text-xs font-semibold text-primary uppercase mb-2">Messages</div>
          <div class="space-y-2">
            <div
              v-for="(message, index) in interaction.messages"
              :key="index"
              class="border-l-4 p-3 rounded bg-base-300"
              :class="getMessageBorderClass(message.role)"
            >
              <div class="font-semibold text-xs uppercase mb-2">{{ message.role }}</div>
              <div v-if="message.role === 'TOOL_CALL' && message.toolCall">
                <div class="font-bold text-success mb-2">{{ message.toolCall.name }}</div>
                <div v-if="message.toolCall.arguments" class="mb-2">
                  <div class="text-xs font-semibold text-success mb-1">Arguments:</div>
                  <pre class="bg-base-200 p-2 rounded text-xs overflow-x-auto">{{ formatJson(message.toolCall.arguments) }}</pre>
                </div>
                <div v-if="message.toolCall.response">
                  <div class="text-xs font-semibold text-success mb-1">Response:</div>
                  <pre class="bg-base-200 p-2 rounded text-xs overflow-x-auto">{{ message.toolCall.response }}</pre>
                </div>
              </div>
              <pre v-else-if="message.text" class="bg-base-200 p-2 rounded text-xs overflow-x-auto">{{ message.text }}</pre>
            </div>
          </div>
        </div>

        <!-- Response -->
        <div>
          <div class="text-xs font-semibold text-primary uppercase mb-1">Response</div>
          <pre class="bg-base-300 p-3 rounded text-xs overflow-x-auto">{{ interaction.response }}</pre>
        </div>
      </div>
    </div>
  </details>
</template>

<script>
import { formatTime } from '../utils/formatters'

export default {
  name: 'InteractionItem',
  props: {
    interaction: {
      type: Object,
      required: true
    }
  },
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

