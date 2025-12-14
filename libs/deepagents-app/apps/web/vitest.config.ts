import { defineConfig } from 'vitest/config'
export default defineConfig({ test: { environment: 'jsdom', globals: true, coverage: { enabled: true, lines: 0.8, functions: 0.8, branches: 0.8 } } })