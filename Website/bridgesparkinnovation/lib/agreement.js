import fs from "fs";
import path from "path";

export function getAgreementMarkdown() {
  const agreementPath = path.join(
    process.cwd(),
    "content",
    "software-development-automation-services-agreement.md",
  );
  return fs.readFileSync(agreementPath, "utf8");
}

export function markdownToBlocks(markdown) {
  const lines = markdown.split(/\r?\n/);
  const blocks = [];
  let list = [];

  function flushList() {
    if (list.length > 0) {
      blocks.push({ type: "ul", items: list });
      list = [];
    }
  }

  lines.forEach((line) => {
    const trimmed = line.trim();

    if (!trimmed || trimmed === "---") {
      flushList();
      return;
    }

    if (trimmed.startsWith("* ")) {
      list.push(trimmed.slice(2));
      return;
    }

    flushList();

    if (trimmed.startsWith("# ")) {
      blocks.push({ type: "h2", text: trimmed.slice(2) });
      return;
    }

    blocks.push({ type: "p", text: trimmed });
  });

  flushList();
  return blocks;
}
