import { defineConfig } from 'vite'
import tailwindcss from "@tailwindcss/vite";
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), vue()],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8079',
        changeOrigin: true,
        rewrite: (path) => path
      }
    }
  }
})
