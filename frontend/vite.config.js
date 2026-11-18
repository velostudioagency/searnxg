import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Point the dev UI at whichever port the API is running on.
// PowerShell:  $env:VITE_BACKEND_PORT = 8010; npm run dev
const backend = process.env.VITE_BACKEND_PORT || '8000'
const target = `http://localhost:${backend}`

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: Number(process.env.VITE_UI_PORT || 5173),
    proxy: {
      '/api': target,
      '/mcp': target,
      '/mcp-http': target,
    },
  },
  build: { outDir: 'dist', emptyOutDir: true },
})
