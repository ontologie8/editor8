// SPDX-License-Identifier: AGPL-3.0-or-later
import { defineConfig } from '@playwright/test';

const origin = 'http://127.0.0.1:18767';
const python = process.env.NAC_TEST_PYTHON || 'python';

export default defineConfig({
  testDir: './tests',
  testMatch: 'smoke.browser.spec.mjs',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: process.env.CI ? 'list' : 'line',
  use: {
    baseURL: origin,
    browserName: 'chromium',
    viewport: { width: 1440, height: 900 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: `"${python}" tests/smoke_server.py`,
    url: `${origin}/healthz`,
    reuseExistingServer: false,
    timeout: 30000,
  },
});
