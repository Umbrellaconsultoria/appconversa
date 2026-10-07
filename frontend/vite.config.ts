import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'

// Configuração do Vite com suporte a acesso por IP e proxy WebSocket
export default defineConfig({
  server: {
    host: true, // Libera o servidor para a rede local (0.0.0.0)
    proxy: {
      // Redireciona conexões WebSocket do frontend para o backend FastAPI
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
  },
  plugins: [
    react(),
    tailwindcss(),
    basicSsl()
  ],
})

