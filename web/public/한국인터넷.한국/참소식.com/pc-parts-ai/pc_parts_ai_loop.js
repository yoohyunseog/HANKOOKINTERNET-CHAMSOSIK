const path = require("path");
const { spawnSync } = require("child_process");

const DEFAULT_COLLECT_INTERVAL_SECONDS = 1800;
const DEFAULT_ASSEMBLY_INTERVAL_SECONDS = 60;
const SCRIPT_DIR = __dirname;
const COLLECTOR = path.join(SCRIPT_DIR, "pc_parts_chrome_collector.js");
const ANALYZER = path.join(SCRIPT_DIR, "pc_parts_research_bot.js");
const AUTO_UPLOAD = process.env.PC_PARTS_AUTO_UPLOAD !== "0";
const UPLOAD_SERVER = process.env.PC_PARTS_UPLOAD_SERVER || "root@211.45.162.155";
const REMOTE_DIR = process.env.PC_PARTS_REMOTE_DIR || "/var/www/chamsosik/pc-parts-ai";
const REMOTE_TMP = process.env.PC_PARTS_REMOTE_TMP || "/tmp/pc_parts_ai_upload";

function nowKst() {
  return new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString().replace("Z", "+09:00");
}

function scriptStamp(scriptPath) {
  try {
    const fs = require("fs");
    return new Date(fs.statSync(scriptPath).mtimeMs + 9 * 60 * 60 * 1000).toISOString().replace("Z", "+09:00");
  } catch {
    return "unknown";
  }
}

function runNodeScript(scriptPath, args = []) {
  console.log(`[pc-parts-ai-loop] 최신 JS 실행: ${path.basename(scriptPath)} updated=${scriptStamp(scriptPath)}`);
  const result = spawnSync(process.execPath, [scriptPath, ...args], {
    cwd: SCRIPT_DIR,
    encoding: "utf8",
    stdio: "inherit",
    windowsHide: true
  });
  if (result.status !== 0) {
    throw new Error(`${path.basename(scriptPath)} failed with exit code ${result.status}`);
  }
}

function runCommand(command, args) {
  const result = spawnSync(command, args, {
    cwd: SCRIPT_DIR,
    encoding: "utf8",
    stdio: "inherit",
    windowsHide: true
  });
  if (result.status !== 0) {
    throw new Error(`${command} failed with exit code ${result.status}`);
  }
}

function uploadToServer() {
  if (!AUTO_UPLOAD) {
    console.log("[pc-parts-ai-loop] upload skipped: PC_PARTS_AUTO_UPLOAD=0");
    return;
  }

  console.log(`[${nowKst()}] [pc-parts-ai-loop] 서버 업로드 시작`);
  runCommand("ssh", [UPLOAD_SERVER, `rm -rf ${REMOTE_TMP}`]);
  runCommand("ssh", [UPLOAD_SERVER, `mkdir -p ${REMOTE_TMP}`]);
  runCommand("scp", ["-r", path.join(SCRIPT_DIR, "*"), `${UPLOAD_SERVER}:${REMOTE_TMP}/`]);
  runCommand("ssh", [UPLOAD_SERVER, `sudo mkdir -p '${REMOTE_DIR}'`]);
  runCommand("ssh", [UPLOAD_SERVER, `sudo rsync -a --delete ${REMOTE_TMP}/ '${REMOTE_DIR}/'`]);
  runCommand("ssh", [UPLOAD_SERVER, `rm -rf ${REMOTE_TMP}`]);
  console.log(`[${nowKst()}] [pc-parts-ai-loop] 서버 업로드 완료: ${REMOTE_DIR}`);
}

async function runCollectAndAnalyze() {
  console.log(`[${nowKst()}] [pc-parts-ai-loop] Chrome 수집 시작`);
  runNodeScript(COLLECTOR);
  console.log(`[${nowKst()}] [pc-parts-ai-loop] AI 조립/N-B 분석 시작`);
  runNodeScript(ANALYZER, ["--reset-explored"]);
  uploadToServer();
  console.log(`[${nowKst()}] [pc-parts-ai-loop] 완료`);
}

async function runAssemblyOnly() {
  console.log(`[${nowKst()}] [pc-parts-ai-loop] AI 조립/N-B 계속 탐색 시작`);
  runNodeScript(ANALYZER);
  uploadToServer();
  console.log(`[${nowKst()}] [pc-parts-ai-loop] 조립 탐색 완료`);
}

async function run() {
  const loop = process.argv.includes("--loop");
  const collectIntervalIndex = process.argv.indexOf("--collect-interval");
  const legacyIntervalIndex = process.argv.indexOf("--interval");
  const assemblyIntervalIndex = process.argv.indexOf("--assembly-interval");
  const collectIntervalSeconds = collectIntervalIndex >= 0
    ? Number(process.argv[collectIntervalIndex + 1] || DEFAULT_COLLECT_INTERVAL_SECONDS)
    : legacyIntervalIndex >= 0
      ? Number(process.argv[legacyIntervalIndex + 1] || DEFAULT_COLLECT_INTERVAL_SECONDS)
      : DEFAULT_COLLECT_INTERVAL_SECONDS;
  const assemblyIntervalSeconds = assemblyIntervalIndex >= 0
    ? Number(process.argv[assemblyIntervalIndex + 1] || DEFAULT_ASSEMBLY_INTERVAL_SECONDS)
    : DEFAULT_ASSEMBLY_INTERVAL_SECONDS;
  const safeCollectIntervalSeconds = Math.max(300, Number.isFinite(collectIntervalSeconds) ? collectIntervalSeconds : DEFAULT_COLLECT_INTERVAL_SECONDS);
  const safeAssemblyIntervalSeconds = Math.max(15, Number.isFinite(assemblyIntervalSeconds) ? assemblyIntervalSeconds : DEFAULT_ASSEMBLY_INTERVAL_SECONDS);
  let nextCollectAt = 0;

  while (true) {
    try {
      const now = Date.now();
      if (!loop || now >= nextCollectAt) {
        await runCollectAndAnalyze();
        nextCollectAt = Date.now() + safeCollectIntervalSeconds * 1000;
      } else {
        await runAssemblyOnly();
      }
    } catch (error) {
      console.error(`[pc-parts-ai-loop] ${error.message}`);
    }

    if (!loop) break;
    const secondsToCollect = Math.max(0, Math.ceil((nextCollectAt - Date.now()) / 1000));
    console.log(`[pc-parts-ai-loop] next assembly search in ${safeAssemblyIntervalSeconds} seconds, next Chrome collect in ${secondsToCollect} seconds`);
    await new Promise((resolve) => setTimeout(resolve, safeAssemblyIntervalSeconds * 1000));
  }
}

run().catch((error) => {
  console.error(`[pc-parts-ai-loop] failed: ${error.message}`);
  process.exit(1);
});
