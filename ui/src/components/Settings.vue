<template>
  <div class="settings-container">
    <div class="settings-header">
      <h2>⚙️ Settings</h2>
      <p>Configure application settings</p>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <div v-if="successMessage" class="success">
      {{ successMessage }}
    </div>

    <!-- Train Station Mappings Section -->
    <div class="settings-section">
      <div class="section-header">
        <h3>🚂 Train Station Mappings</h3>
        <p class="section-description">
          Map train station names to Home Assistant entity IDs
        </p>
      </div>

      <!-- Add New Mapping Form -->
      <div class="add-mapping-form">
        <input
          v-model="newMapping.stationName"
          type="text"
          placeholder="Station name (e.g., Central Station)"
          class="input"
        />
        <input
          v-model="newMapping.entityId"
          type="text"
          placeholder="Entity ID (e.g., sensor.train_central)"
          class="input"
        />
        <button @click="addMapping" class="btn btn-primary" :disabled="!canAddMapping">
          ➕ Add
        </button>
      </div>

      <!-- Mappings List -->
      <div class="mappings-list" v-if="mappings.length > 0">
        <div
          v-for="mapping in mappings"
          :key="mapping.id"
          class="mapping-item"
        >
          <div class="mapping-content">
            <div class="mapping-station">{{ mapping.station_name }}</div>
            <div class="mapping-arrow">→</div>
            <div class="mapping-entity">{{ mapping.entity_id }}</div>
          </div>
          <button @click="deleteMapping(mapping.id)" class="btn btn-delete">
            🗑️ Delete
          </button>
        </div>
      </div>

      <div v-else class="empty-state">
        No train station mappings configured yet
      </div>
    </div>
  </div>
</template>

<script>
import { apiService } from '../services/api'

export default {
  name: 'Settings',
  data() {
    return {
      mappings: [],
      newMapping: {
        stationName: '',
        entityId: ''
      },
      loading: false,
      error: null,
      successMessage: null
    }
  },
  computed: {
    canAddMapping() {
      return this.newMapping.stationName.trim() && this.newMapping.entityId.trim()
    }
  },
  mounted() {
    this.loadMappings()
  },
  methods: {
    async loadMappings() {
      this.loading = true
      this.error = null
      try {
        this.mappings = await apiService.getTrainStationMappings()
      } catch (err) {
        this.error = 'Failed to load train station mappings'
        console.error(err)
      } finally {
        this.loading = false
      }
    },
    async addMapping() {
      if (!this.canAddMapping) return

      this.error = null
      this.successMessage = null

      try {
        await apiService.addTrainStationMapping(
          this.newMapping.stationName.trim(),
          this.newMapping.entityId.trim()
        )

        // Reload mappings
        await this.loadMappings()

        // Clear form
        this.newMapping.stationName = ''
        this.newMapping.entityId = ''

        // Show success message
        this.successMessage = 'Mapping added successfully'
        setTimeout(() => {
          this.successMessage = null
        }, 3000)
      } catch (err) {
        this.error = 'Failed to add mapping'
        console.error(err)
      }
    },
    async deleteMapping(mappingId) {
      const mapping = this.mappings.find(m => m.id === mappingId)
      if (!mapping) return
      
      if (!confirm(`Delete mapping for "${mapping.station_name}"?`)) return

      this.error = null
      this.successMessage = null

      try {
        await apiService.deleteTrainStationMapping(mappingId)

        // Reload mappings
        await this.loadMappings()

        // Show success message
        this.successMessage = 'Mapping deleted successfully'
        setTimeout(() => {
          this.successMessage = null
        }, 3000)
      } catch (err) {
        this.error = 'Failed to delete mapping'
        console.error(err)
      }
    }
  }
}
</script>

<style scoped>
.settings-container {
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-header h2 {
  color: #e4e4e7;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.settings-header p {
  color: #a1a1aa;
  font-size: 0.875rem;
}

.error {
  background: #7f1d1d;
  color: #fecaca;
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.success {
  background: #14532d;
  color: #bbf7d0;
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.settings-section {
  background: #18181b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.section-header h3 {
  color: #e4e4e7;
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.section-description {
  color: #a1a1aa;
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

.add-mapping-form {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.input {
  flex: 1;
  min-width: 200px;
  background: #27272a;
  border: 1px solid #3f3f46;
  color: #e4e4e7;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.input:focus {
  outline: none;
  border-color: #a855f7;
}

.input::placeholder {
  color: #71717a;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: #a855f7;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #9333ea;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-delete {
  background: #dc2626;
  color: white;
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}

.btn-delete:hover {
  background: #b91c1c;
}

.mappings-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.mapping-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #27272a;
  padding: 1rem;
  border-radius: 0.5rem;
  gap: 1rem;
}

.mapping-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
  flex-wrap: wrap;
}

.mapping-station {
  color: #e4e4e7;
  font-weight: 500;
  font-size: 0.875rem;
}

.mapping-arrow {
  color: #71717a;
  font-size: 1rem;
}

.mapping-entity {
  color: #a855f7;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}

.empty-state {
  text-align: center;
  color: #71717a;
  padding: 2rem;
  font-size: 0.875rem;
}
</style>
