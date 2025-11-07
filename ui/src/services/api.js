import axios from 'axios'

/**
 * API service for all dashboard data fetching
 */
const api = axios.create({
  baseURL: '/api'
})

export const apiService = {
  /**
   * Fetch all actions
   */
  async getActions() {
    const response = await api.get('/actions')
    return response.data.reverse() // Show newest first
  },

  /**
   * Fetch all memories
   */
  async getMemories() {
    const response = await api.get('/memories')
    return response.data.sort((a, b) =>
      new Date(b.modified_at) - new Date(a.modified_at)
    ) // Show newest first
  },

  /**
   * Fetch all logs
   */
  async getLogs() {
    const response = await api.get('/logs')
    return response.data // Already sorted newest first from API
  },

  /**
   * Fetch all scheduled tasks
   */
  async getScheduledTasks() {
    const response = await api.get('/scheduled-tasks')
    return response.data.sort((a, b) => {
      if (!a.next_run_time) return 1
      if (!b.next_run_time) return -1
      return new Date(a.next_run_time) - new Date(b.next_run_time)
    }) // Sort by next run time
  },

  /**
   * Fetch all interactions
   */
  async getInteractions() {
    const response = await api.get('/interactions')
    return response.data // Already sorted newest first from API
  },

  /**
   * Fetch a single interaction by ID
   */
  async getInteractionDetail(interactionId) {
    const response = await api.get(`/interactions/${interactionId}`)
    return response.data
  }
}

