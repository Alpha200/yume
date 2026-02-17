import { createRouter, createWebHistory } from 'vue-router'
import { apiService } from './services/api'

// Page components
import MemoriesPage from './pages/MemoriesPage.vue'
import InteractionsPage from './pages/InteractionsPage.vue'
import SchedulerLogsPage from './pages/SchedulerLogsPage.vue'
import DayPlannerPage from './pages/DayPlannerPage.vue'
import PreferencesPage from './pages/PreferencesPage.vue'

const routes = [
  {
    path: '/',
    redirect: '/memories'
  },
  {
    path: '/memories',
    name: 'memories',
    component: MemoriesPage
  },
  {
    path: '/interactions',
    name: 'interactions',
    component: InteractionsPage
  },
  {
    path: '/scheduler',
    name: 'scheduler',
    component: SchedulerLogsPage
  },
  {
    path: '/planner',
    name: 'planner',
    component: DayPlannerPage
  },
  {
    path: '/preferences',
    name: 'preferences',
    component: PreferencesPage
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
