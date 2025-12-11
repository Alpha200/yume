import axios from 'axios'

/**
 * Generate PKCE code verifier and challenge
 */
function generateCodeVerifier() {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder()
  const data = encoder.encode(verifier)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return btoa(String.fromCharCode(...new Uint8Array(hash)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

/**
 * Parse JWT token to get expiration time
 */
function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
    return JSON.parse(jsonPayload)
  } catch (e) {
    return null
  }
}

/**
 * API service for all dashboard data fetching
 */
const api = axios.create({
  baseURL: '/api'
})

// Add request interceptor to include auth token and handle refresh
api.interceptors.request.use(async config => {
  const token = localStorage.getItem('access_token')
  const refreshToken = localStorage.getItem('refresh_token')
  const expiresAt = localStorage.getItem('token_expires_at')
  
  // Check if token is about to expire (within 5 minutes)
  const shouldRefresh = expiresAt && Date.now() > (parseInt(expiresAt) - 5 * 60 * 1000)
  
  if (shouldRefresh && refreshToken) {
    try {
      // Get OIDC config
      const configResponse = await axios.get('/auth/config')
      const oidcConfig = configResponse.data
      
      // Refresh the token directly with Keycloak
      const formData = new URLSearchParams()
      formData.append('grant_type', 'refresh_token')
      formData.append('client_id', oidcConfig.client_id)
      formData.append('refresh_token', refreshToken)
      
      const response = await axios.post(oidcConfig.token_endpoint, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      
      const { access_token, refresh_token: new_refresh, expires_in } = response.data
      
      // Update tokens
      localStorage.setItem('access_token', access_token)
      if (new_refresh) {
        localStorage.setItem('refresh_token', new_refresh)
      }
      const newExpiresAt = Date.now() + (expires_in * 1000)
      localStorage.setItem('token_expires_at', newExpiresAt.toString())
      
      // Use new token
      config.headers.Authorization = `Bearer ${access_token}`
    } catch (error) {
      // Refresh failed, clear auth and redirect to login
      console.error('Token refresh failed:', error)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('token_expires_at')
      window.location.href = '/'
      return Promise.reject(error)
    }
  } else if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  return config
}, error => {
  return Promise.reject(error)
})

// Add response interceptor to handle 401 errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expired or invalid, clear auth and reload
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export const apiService = {
  /**
   * Get authentication configuration (bypasses auth interceptor)
   */
  async getAuthConfig() {
    const response = await axios.get('/auth/config')
    return response.data
  },

  /**
   * Start OAuth flow with PKCE
   */
  async startOAuthFlow() {
    const config = await this.getAuthConfig()
    
    // Validate config was received
    if (!config.authorization_endpoint) {
      throw new Error('OIDC configuration not available. Please check server logs.')
    }
    
    // Generate PKCE parameters
    const codeVerifier = generateCodeVerifier()
    const codeChallenge = await generateCodeChallenge(codeVerifier)
    
    // Generate state for CSRF protection
    const state = generateCodeVerifier()
    
    // Store for later use
    localStorage.setItem('oauth_code_verifier', codeVerifier)
    localStorage.setItem('oauth_state', state)
    
    // Build authorization URL with PKCE
    const redirectUri = `${window.location.origin}/`
    const authUrl = `${config.authorization_endpoint}?` +
      `client_id=${encodeURIComponent(config.client_id)}&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}&` +
      `response_type=code&` +
      `scope=${encodeURIComponent('openid profile email')}&` +
      `state=${encodeURIComponent(state)}&` +
      `code_challenge=${encodeURIComponent(codeChallenge)}&` +
      `code_challenge_method=S256`
    
    window.location.href = authUrl
  },

  /**
   * Exchange authorization code for tokens
   */
  async exchangeCodeForTokens(code, state) {
    const config = await this.getAuthConfig()
    const storedState = localStorage.getItem('oauth_state')
    const codeVerifier = localStorage.getItem('oauth_code_verifier')
    
    // Verify state
    if (state !== storedState) {
      throw new Error('Invalid OAuth state. Possible CSRF attack.')
    }
    
    // Exchange code for tokens with PKCE
    const formData = new URLSearchParams()
    formData.append('grant_type', 'authorization_code')
    formData.append('client_id', config.client_id)
    formData.append('code', code)
    formData.append('redirect_uri', `${window.location.origin}/`)
    formData.append('code_verifier', codeVerifier)
    
    const response = await axios.post(config.token_endpoint, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    
    // Clean up
    localStorage.removeItem('oauth_state')
    localStorage.removeItem('oauth_code_verifier')
    
    return response.data
  },

  /**
   * Logout
   */
  async logout() {
    const config = await this.getAuthConfig()
    const redirectUri = `${window.location.origin}/`
    
    return {
      logout_url: `${config.end_session_endpoint}?` +
        `client_id=${encodeURIComponent(config.client_id)}&` +
        `post_logout_redirect_uri=${encodeURIComponent(redirectUri)}`
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    const token = localStorage.getItem('access_token')
    
    if (!token) {
      return false
    }
    
    // Parse JWT to check expiration
    const payload = parseJwt(token)
    if (!payload || !payload.exp) {
      return false
    }
    
    // Check if token is expired (exp is in seconds, Date.now() is in milliseconds)
    return Date.now() < payload.exp * 1000
  },

  /**
   * Set tokens in localStorage
   */
  setTokens(accessToken, refreshToken) {
    localStorage.setItem('access_token', accessToken)
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    }
    
    // Parse access token to get expiration
    const payload = parseJwt(accessToken)
    if (payload && payload.exp) {
      localStorage.setItem('token_expires_at', (payload.exp * 1000).toString())
    }
  },

  /**
   * Clear authentication
   */
  clearAuth() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')
  },

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
  },

  /**
   * Fetch day plan for a specific date
   */
  async getDayPlan(date) {
    const response = await api.get(`/day-plans/${date}`)
    return response.data
  },

  /**
   * Fetch today's day plan
   */
  async getTodayPlan() {
    const response = await api.get('/day-plans/today')
    return response.data
  }
}
