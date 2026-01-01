<template>
  <div v-if="interaction" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>🤖 {{ interaction.agent }}</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <div class="detail-section">
          <div class="detail-label">Timestamp</div>
          <div class="detail-value">{{ formatTime(interaction.timestamp) }}</div>
          <div class="detail-value-full">{{ new Date(interaction.timestamp).toLocaleString() }}</div>
        </div>
        <div v-if="interaction.messages && interaction.messages.length" class="detail-section">
          <div class="detail-label">Messages</div>
          <div class="messages-wrapper">
            <div
              v-for="(message, index) in interaction.messages"
              :key="index"
              class="message-record"
              :class="message.role.toLowerCase()"
            >
              <div class="message-role">{{ message.role }}</div>
              <div v-if="message.role === 'TOOL_CALL' && message.toolCall">
                <div class="tool-call-name">{{ message.toolCall.name }}</div>
                <div v-if="message.toolCall.arguments" class="tool-section">
                  <div class="tool-section-label">Arguments:</div>
                  <pre class="detail-code tool-code">{{ formatJson(message.toolCall.arguments) }}</pre>
                </div>
                <div v-if="message.toolCall.response" class="tool-section">
                  <div class="tool-section-label">Response:</div>
                  <pre class="detail-code tool-code">{{ message.toolCall.response }}</pre>
                </div>
              </div>
              <pre v-else-if="message.text" class="detail-code message-text">{{ message.text }}</pre>
            </div>
          </div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Response</div>
          <pre class="detail-code">{{ interaction.response }}</pre>
        </div>
      </div>
    </div>
  </div>
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
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  overflow-y: auto;
}

.modal-content {
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 0.75rem;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  background: #1c1c1e;
  padding: 1.5rem;
  border-bottom: 1px solid #27272a;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  color: #f4f4f5;
  font-size: 1.25rem;
  margin: 0;
}

.close-btn {
  background: #27272a;
  color: #a1a1aa;
  border: none;
  width: 2rem;
  height: 2rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  line-height: 1;
}

.close-btn:hover {
  background: #3f3f46;
  color: #e4e4e7;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: #27272a;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #52525b;
  border-radius: 4px;
}

.detail-section {
  margin-bottom: 1.5rem;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  color: #a855f7;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-value {
  color: #e4e4e7;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.detail-value-full {
  color: #71717a;
  font-size: 0.75rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
}

.detail-code {
  background: #09090b;
  border: 1px solid #27272a;
  border-radius: 0.5rem;
  padding: 1rem;
  color: #e4e4e7;
  font-size: 0.8rem;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  margin: 0;
}

.detail-code::-webkit-scrollbar {
  height: 6px;
}

.detail-code::-webkit-scrollbar-track {
  background: #18181b;
}

.detail-code::-webkit-scrollbar-thumb {
  background: #52525b;
  border-radius: 3px;
}

.messages-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.message-record {
  padding: 0.75rem;
  border: 1px solid #27272a;
  border-radius: 0.5rem;
  background: #0f0f11;
}

.message-record.user {
  border-left: 3px solid #3b82f6;
}

.message-record.system {
  border-left: 3px solid #a855f7;
}

.message-record.tool_call {
  border-left: 3px solid #10b981;
}

.message-role {
  font-weight: 600;
  color: #f4f4f5;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.75rem;
}

.message-text {
  margin: 0;
  background: #1a1a1d;
  border-color: #3f3f46;
}

.tool-call-name {
  font-weight: 700;
  color: #10b981;
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #3f3f46;
}

.tool-section {
  margin-top: 0.75rem;
}

.tool-section-label {
  color: #10b981;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.375rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tool-code {
  margin: 0;
  background: #1a1a1d;
  border-color: #3f3f46;
}
</style>

