/** Capture real SolarJEPA Streamlit UI without altering app styling or data.
 * Usage: node scripts/presentation/capture_dashboard.mjs [--detail-only]
 * Optional env: PLAYWRIGHT_MODULE, BROWSER_EXECUTABLE, DASHBOARD_URL, SOURCE_ROOT.
 */
import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
const require = createRequire(import.meta.url);
const playwrightModule = process.env.PLAYWRIGHT_MODULE ?? (process.env.RUNTIME_NODE_MODULES ? path.join(process.env.RUNTIME_NODE_MODULES, 'playwright') : 'playwright');
const browserExecutable = process.env.BROWSER_EXECUTABLE ?? '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser';
const sourceRoot = process.env.SOURCE_ROOT;
if (!sourceRoot) throw new Error('Set SOURCE_ROOT to the pinned analysis checkout');
const url = process.env.DASHBOARD_URL ?? 'http://127.0.0.1:8512/';
const assets = path.resolve('presentations/assets');
const { chromium } = require(playwrightModule);
await fs.mkdir(assets, { recursive: true });
const browser = await chromium.launch({ executablePath: browserExecutable, headless: true, args: ['--disable-extensions'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 1050 }, deviceScaleFactor: 1 });
const browserErrors = [];
page.on('pageerror', error => browserErrors.push(error.message));
const detailOnly = process.argv.includes('--detail-only');
const previous = detailOnly ? JSON.parse(await fs.readFile(path.join(assets, 'dashboard_capture_metadata.json'), 'utf8')) : null;
const captures = previous ? previous.captures.filter(c => !c.file.endsWith('dashboard_replay_detail.png')) : [];
async function waitForCharts(count) {
  await page.waitForFunction(n => {
    const plots = Array.from(document.querySelectorAll('.js-plotly-plot'));
    return plots.length >= n && plots.every(p => p.data?.length > 0 && p.querySelector('svg'));
  }, count, { timeout: 120000 });
}
async function capture(name, extra, height = 1000, clip = { x: 0, y: 0, width: 1600, height }) {
  const pixels = await page.screenshot({ path: path.join(assets, name), clip });
  const selectedPage = await page.getByRole('radio').evaluateAll(es => es.filter(e => e.checked).map(e => e.closest('label')?.innerText));
  captures.push({ file: `presentations/assets/${name}`, captured_utc: new Date().toISOString(), sha256: createHash('sha256').update(pixels).digest('hex'), selected_page: selectedPage, width: clip.width, height: clip.height, screenshot_clip: clip, ...extra });
}
try {
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.getByRole('heading', { name: 'GOES Solar X-Ray Flux Over Time', exact: true }).waitFor({ timeout: 120000 });
  await waitForCharts(1);
  if (!detailOnly) {
  await capture('dashboard_overview.png', { action: 'Initial Overview page', observed_records: 87840, cadence_seconds: 60, scope: '01 May 2024 00:00 – 30 June 2024 23:59 UTC; observed records before channel quality rejection' }, 955);
  await page.getByText('Data Explorer', { exact: true }).click();
  await page.getByRole('heading', { name: 'XRS-A and XRS-B comparison', exact: true }).waitFor({ timeout: 120000 });
  await waitForCharts(4);
  const explorerText = await page.locator('body').innerText();
  if (!explorerText.includes('It is not the original May–August histogram.')) throw new Error('Expected scope distinction missing');
  await capture('dashboard_explorer.png', { action: 'Clicked Data Explorer navigation label', scope: 'Interactive comparison and histogram use verified May–June native observations; added report sections below use the distinct full May–August selection', chart_count: await page.locator('.js-plotly-plot').count() }, 875);
  }
  await page.getByText('Model Results', { exact: true }).click();
  const runButton = page.getByRole('button', { name: 'Run saved-model inference', exact: true });
  await runButton.waitFor({ timeout: 120000 });
  await runButton.click();
  const success = 'Saved-model inference verified against the pinned forecast and metrics.';
  await page.getByText(success, { exact: true }).waitFor({ timeout: 120000 });
  await waitForCharts(2);
  const heading = page.getByRole('heading', { name: 'Saved-model inference · observed and forecast flux', exact: true });
  await heading.evaluate(el => el.scrollIntoView({ block: 'start' }));
  await page.mouse.move(20, 800);
  await page.waitForFunction(() => Array.from(document.querySelectorAll('h4')).some(e => e.textContent.includes('Saved-model inference') && e.getBoundingClientRect().top >= 50));
  const modelText = await page.locator('body').innerText();
  if (!detailOnly) await capture('dashboard_model_inference.png', { action: 'Clicked Model Results, then Run saved-model inference; scrolled actual saved-model inference heading into view', observed_success_message: success, section_heading: await heading.innerText(), scope: 'Single held-out forecast origin from saved classical parameters; retrospective realized future is displayed but not passed into inference', issue_context_caption: modelText.split('\n').find(t => t.startsWith('Issue time:')) }, 945);
  const headingRect = await heading.boundingBox();
  const firstPanelBottom = await page.locator('.js-plotly-plot').last().evaluate(el => el.getBoundingClientRect().y + el._fullLayout.yaxis._offset + el._fullLayout.yaxis._length);
  const detailClip = { x: Math.floor(headingRect.x - 60), y: Math.floor(headingRect.y - 12), width: Math.ceil(headingRect.width + 120), height: Math.ceil(firstPanelBottom + 8) - Math.floor(headingRect.y - 12) };
  await capture('dashboard_replay_detail.png', { action: 'Clicked Model Results and Run saved-model inference, then clipped the real heading, controls, success message and complete XRS-A subplot; sidebar and XRS-B excluded', observed_success_message: success, section_heading: await heading.innerText(), scope: 'Detail of the single held-out saved-model replay; XRS-A panel only', issue_context_caption: modelText.split('\n').find(t => t.startsWith('Issue time:')) }, detailClip.height, detailClip);
  const metadata = { captured_utc: new Date().toISOString(), source_url: url, source_root: sourceRoot, source_commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: sourceRoot, encoding: 'utf8' }).trim(), source_git_status: execFileSync('git', ['status', '--short'], { cwd: sourceRoot, encoding: 'utf8' }).trim(), browser: browser.version(), browser_executable: browserExecutable, headless: true, screenshot_method: 'Playwright native screenshot of real live Streamlit DOM; no CSS or data modification', browser_errors: browserErrors, captures };
  await fs.writeFile(path.join(assets, 'dashboard_capture_metadata.json'), JSON.stringify(metadata, null, 2) + '\n');
  console.log(JSON.stringify(metadata, null, 2));
} finally { await browser.close(); }
