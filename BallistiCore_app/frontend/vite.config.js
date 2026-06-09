import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // host: true exposes the dev server on the LAN so a phone on the same Wi-Fi
    // can reach it at http://<your-PC-IP>:5173
    host: true,
    allowedHosts: ['slobbery-rocky-name.ngrok-free.dev'],
    // Forward API + health calls to the backend so the frontend can use
    // same-origin relative paths (works over localhost, LAN IP and ngrok).
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
