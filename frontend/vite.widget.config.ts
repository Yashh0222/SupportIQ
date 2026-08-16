import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

const entry = fileURLToPath(new URL('src/embed-entry.tsx', import.meta.url))

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    lib: {
      entry,
      name: 'SupportIQ',
      formats: ['iife'],
      fileName: () => 'widget.js',
    },
    outDir: 'dist-widget',
    emptyOutDir: true,
    copyPublicDir: false,
    cssCodeSplit: false,
    sourcemap: true,
  },
})
