import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: false,
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://nfgxyb0os2.execute-api.us-east-1.amazonaws.com/dev',
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
