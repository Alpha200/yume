<template>
  <div v-if="interaction" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>🤖 {{ formatAgentType(interaction.agent_type) }}</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <div v-if="interaction.system_instructions" class="detail-section system-instructions-section">
          <div class="detail-label">System Instructions</div>
          <pre class="detail-code system-instructions">{{ interaction.system_instructions }}</pre>
        </div>
        <div class="detail-section">
          <div class="detail-label">Timestamp</div>
          <div class="detail-value">{{ formatTime(interaction.timestamp) }}</div>
          <div class="detail-value-full">{{ new Date(interaction.timestamp).toLocaleString() }}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Input</div>
          <pre class="detail-code">{{ interaction.input_data }}</pre>
        </div>
        <div class="detail-section">
          <div class="detail-label">Output</div>
          <pre class="detail-code">{{ interaction.output_data }}</pre>
        </div>
        <div v-if="interaction.metadata && Object.keys(interaction.metadata).length > 0" class="detail-section">
          <div class="detail-label">Metadata</div>
          <pre class="detail-code">{{ JSON.stringify(interaction.metadata, null, 2) }}</pre>
        </div>
        <div v-if="interaction.tool_usage && interaction.tool_usage.length" class="detail-section usage-section">
          <div class="detail-label">Tool Usage</div>
          <div class="usage-record-wrapper">
            <div
              v-for="(toolCall, index) in interaction.tool_usage"
              :key="`${toolCall.tool_name}-${index}-${toolCall.start_time}`"
              class="usage-record"
            >
              <div class="usage-record-header">
                <span class="usage-record-title">{{ toolCall.tool_name }}</span>
                <span class="usage-record-times">{{ formatTimeRange(toolCall.start_time, toolCall.end_time) }}</span>
              </div>
              <div v-if="toolCall.input" class="usage-input-wrapper">
                <div class="usage-input-label">Input:</div>
                <pre class="detail-code usage-input">{{ toolCall.input }}</pre>
              </div>
              <div v-if="toolCall.result" class="usage-result-wrapper">
                <div class="usage-result-label">Result:</div>
                <pre class="detail-code usage-result">{{ toolCall.result }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatTime, formatAgentType, formatDateTime } from '../utils/formatters'

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
    formatAgentType,
    formatTimeRange(start, end) {
      if (!start) {
        return 'Unknown time'
      }
      const formattedStart = formatDateTime(start)
      if (end) {
        return `${formattedStart} → ${formatDateTime(end)}`
      }
      return `${formattedStart} (pending)`
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

.system-instructions-section {
  border: 1px solid #a855f7;
  border-radius: 0.5rem;
  padding: 1rem;
  background: rgba(168, 85, 247, 0.05);
  margin-bottom: 1.5rem;
}

.system-instructions {
  background: rgba(168, 85, 247, 0.1);
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.usage-section .usage-record-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.usage-record {
  padding: 0.75rem;
  border: 1px solid #27272a;
  border-radius: 0.5rem;
  background: #0f0f11;
}

.usage-record-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.5rem;
  align-items: center;
}

.usage-record-title {
  font-weight: 600;
  color: #f4f4f5;
}

.usage-record-times {
  color: #a3a3ff;
  font-size: 0.75rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
}

.usage-input-wrapper,
.usage-result-wrapper {
  margin-top: 0.5rem;
}

.usage-input-label,
.usage-result-label {
  color: #a1a1aa;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.375rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.usage-input {
  margin: 0;
  background: #1a1a1d;
  border-color: #3f3f46;
}

.usage-result {
  margin: 0;
  background: #151515;
}
</style>

