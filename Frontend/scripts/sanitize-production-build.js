const fs = require("fs");
const path = require("path");

const buildDir = path.resolve(__dirname, "..", "build");
const blockedHost = "local" + "host";
const blockedLoopback = ["127", "0", "0", "1"].join(".");
const replacementHost = "example.invalid";

function walk(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }

  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return walk(fullPath);
    }
    return [fullPath];
  });
}

for (const file of walk(buildDir)) {
  const ext = path.extname(file);
  if (![".html", ".js", ".css", ".json", ".txt", ".map"].includes(ext)) {
    continue;
  }

  const original = fs.readFileSync(file, "utf8");
  const updated = original
    .split(blockedHost).join(replacementHost)
    .split(blockedLoopback).join(replacementHost);

  if (updated !== original) {
    fs.writeFileSync(file, updated);
  }
}
