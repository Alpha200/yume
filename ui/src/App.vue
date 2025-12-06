<template>
  <div class="container">
    <div class="header">
      <h1>🌙 Yume Dashboard</h1>
      <p>AI Actions & Memory Management</p>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <!-- Tabs Navigation -->
    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'memories' }"
        @click="switchTab('memories')"
      >
        🧠 Memory Store
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'actions' }"
        @click="switchTab('actions')"
      >
        ⚡ AI Actions
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'logs' }"
        @click="switchTab('logs')"
      >
        📋 System Logs
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'settings' }"
        @click="switchTab('settings')"
      >
        ⚙️ Settings
      </button>
    </div>

    <!-- Memory Section -->
    <Section
      v-if="activeTab === 'memories'"
      title="🧠 Memory Store"
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

    <!-- AI Actions Section -->
    <div v-if="activeTab === 'actions'">
      <Section
        title="📅 Next Scheduled Tasks"
        :items="scheduledTasks"
        :loading="loadingScheduledTasks"
        loadingMessage="Loading scheduled tasks..."
        emptyMessage="No scheduled tasks"
        @refresh="loadScheduledTasks"
      >
        <template #default="{ items }">
          <TaskItem v-for="task in items" :key="task.id" :task="task" />
        </template>
      </Section>

      <Section
        title="⚡ Recent AI Actions"
        :items="actions"
        :loading="loadingActions"
        loadingMessage="Loading actions..."
        emptyMessage="No actions recorded yet"
        @refresh="loadActions"
      >
        <template #default="{ items }">
          <ActionItem v-for="action in items" :key="action.timestamp" :action="action" />
        </template>
      </Section>

      <Section
        title="🤖 Agent Interactions"
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
    </div>

    <!-- Interaction Detail Modal -->
    <InteractionDetailModal
      :interaction="selectedInteraction"
      @close="closeInteractionDetail"
    />

    <!-- System Logs Section -->
    <Section
      v-if="activeTab === 'logs'"
      title="📋 System Logs"
      :items="logs"
      :loading="loadingLogs"
      loadingMessage="Loading logs..."
      emptyMessage="No logs available"
      @refresh="loadLogs"
    >
      <template #default="{ items }">
        <LogItem v-for="log in items" :key="log.timestamp" :log="log" />
      </template>
    </Section>

    <!-- Settings Section -->
    <Settings v-if="activeTab === 'settings'" />
  </div>
</template>

<script>
import { apiService } from './services/api'
import Section from './components/Section.vue'
import MemoryItem from './components/MemoryItem.vue'
import ActionItem from './components/ActionItem.vue'
import TaskItem from './components/TaskItem.vue'
import LogItem from './components/LogItem.vue'
import InteractionItem from './components/InteractionItem.vue'
import InteractionDetailModal from './components/InteractionDetailModal.vue'
import Settings from './components/Settings.vue'

export default {
  name: 'App',
  components: {
    Section,
    MemoryItem,
    ActionItem,
    TaskItem,
    LogItem,
    InteractionItem,
    InteractionDetailModal,
    Settings
  },
  data() {
    return {
      activeTab: 'memories',
      actions: [],
      memories: [],
      logs: [],
      scheduledTasks: [],
      interactions: [],
      selectedInteraction: null,
      loadingActions: false,
      loadingMemories: false,
      loadingLogs: false,
      loadingScheduledTasks: false,
      loadingInteractions: false,
      error: null
    }
  },
  methods: {
    async loadActions() {
      this.loadingActions = true
      this.error = null
      try {
        this.actions = await apiService.getActions()
      } catch (error) {
        this.error = 'Failed to load actions: ' + error.message
        console.error('Error loading actions:', error)
      } finally {
        this.loadingActions = false
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
    async loadLogs() {
      this.loadingLogs = true
      this.error = null
      try {
        this.logs = await apiService.getLogs()
      } catch (error) {
        this.error = 'Failed to load logs: ' + error.message
        console.error('Error loading logs:', error)
      } finally {
        this.loadingLogs = false
      }
    },
    async loadScheduledTasks() {
      this.loadingScheduledTasks = true
      this.error = null
      try {
        this.scheduledTasks = await apiService.getScheduledTasks()
      } catch (error) {
        this.error = 'Failed to load scheduled tasks: ' + error.message
        console.error('Error loading scheduled tasks:', error)
      } finally {
        this.loadingScheduledTasks = false
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
      } else if (tab === 'actions') {
        if (this.actions.length === 0) {
          this.loadActions()
        }
        if (this.scheduledTasks.length === 0) {
          this.loadScheduledTasks()
        }
        if (this.interactions.length === 0) {
          this.loadInteractions()
        }
      } else if (tab === 'logs' && this.logs.length === 0) {
        this.loadLogs()
      }
    }
  },
  async mounted() {
    // Load memories by default since that's the default tab
    await this.loadMemories()
  }
}
</script>

<style scoped>
.container {
  max-width: 100%;
  padding: 1rem;
  margin: 0 auto;
}

@media (min-width: 768px) {
  .container {
    max-width: 768px;
    padding: 2rem;
  }
}

.header {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #27272a;
}

.header h1 {
  color: #a855f7;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

@media (min-width: 768px) {
  .header h1 {
    font-size: 2rem;
  }
}

.header p {
  color: #71717a;
  font-size: 0.875rem;
}

.tabs {
  display: flex;
  margin-bottom: 2rem;
  background: #18181b;
  border-radius: 0.75rem;
  border: 1px solid #27272a;
  overflow: hidden;
}

.tab {
  flex: 1;
  padding: 1rem;
  background: transparent;
  border: none;
  color: #71717a;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border-right: 1px solid #27272a;
}

.tab:last-child {
  border-right: none;
}

.tab:hover {
  background: #1c1c1e;
  color: #e4e4e7;
}

.tab.active {
  background: #a855f7;
  color: white;
}

.error {
  background: #dc2626;
  color: white;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}
</style>
