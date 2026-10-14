"use strict";

const fs = require("node:fs");
const path = require("node:path");

const root = __dirname;
const sourcePath = path.join(root, "rca_standardization_FY27.html");
const outputPath = path.join(root, "rca_standardization_FY27.shareable.html");
const scripts = [
  ["vendor/exceljs.min.js", path.join(root, "vendor", "exceljs.min.js")],
  ["rca_standardization_FY27.data.js", path.join(root, "rca_standardization_FY27.data.js")],
  ["rca_standardization.js", path.join(root, "rca_standardization.js")],
];

let html = fs.readFileSync(sourcePath, "utf8");
for (const [src, scriptPath] of scripts) {
  const tag = `<script src="${src}"></script>`;
  if (!html.includes(tag)) {
    throw new Error(`Expected script reference not found in ${sourcePath}: ${tag}`);
  }

  const script = fs.readFileSync(scriptPath, "utf8").replace(/<\/script/gi, "<\\/script");
  html = html.replace(tag, `<script>\n${script}\n</script>`);
}

fs.writeFileSync(outputPath, html, "utf8");
console.log(`Built ${outputPath}`);
