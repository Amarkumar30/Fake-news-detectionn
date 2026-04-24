import childProcess from "node:child_process";
import { fileURLToPath } from "node:url";
import { syncBuiltinESMExports } from "node:module";

function patchWindowsNetUseExec() {
  if (process.platform !== "win32") {
    return;
  }

  const originalExec = childProcess.exec;

  childProcess.exec = function patchedExec(command, options, callback) {
    let resolvedOptions = options;
    let resolvedCallback = callback;

    if (typeof resolvedOptions === "function") {
      resolvedCallback = resolvedOptions;
      resolvedOptions = undefined;
    }

    if (typeof command === "string" && command.trim().toLowerCase() === "net use") {
      queueMicrotask(() => {
        if (resolvedCallback) {
          resolvedCallback(new Error("Skipped `net use` probe on Windows."), "", "");
        }
      });

      return {
        kill() {},
        pid: undefined,
        stdin: null,
        stdout: null,
        stderr: null,
      };
    }

    return originalExec.call(this, command, resolvedOptions, resolvedCallback);
  };

  syncBuiltinESMExports();
}

async function main() {
  const tool = process.argv[2];
  if (!tool) {
    throw new Error("Missing CLI target. Expected `vite` or `vitest`.");
  }

  patchWindowsNetUseExec();

  if (tool === "vite") {
    process.argv = [
      process.argv[0],
      fileURLToPath(new URL("../node_modules/vite/bin/vite.js", import.meta.url)),
      ...process.argv.slice(3),
    ];
    await import("../node_modules/vite/bin/vite.js");
    return;
  }

  if (tool === "vitest") {
    process.argv = [
      process.argv[0],
      fileURLToPath(new URL("../node_modules/vitest/vitest.mjs", import.meta.url)),
      ...process.argv.slice(3),
    ];
    await import("../node_modules/vitest/vitest.mjs");
    return;
  }

  throw new Error(`Unsupported CLI target: ${tool}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
