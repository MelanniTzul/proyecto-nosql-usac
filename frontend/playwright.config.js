import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e', workers: 1, timeout: 60000,
  outputDir: '../data/reports/etapa-6/playwright', reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5180', browserName: 'chromium', channel: 'chrome', headless: true,
    viewport: { width: 1440, height: 1000 }, launchOptions: { args: ['--no-sandbox', '--disable-dev-shm-usage'] }, trace: 'retain-on-failure' },
  webServer: [
    { command: '../.venv/bin/python -m uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port 8010', url: 'http://127.0.0.1:8010/api/health/databases', timeout: 60000, reuseExistingServer: false },
    { command: 'npm run dev', env: { FRONTEND_PORT: '5180', API_PROXY_TARGET: 'http://127.0.0.1:8010' }, url: 'http://127.0.0.1:5180', timeout: 60000, reuseExistingServer: false },
  ],
});
