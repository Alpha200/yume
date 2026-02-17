<template>
  <div class="max-w-4xl mx-auto">
    <!-- Header Card -->
    <div class="card bg-base-200 border border-base-300 mb-6">
      <div class="card-body">
        <h2 class="card-title">️Preferences</h2>
      </div>
    </div>

    <!-- Preferences Grid -->
    <div class="space-y-3">
      <!-- Strava Integration Card -->
      <div class="card bg-base-200 border border-base-300">
        <div class="card-body">
          <h3 class="card-title text-lg">Strava</h3>
          
          <div v-if="stravaConnected" class="space-y-3">
            <div class="p-3 bg-base-300 rounded-lg">
              <p class="font-semibold text-sm">Connected</p>
              <p class="text-xs text-base-content/70">{{ stravaAthleteName }}</p>
            </div>
            <button @click="disconnectStrava" class="btn btn-soft btn-error btn-sm w-full">
              Disconnect
            </button>
          </div>

          <div v-else class="space-y-3">
            <p class="text-sm text-base-content/80">Fetch and analyze your cycling activities from Strava.</p>
            <button 
              @click="startStravaAuth" 
              class="btn btn-primary btn-sm w-full" 
              :disabled="loading"
            >
              {{ loading ? 'Redirecting...' : 'Connect' }}
            </button>
          </div>

          <div v-if="stravaError" class="alert alert-error alert-sm mt-3">
            <span class="text-xs">{{ stravaError }}</span>
          </div>
        </div>
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
