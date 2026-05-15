/**
 * Capture README screenshots. Requires web dev server on :5173 (or WEB_URL).
 * Usage: node scripts/capture_screenshots.mjs
 */
import { createRequire } from "module";
import { mkdir } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const { chromium } = require("../web/node_modules/playwright");

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const docsDir = path.join(root, "docs");
const baseUrl = process.env.WEB_URL ?? "http://127.0.0.1:5173";

await mkdir(docsDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

await page.goto(`${baseUrl}/`);
await page.waitForTimeout(600);
await page.getByPlaceholder(/genes, diseases/i).fill("What is the link between BRCA1 and breast cancer?");
await page.getByRole("button", { name: "Ask" }).click();
await page.waitForTimeout(2500);
await page.screenshot({ path: path.join(docsDir, "screenshot-ask.png"), fullPage: true });

await page.goto(`${baseUrl}/graph/BRCA1`);
await page.waitForSelector(".graph-panel canvas", { timeout: 15000 });
await page.waitForTimeout(1200);
await page.locator(".graph-section").screenshot({
  path: path.join(docsDir, "screenshot-graph.png"),
});

await page.goto(`${baseUrl}/corpus`);
await page.waitForTimeout(800);
await page.screenshot({ path: path.join(docsDir, "screenshot-corpus.png"), fullPage: true });

await browser.close();
console.log("Screenshots saved to docs/");
