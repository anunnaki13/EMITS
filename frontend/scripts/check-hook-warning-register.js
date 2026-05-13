#!/usr/bin/env node

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const frontendRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(frontendRoot, "..");
const registerPath = path.join(repoRoot, "docs", "quality", "REACT_HOOK_WARNINGS.md");

function normalizeWarningFile(filePath) {
  const cleaned = filePath.replace(/\\/g, "/").replace(/^\.\//, "");
  return cleaned.startsWith("frontend/") ? cleaned : `frontend/${cleaned}`;
}

function parseHookWarnings(output) {
  const normalized = output.replace(/\r\n/g, "\n");
  const warnings = [];
  const warningRegex = /((?:\.\/)?src\/[^\n]+?\.js)\n\s+Line\s+(\d+):\d+:\s+(React Hook[^\n]*react-hooks\/exhaustive-deps)/g;
  let match;

  while ((match = warningRegex.exec(normalized)) !== null) {
    warnings.push({
      file: normalizeWarningFile(match[1]),
      line: Number(match[2]),
      message: match[3].replace(/\s+/g, " ").trim()
    });
  }

  return warnings;
}

function parseRegister() {
  if (!fs.existsSync(registerPath)) {
    throw new Error(`Warning register not found: ${registerPath}`);
  }

  const register = fs.readFileSync(registerPath, "utf8");
  const documented = [];
  const rowRegex = /^\|\s*`(frontend\/src\/[^`|]+?\.js)`\s*\|\s*(\d+)\s*\|/gm;
  let match;

  while ((match = rowRegex.exec(register)) !== null) {
    documented.push({
      file: match[1],
      line: Number(match[2])
    });
  }

  return documented;
}

function idOf(warning) {
  return `${warning.file}:${warning.line}`;
}

function list(items) {
  return items.map((item) => `  - ${item}`).join("\n");
}

function runBuild() {
  const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
  const result = spawnSync(npmCommand, ["run", "build"], {
    cwd: frontendRoot,
    encoding: "utf8",
    env: {
      ...process.env,
      CI: process.env.CI || "false"
    }
  });

  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);

  if (result.status !== 0) {
    process.exit(result.status || 1);
  }

  return `${result.stdout || ""}\n${result.stderr || ""}`;
}

function main() {
  const output = runBuild();
  const actualWarnings = parseHookWarnings(output);
  const documentedWarnings = parseRegister();

  const actualIds = new Set(actualWarnings.map(idOf));
  const documentedIds = new Set(documentedWarnings.map(idOf));

  const unexpected = actualWarnings
    .map(idOf)
    .filter((id) => !documentedIds.has(id));
  const stale = documentedWarnings
    .map(idOf)
    .filter((id) => !actualIds.has(id));

  if (unexpected.length || stale.length) {
    console.error("\nReact hook warning register drift detected.");
    if (unexpected.length) {
      console.error("\nUndocumented build warnings:");
      console.error(list(unexpected));
    }
    if (stale.length) {
      console.error("\nStale register entries not emitted by build:");
      console.error(list(stale));
    }
    console.error(`\nUpdate ${path.relative(repoRoot, registerPath)} to match npm run build output.`);
    process.exit(1);
  }

  console.log(`\nReact hook warning register matches build output (${actualWarnings.length} warning${actualWarnings.length === 1 ? "" : "s"}).`);
}

main();
