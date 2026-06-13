import { chromium } from 'playwright'

const pages = [
  { path: '/settings',          name: '01-settings-state-machine' },
  { path: '/settings?tab=custom-fields', name: '02-settings-custom-fields', click: () => null },
  { path: '/documents',         name: '03-documents' },
  { path: '/modules',           name: '04-modules' },
  { path: '/webhooks',          name: '05-webhooks' },
  { path: '/users',             name: '06-users' },
  { path: '/standup',           name: '07-standup' },
]

;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  const errors = []
  page.on('pageerror', e => errors.push(`PAGEERR ${e.message}`))
  page.on('console', m => { if (m.type() === 'error') errors.push(`CONSOLE ${m.text()}`) })
  for (const p of pages) {
    try {
      await page.goto(`http://localhost:5173${p.path}`, { waitUntil: 'networkidle', timeout: 15000 })
      await page.waitForTimeout(800)
      await page.screenshot({ path: `/tmp/codeseer-${p.name}.png`, fullPage: true })
      console.log(`OK ${p.name} (${p.path})`)
    } catch (e) {
      console.log(`FAIL ${p.name}: ${e.message}`)
    }
  }
  if (errors.length) {
    console.log('--- runtime errors ---')
    for (const e of errors) console.log(e)
  }
  await browser.close()
})()
