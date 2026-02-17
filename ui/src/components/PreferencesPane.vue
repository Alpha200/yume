<template>
  <div class="card bg-base-200 border border-base-300">
    <div class="card-body">
      <h2 class="card-title">️Preferences</h2>
      <div class="divider my-0"></div>

      <div class="space-y-4">
        <div>
          <h3 class="font-semibold text-sm uppercase">Strava Integration</h3>
          
          <div v-if="stravaConnected" class="p-4 bg-base-300 rounded-lg space-y-3">
            <div class="flex items-center gap-3">
              <div class="indicator">
                <div class="indicator-item badge badge-success"></div>
                <div>
                  <p class="font-semibold">Connected</p>
                  <p class="text-sm text-base-content/70">{{ stravaAthleteName }}</p>
                </div>
              </div>
            </div>
            <button @click="disconnectStrava" class="btn btn-outline btn-error btn-sm width-full">
              Disconnect Strava
            </button>
          </div>

          <div v-else class="p-4 bg-base-300 rounded-lg space-y-3">
            <p class="text-sm">Strava integration allows Yume to fetch and analyze your cycling activities.</p>
            <button 
              @click="startStravaAuth" 
              class="btn btn-primary btn-sm" 
              :disabled="loading"
            >
              {{ loading ? '🔄 Redirecting to Strava...' : '🔗 Connect with Strava' }}
            </button>
          </div>

          <div v-if="stravaError" class="alert alert-error mt-3">
            <span>{{ stravaError }}</span>
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
