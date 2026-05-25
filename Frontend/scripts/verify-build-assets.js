const fs = require('fs');
const path = require('path');

const buildDir = path.resolve(__dirname, '..', 'build');
const indexPath = path.join(buildDir, 'index.html');
const manifestPath = path.join(buildDir, 'asset-manifest.json');

const missing = new Set();

const normalizeAssetPath = (assetPath) => {
  if (!assetPath || typeof assetPath !== 'string') return null;
  const cleanPath = assetPath.split('?', 1)[0].replace(/^\//, '');
  if (!cleanPath || cleanPath.startsWith('http://') || cleanPath.startsWith('https://')) return null;
  return path.join(buildDir, cleanPath);
};

const verifyAsset = (assetPath) => {
  const fullPath = normalizeAssetPath(assetPath);
  if (fullPath && !fs.existsSync(fullPath)) {
    missing.add(assetPath);
  }
};

if (!fs.existsSync(indexPath)) {
  throw new Error(`Build verification failed: missing ${indexPath}`);
}

const indexHtml = fs.readFileSync(indexPath, 'utf8');
const htmlAssetPattern = /(?:src|href)="([^"]+\.(?:js|css))"/g;
for (const match of indexHtml.matchAll(htmlAssetPattern)) {
  verifyAsset(match[1]);
}

if (fs.existsSync(manifestPath)) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  Object.values(manifest.files || {}).forEach(verifyAsset);
  (manifest.entrypoints || []).forEach(verifyAsset);
}

if (missing.size > 0) {
  const list = Array.from(missing).map((asset) => ` - ${asset}`).join('\n');
  throw new Error(`Build verification failed. Missing referenced assets:\n${list}`);
}

console.log('Build asset verification passed.');
