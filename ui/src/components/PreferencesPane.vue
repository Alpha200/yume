<template>
  <div class="preferences">
    <h2>⚙️ Preferences</h2>

    <div class="preferences-section">
      <h3>Strava Integration</h3>
      
      <div v-if="stravaConnected" class="strava-connected">
        <div class="status-item">
          <div class="status-indicator connected"></div>
          <div>
            <p class="status-label">Connected</p>
            <p class="athlete-name">{{ stravaAthleteName }}</p>
          </div>
        </div>
        <button @click="disconnectStrava" class="button button-danger">
          Disconnect Strava
        </button>
      </div>

      <div v-else class="strava-disconnected">
        <p>Strava integration allows Yume to fetch and analyze your cycling activities.</p>
        <button @click="startStravaAuth" class="button button-primary" :disabled="loading">
          {{ loading ? '🔄 Redirecting to Strava...' : '🔗 Connect with Strava' }}
        </button>
      </div>

      <div v-if="stravaError" class="error-message">
        {{ stravaError }}
      </div>
    </div>
  </div>
</template>

<script>
import { apiService } from '../services/api'

export default {
  name: 'PreferencesPane',
  data() {
    return {
      stravaConnected: false,
      stravaAthleteName: '',
      stravaError: null,
      loading: false
    }
  },
  mounted() {
    this.loadStravaStatus()
  },
  methods: {
    async loadStravaStatus() {
      try {
        const status = await apiService.getStravaStatus()
        this.stravaConnected = status.connected
        if (status.connected) {
          this.stravaAthleteName = status.athleteName || 'Connected'
        }
        this.stravaError = null
      } catch (error) {
        console.error('Failed to load Strava status:', error)
        this.stravaError = null // Don't show error if not connected
      }
    },
    startStravaAuth() {
      // Get the authorization URL from the backend
      this.loading = true
      this.stravaError = null
      
      apiService.getStravaAuthorizeUrl()
        .then(response => {
          // Redirect to Strava OAuth
          window.location.href = response.url
        })
        .catch(error => {
          this.stravaError = 'Failed to start Strava authorization: ' + error.message
          console.error('Failed to get authorize URL:', error)
          this.loading = false
        })
    },
    async disconnectStrava() {
      if (confirm('Are you sure you want to disconnect your Strava account?')) {
        try {
          await apiService.disconnectStrava()
          this.stravaConnected = false
          this.stravaAthleteName = ''
          this.stravaError = null
        } catch (error) {
          this.stravaError = 'Failed to disconnect Strava: ' + error.message
        }
      }
    }
  }
}
</script>

<style scoped>
.preferences {
  margin-bottom: 2rem;
  background: #18181b;
  border-radius: 0.75rem;
  border: 1px solid #27272a;
  padding: 0;
  overflow: hidden;
}

.preferences h2 {
  margin: 0;
  color: #f4f4f5;
  font-size: 1.125rem;
  padding: 1rem;
  background: #1c1c1e;
  border-bottom: 1px solid #27272a;
}

.preferences-section {
  padding: 1rem;
  margin: 0;
}

.preferences-section h3 {
  font-size: 0.875rem;
  color: #a1a1a6;
  margin: 0 0 1rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.strava-connected,
.strava-disconnected {
  padding: 1rem;
  border-radius: 0.5rem;
  background: #27272a;
  border: 1px solid #3f3f46;
}

.status-item {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  gap: 12px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-indicator.connected {
  background: #4caf50;
}

.status-label {
  font-weight: 600;
  color: #f4f4f5;
  margin: 0 0 0.25rem 0;
  font-size: 14px;
}

.athlete-name {
  color: #a1a1a6;
  margin: 0;
  font-size: 14px;
}

.button {
  padding: 0.625rem 1rem;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.button-primary {
  background: #fc5200;
  color: white;
}

.button-primary:hover {
  background: #e64800;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(252, 82, 0, 0.2);
}

.button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button-danger {
  background: #f44336;
  color: white;
}

.button-danger:hover {
  background: #d32f2f;
}

.error-message {
  color: #f87171;
  padding: 0.625rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  border-radius: 0.375rem;
  margin-top: 0.625rem;
  font-size: 14px;
}

.strava-disconnected p {
  color: #a1a1a6;
  margin: 0 0 1rem 0;
  font-size: 14px;
  line-height: 1.5;
}
</style>
