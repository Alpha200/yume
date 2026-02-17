<template>
  <div v-if="isAuthenticated" class="min-h-screen bg-base-100">
    <div class="navbar bg-base-200 sticky top-0 z-50">
      <!-- Left: Logo -->
      <div class="flex-1">
        <a class="btn btn-ghost text-xl">Yume Dashboard</a>
      </div>

      <!-- Middle: Desktop Tabs (hidden on mobile) -->
      <div class="flex-none hidden md:flex md:gap-1">
        <button
          class="btn btn-ghost"
          :class="{ 'btn-active': activeTab === 'memories' }"
          @click="switchTab('memories')"
        >
          Memory Store
        </button>
        <button
          class="btn btn-ghost"
          :class="{ 'btn-active': activeTab === 'interactions' }"
          @click="switchTab('interactions')"
        >
          Agent Interactions
        </button>
        <button
          class="btn btn-ghost"
          :class="{ 'btn-active': activeTab === 'logs' }"
          @click="switchTab('logs')"
        >
          Scheduler Logs
        </button>
        <button
          class="btn btn-ghost"
          :class="{ 'btn-active': activeTab === 'planner' }"
          @click="switchTab('planner')"
        >
          Day Planner
        </button>
        <button
          class="btn btn-ghost"
          :class="{ 'btn-active': activeTab === 'preferences' }"
          @click="switchTab('preferences')"
        >
          Preferences
        </button>
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
              <button
                :class="{ 'active': activeTab === 'memories' }"
                @click="switchTab('memories'); closeDropdown()"
              >
                Memory Store
              </button>
            </li>
            <li>
              <button
                :class="{ 'active': activeTab === 'interactions' }"
                @click="switchTab('interactions'); closeDropdown()"
              >
                Agent Interactions
              </button>
            </li>
            <li>
              <button
                :class="{ 'active': activeTab === 'logs' }"
                @click="switchTab('logs'); closeDropdown()"
              >
                Scheduler Logs
              </button>
            </li>
            <li>
              <button
                :class="{ 'active': activeTab === 'planner' }"
                @click="switchTab('planner'); closeDropdown()"
              >
                Day Planner
              </button>
            </li>
            <li>
              <button
                :class="{ 'active': activeTab === 'preferences' }"
                @click="switchTab('preferences'); closeDropdown()"
              >
                Preferences
              </button>
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

    <!-- Memory Section -->
      <Section
        v-if="activeTab === 'memories'"
        title="Memory Store"
        :items="memories"
        :loading="loadingMemories"
        loadingMessage="Loading memories..."
        emptyMessage="No memories stored yet"
        @refresh="loadMemories"
      >
        <template #default="{ items }">
          <MemoryItem v-for="memory in items" :key="memory.id" :memory="memory" />
        </template>
      </Section>

      <!-- Agent Interactions Section -->
      <Section
        v-if="activeTab === 'interactions'"
        title="Agent Interactions"
        :items="interactions"
        :loading="loadingInteractions"
        loadingMessage="Loading interactions..."
        emptyMessage="No interactions recorded yet"
        @refresh="loadInteractions"
      >
        <template #default="{ items }">
          <InteractionItem
            v-for="interaction in items"
            :key="interaction.id"
            :interaction="interaction"
          />
        </template>
      </Section>

      <!-- Scheduler Logs Section -->
      <SchedulerRunsPanel v-if="activeTab === 'logs'" />

      <!-- Day Planner Section -->
      <DayPlanner v-if="activeTab === 'planner'" />

      <!-- Preferences Section -->
      <PreferencesPane v-if="activeTab === 'preferences'" />
    </div>
  </div>
</template>

<script>
import { apiService } from './services/api'
import Section from './components/Section.vue'
import MemoryItem from './components/MemoryItem.vue'
import InteractionItem from './components/InteractionItem.vue'
import DayPlanner from './components/DayPlanner.vue'
import PreferencesPane from './components/PreferencesPane.vue'
import SchedulerRunsPanel from './components/SchedulerRunsPanel.vue'

export default {
  name: 'App',
  components: {
    Section,
    MemoryItem,
    InteractionItem,
    DayPlanner,
    PreferencesPane,
    SchedulerRunsPanel
  },
  data() {
    return {
      isAuthenticated: false,
      activeTab: 'memories',
      memories: [],
      interactions: [],
      loadingMemories: false,
      loadingInteractions: false,
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
        
        // Load initial data
        await this.loadMemories()
      } catch (error) {
        this.error = 'Failed to exchange code for tokens: ' + error.message
        console.error('Token exchange error:', error)
        // Retry login on failure
        setTimeout(() => this.login(), 2000)
      }
    },
    async loadMemories() {
      this.loadingMemories = true
      this.error = null
      try {
        this.memories = await apiService.getMemories()
      } catch (error) {
        this.error = 'Failed to load memories: ' + error.message
        console.error('Error loading memories:', error)
      } finally {
        this.loadingMemories = false
      }
    },
    async loadInteractions() {
      this.loadingInteractions = true
      this.error = null
      try {
        this.interactions = await apiService.getInteractions()
      } catch (error) {
        this.error = 'Failed to load interactions: ' + error.message
        console.error('Error loading interactions:', error)
      } finally {
        this.loadingInteractions = false
      }
    },

    switchTab(tab) {
      this.activeTab = tab
      if (tab === 'memories' && this.memories.length === 0) {
        this.loadMemories()
      } else if (tab === 'interactions' && this.interactions.length === 0) {
        this.loadInteractions()
      }
    },
    handleTabFromUrl() {
      const urlParams = new URLSearchParams(window.location.search)
      const tab = urlParams.get('tab')
      if (tab) {
        this.activeTab = tab
      }
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
    
    // Check for tab parameter in URL
    this.handleTabFromUrl()
    
    // Check authentication status
    this.isAuthenticated = apiService.isAuthenticated()
    
    if (this.isAuthenticated) {
      // Load memories by default since that's the default tab
      await this.loadMemories()
    } else if (!hasCallback) {
      // Not authenticated and not processing callback - auto-redirect to login
      await this.login()
    }
  }
}
</script>
