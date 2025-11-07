/**
 * Formatting utilities for the dashboard
 */

/**
 * Format a timestamp as relative time
 * @param {string|Date} timestamp - The timestamp to format
 * @returns {string} Formatted relative time
 */
export function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = Math.abs(now - date)
  const diffHours = diffMs / (1000 * 60 * 60)
  const diffDays = diffMs / (1000 * 60 * 60 * 24)
  const isFuture = date > now

  if (diffHours < 1) {
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    if (diffMinutes < 1) {
      return isFuture ? 'Starting soon' : 'Just now'
    }
    return isFuture ? `in ${diffMinutes}m` : `${diffMinutes}m ago`
  } else if (diffHours < 24) {
    const hours = Math.floor(diffHours)
    return isFuture ? `in ${hours}h` : `${hours}h ago`
  } else if (diffDays < 7) {
    const days = Math.floor(diffDays)
    return isFuture ? `in ${days}d` : `${days}d ago`
  } else {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

/**
 * Format memory type to display name
 * @param {string} type - The memory type
 * @returns {string} Formatted display name
 */
export function formatMemoryType(type) {
  const typeMap = {
    'user_preference': 'Preference',
    'user_observation': 'Observation',
    'reminder': 'Reminder'
  }
  return typeMap[type] || type
}

/**
 * Format agent type to display name
 * @param {string} type - The agent type
 * @returns {string} Formatted display name
 */
export function formatAgentType(type) {
  const typeMap = {
    'ai_engine': 'AI Engine',
    'memory_manager': 'Memory Manager',
    'ai_scheduler': 'AI Scheduler'
  }
  return typeMap[type] || type
}

