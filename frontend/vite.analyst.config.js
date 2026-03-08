import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist-analyst',
    rollupOptions: {
      input: resolve(__dirname, 'analyst.html'),
    },
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
