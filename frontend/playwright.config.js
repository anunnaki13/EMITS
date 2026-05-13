const { defineConfig, devices } = require("@playwright/test");

const baseURL = process.env.VISUAL_SMOKE_BASE_URL || "http://127.0.0.1:3000";
const serverURL = new URL(baseURL).origin;

module.exports = defineConfig({
  testDir: "./e2e",
  outputDir: "test-results/visual-smoke",
  timeout: 45_000,
  expect: {
    timeout: 10_000
  },
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }]
  ],
  use: {
    baseURL,
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
    screenshot: "only-on-failure",
    trace: "retain-on-failure"
  },
  webServer: process.env.VISUAL_SMOKE_START_SERVER === "1"
    ? {
        command: "npm start",
        url: serverURL,
        reuseExistingServer: true,
        timeout: 120_000
      }
    : undefined,
  projects: [
    {
      name: "desktop-chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 }
      }
    },
    {
      name: "tablet-chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1024, height: 768 },
        deviceScaleFactor: 1,
        isMobile: false
      }
    }
  ]
});
