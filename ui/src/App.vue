<template>
  <div v-if="isAuthenticated" class="min-h-screen bg-base-100">
    <div class="navbar bg-base-200 sticky top-0 z-50">
      <div class="flex-1">
        <a class="btn btn-ghost text-xl">🌙 Yume Dashboard</a>
      </div>
      <div class="flex-none gap-2">
        <button @click="logout" class="btn btn-primary btn-sm">Logout</button>
      </div>
    </div>

    <div class="max-w-6xl mx-auto px-4 py-6">
      <div v-if="error" class="alert alert-error mb-6 shadow-lg">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l-2-2m0 0l-2 2m2-2l2 2m2-2l2-2m0 0l-2-2m2 2l-2-2"/></svg>
        <span>{{ error }}</span>
      </div>

      <!-- Tabs Navigation -->
      <div class="tabs tabs-bordered mb-6">
        <button
          class="tab"
          :class="{ 'tab-active': activeTab === 'memories' }"
          @click="switchTab('memories')"
        >
          Memory Store
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': activeTab === 'interactions' }"
          @click="switchTab('interactions')"
        >
          Agent Interactions
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': activeTab === 'logs' }"
          @click="switchTab('logs')"
        >
          Scheduler Logs
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': activeTab === 'planner' }"
          @click="switchTab('planner')"
        >
          Day Planner
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': activeTab === 'preferences' }"
          @click="switchTab('preferences')"
        >
          Preferences
        </button>
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
            @select="showInteractionDetail"
          />
        </template>
      </Section>

      <!-- Scheduler Logs Section -->
      <SchedulerRunsPanel v-if="activeTab === 'logs'" />

      <!-- Day Planner Section -->
      <DayPlanner v-if="activeTab === 'planner'" />

      <!-- Preferences Section -->
      <PreferencesPane v-if="activeTab === 'preferences'" />

      <!-- Interaction Detail Modal -->
      <InteractionDetailModal
        v-if="selectedInteraction"
        :interaction="selectedInteraction"
        @close="closeInteractionDetail"
      />
    </div>
  </div>
</template>

<script>
import { apiService } from './services/api'
import Section from './components/Section.vue'
import MemoryItem from './components/MemoryItem.vue'
import InteractionItem from './components/InteractionItem.vue'
import InteractionDetailModal from './components/InteractionDetailModal.vue'
import DayPlanner from './components/DayPlanner.vue'
import PreferencesPane from './components/PreferencesPane.vue'
import SchedulerRunsPanel from './components/SchedulerRunsPanel.vue'

export default {
  name: 'App',
  components: {
    Section,
    MemoryItem,
    InteractionItem,
    InteractionDetailModal,
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
      selectedInteraction: null,
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
    async showInteractionDetail(interactionId) {
      try {
        this.selectedInteraction = await apiService.getInteractionDetail(interactionId)
      } catch (error) {
        this.error = 'Failed to load interaction details: ' + error.message
        console.error('Error loading interaction details:', error)
      }
    },
    closeInteractionDetail() {
      this.selectedInteraction = null
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
