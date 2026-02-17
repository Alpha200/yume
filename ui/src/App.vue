<template>
  <div v-if="isAuthenticated" class="min-h-screen bg-base-100">
    <div class="navbar bg-base-200 sticky top-0 z-50">
      <!-- Left: Logo -->
      <div class="flex-1">
        <a class="btn btn-ghost text-xl">Yume Dashboard</a>
      </div>

      <!-- Middle: Desktop Tabs (hidden on mobile) -->
      <div class="flex-none hidden md:flex md:gap-1">
        <router-link
          to="/memories"
          class="btn btn-ghost"
          :class="{ 'btn-active': $route.path === '/memories' }"
        >
          Memory Store
        </router-link>
        <router-link
          to="/interactions"
          class="btn btn-ghost"
          :class="{ 'btn-active': $route.path === '/interactions' }"
        >
          Agent Interactions
        </router-link>
        <router-link
          to="/scheduler"
          class="btn btn-ghost"
          :class="{ 'btn-active': $route.path === '/scheduler' }"
        >
          Scheduler Logs
        </router-link>
        <router-link
          to="/planner"
          class="btn btn-ghost"
          :class="{ 'btn-active': $route.path === '/planner' }"
        >
          Day Planner
        </router-link>
        <router-link
          to="/preferences"
          class="btn btn-ghost"
          :class="{ 'btn-active': $route.path === '/preferences' }"
        >
          Preferences
        </router-link>
      </div>

      <!-- Right: Mobile Dropdown + Logout -->
      <div class="flex-none gap-2">
        <!-- Mobile Dropdown (visible on mobile only) -->
        <div class="dropdown dropdown-end md:hidden">
          <button ref="mobileMenuButton" class="btn btn-ghost" tabindex="0">
            ☰
          </button>
          <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box shadow border border-base-300 w-52">
            <li>
              <router-link
                to="/memories"
                :class="{ 'active': $route.path === '/memories' }"
                @click="closeDropdown()"
              >
                Memory Store
              </router-link>
            </li>
            <li>
              <router-link
                to="/interactions"
                :class="{ 'active': $route.path === '/interactions' }"
                @click="closeDropdown()"
              >
                Agent Interactions
              </router-link>
            </li>
            <li>
              <router-link
                to="/scheduler"
                :class="{ 'active': $route.path === '/scheduler' }"
                @click="closeDropdown()"
              >
                Scheduler Logs
              </router-link>
            </li>
            <li>
              <router-link
                to="/planner"
                :class="{ 'active': $route.path === '/planner' }"
                @click="closeDropdown()"
              >
                Day Planner
              </router-link>
            </li>
            <li>
              <router-link
                to="/preferences"
                :class="{ 'active': $route.path === '/preferences' }"
                @click="closeDropdown()"
              >
                Preferences
              </router-link>
            </li>
            <li><a class="pt-0"></a></li>
            <li>
              <button @click="logout" class="text-error">
                Logout
              </button>
            </li>
          </ul>
        </div>
        <!-- Desktop Logout -->
        <button @click="logout" class="btn btn-ghost btn-primary hidden md:inline-flex">Logout</button>
      </div>
    </div>

    <div class="max-w-6xl mx-auto px-4 py-6">
      <div v-if="error" class="alert alert-error mb-6 shadow-lg">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l-2-2m0 0l-2 2m2-2l2 2m2-2l2-2m0 0l-2-2m2 2l-2-2"/></svg>
        <span>{{ error }}</span>
      </div>

      <router-view @error="handleError" />
    </div>
  </div>
</template>

<script>
import { apiService } from './services/api'

export default {
  name: 'App',
  data() {
    return {
      isAuthenticated: false,
      error: null
    }
  },
  methods: {
    async login() {
      try {
        await apiService.startOAuthFlow()
      } catch (error) {
        this.error = 'Failed to initiate login: ' + error.message
        console.error('Login error:', error)
      }
    },
    async logout() {
      try {
        const response = await apiService.logout()
        apiService.clearAuth()
        window.location.href = response.logout_url
      } catch (error) {
        // Clear local auth anyway
        apiService.clearAuth()
        this.isAuthenticated = false
        console.error('Logout error:', error)
      }
    },
    handleOAuthCallback() {
      const urlParams = new URLSearchParams(window.location.search)
      const code = urlParams.get('code')
      const state = urlParams.get('state')
      
      if (code && state) {
        // Exchange code for tokens (state validation happens there)
        this.exchangeCodeForTokens(code, state)
        
        // Clean URL
        window.history.replaceState({}, document.title, '/')
        return true
      }
      
      return false
    },
    async exchangeCodeForTokens(code, state) {
      try {
        const tokens = await apiService.exchangeCodeForTokens(code, state)
        apiService.setTokens(tokens.access_token, tokens.refresh_token)
        this.isAuthenticated = true
      } catch (error) {
        this.error = 'Failed to exchange code for tokens: ' + error.message
        console.error('Token exchange error:', error)
        // Retry login on failure
        setTimeout(() => this.login(), 2000)
      }
    },
    handleError(error) {
      this.error = error
      // Auto-dismiss error after 5 seconds
      setTimeout(() => {
        this.error = null
      }, 5000)
    },
    closeDropdown() {
      // Close the mobile dropdown menu
      if (this.$refs.mobileMenuButton) {
        this.$refs.mobileMenuButton.blur()
      }
    }
  },
  async mounted() {
    // Check if we're returning from OAuth callback
    const hasCallback = this.handleOAuthCallback()
    
    // Check authentication status
    this.isAuthenticated = apiService.isAuthenticated()
    
    if (!this.isAuthenticated && !hasCallback) {
      // Not authenticated and not processing callback - auto-redirect to login
      await this.login()
    }
  }
}
</script>
