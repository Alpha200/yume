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
  
  // Check if we should format as just time (HH:MM) or relative time
  // If it's a date object without timezone info, treat as time-only
  const timeOnlyPattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/
  if (timeOnlyPattern.test(timestamp)) {
    // Return time in HH:MM format for day planner items
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  // Original relative time logic
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
 * Format a timestamp with date and time for memory entries
 * @param {string|Date} timestamp - The timestamp to format
 * @returns {string} Formatted date and time
 */
export function formatMemoryDateTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = Math.abs(now - date)
  const diffHours = diffMs / (1000 * 60 * 60)
  const diffDays = diffMs / (1000 * 60 * 60 * 24)
  const isFuture = date > now

  // Format the date and time
  const dateStr = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  })
  const timeStr = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })

  // Show relative time followed by actual date/time
  let relativeStr = ''
  if (diffHours < 1) {
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    if (diffMinutes < 1) {
      relativeStr = isFuture ? 'Starting soon' : 'Just now'
    } else {
      relativeStr = isFuture ? `in ${diffMinutes}m` : `${diffMinutes}m ago`
    }
  } else if (diffHours < 24) {
    const hours = Math.floor(diffHours)
    relativeStr = isFuture ? `in ${hours}h` : `${hours}h ago`
  } else if (diffDays < 7) {
    const days = Math.floor(diffDays)
    relativeStr = isFuture ? `in ${days}d` : `${days}d ago`
  }

  return relativeStr ? `${relativeStr} (${dateStr} ${timeStr})` : `${dateStr} ${timeStr}`
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

/**
 * Format a date object to a readable date string
 * @param {string|Date} dateString - The date to format
 * @returns {string} Formatted date string (e.g., "Saturday, December 7, 2025")
 */
export function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

/**
 * Format a date/time to a readable string
 * @param {string|Date} dateString - The date/time to format
 * @returns {string} Formatted date/time string
 */
export function formatDateTime(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
