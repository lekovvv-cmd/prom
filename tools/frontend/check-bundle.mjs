import { readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..", "..");
const assetsDirectory = resolve(root, "apps/platform-shell/dist/assets");
const assets = readdirSync(assetsDirectory).map((name) => ({
  name,
  bytes: statSync(resolve(assetsDirectory, name)).size,
}));

const mainJavaScript = assets.find((asset) => /^main-.*\.js$/.test(asset.name));
const mainCss = assets.find((asset) => /^main-.*\.css$/.test(asset.name));
const javascriptAssets = assets.filter((asset) => asset.name.endsWith(".js"));
const cssAssets = assets.filter((asset) => asset.name.endsWith(".css"));
const lazyJavaScriptAssets = javascriptAssets.filter(
  (asset) => asset !== mainJavaScript,
);
const largestJavaScript = lazyJavaScriptAssets.reduce((largest, asset) =>
  asset.bytes > largest.bytes ? asset : largest,
);
const largestCss = cssAssets.reduce((largest, asset) =>
  asset.bytes > largest.bytes ? asset : largest,
);

const checks = [
  [mainJavaScript, 300_000, "initial JavaScript"],
  [mainCss, 30_000, "initial CSS"],
  [largestJavaScript, 60_000, "largest lazy JavaScript chunk"],
  [largestCss, 45_000, "largest CSS chunk"],
];
for (const [asset, budget, label] of checks) {
  if (!asset) throw new Error(`Could not find ${label} asset`);
  console.log(
    `${label}: ${asset.name} = ${asset.bytes} bytes (budget: ${budget})`,
  );
  if (asset.bytes > budget) {
    throw new Error(
      `${label} exceeded its budget by ${asset.bytes - budget} bytes`,
    );
  }
}
