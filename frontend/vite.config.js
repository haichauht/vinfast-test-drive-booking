import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// TODO [BACKEND/ENV]: Frontend API clients should read VITE_API_BASE_URL and
// VITE_MAPS_PROVIDER_KEY from environment variables. Never hard-code secrets;
// browser map keys must be domain-restricted. See BACKEND_HANDOFF.md.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
})
