<template>
  <div class="settings-container">
    <div class="settings-header">
      <h2>⚙️ Settings</h2>
      <p>Configure application settings</p>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <div v-if="successMessage" class="success">
      {{ successMessage }}
    </div>

    <!-- Empty state -->
    <div class="settings-section">
      <div class="section-header">
        <h3>⚙️ Settings</h3>
        <p class="section-description">
          No settings to configure at this time
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Settings',
  data() {
    return {
      error: null,
      successMessage: null
    }
  }
}
</script>

<style scoped>
.settings-container {
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-header h2 {
  color: #e4e4e7;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.settings-header p {
  color: #a1a1aa;
  font-size: 0.875rem;
}

.error {
  background: #7f1d1d;
  color: #fecaca;
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.success {
  background: #14532d;
  color: #bbf7d0;
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.settings-section {
  background: #18181b;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.section-header h3 {
  color: #e4e4e7;
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.section-description {
  color: #a1a1aa;
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}
</style>
