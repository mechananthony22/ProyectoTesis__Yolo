import {defineConfig, devices} from '@playwright/test'
export default defineConfig({
 testDir:'./tests/e2e', fullyParallel:false, retries:process.env.CI?1:0,
 reporter:[['list'],['html',{open:'never'}]],
 use:{baseURL:'http://127.0.0.1:5173',trace:'retain-on-failure',screenshot:'only-on-failure'},
 projects:[{name:'chromium',use:{...devices['Desktop Chrome']}}],
 webServer:[
  {command:'python ../scripts/smoke_server.py',url:'http://127.0.0.1:8000/api/v1/datasets/',reuseExistingServer:false,timeout:60000},
  {command:'npm run dev -- --port 5173',url:'http://127.0.0.1:5173',reuseExistingServer:false,timeout:60000}
 ]
})
