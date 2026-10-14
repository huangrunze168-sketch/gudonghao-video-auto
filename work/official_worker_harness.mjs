import { createServer } from "node:net";
import { randomBytes } from "node:crypto";
import { writeFileSync } from "node:fs";

const bridge = globalThis[Symbol.for("custom-agent.runtime-sandbox-bridge")];
const app = "C:\\Users\\Administrator\\AppData\\Local\\JianyingPro\\Apps\\11.5.0.14471";
const runtime = `${app}\\Resources\\canvas_agent\\runtime`;
const cwd = process.cwd();
const workspace = process.env.DRAFTEDITING_WORKSPACE || `${process.env.LOCALAPPDATA}\\Temp\\jianying-official-blueprint-probe`;
const vmId = `draftediting-worker-${Date.now()}`;
const sandboxSessionId = `session-${randomBytes(8).toString("hex")}`;
const token = randomBytes(32).toString("hex");
const endpoint = `\\\\.\\pipe\\jianying-draftediting-${process.pid}-${Date.now()}`;
const events = [];
const unsubscribe = bridge.subscribeEvents((event) => events.push(event));
const policy = JSON.parse(bridge.basePolicy().fullConfig);
policy.rules.push({ file_path: cwd, process_name: "", type: "read_write" });

let socket;
let buffer = "";
let resolveReady;
let resolveResponse;
const ready = new Promise((resolve) => (resolveReady = resolve));
const response = new Promise((resolve) => (resolveResponse = resolve));
const server = createServer((client) => {
  socket = client;
  client.setEncoding("utf8");
  client.on("data", (chunk) => {
    buffer += chunk;
    for (;;) {
      const pos = buffer.indexOf("\n");
      if (pos < 0) break;
      const line = buffer.slice(0, pos).trim();
      buffer = buffer.slice(pos + 1);
      if (!line) continue;
      const message = JSON.parse(line);
      if (message.type === "ready") resolveReady(message);
      if (message.type === "response" && message.requestId === "compile-1") resolveResponse(message);
    }
  });
});
await new Promise((resolve, reject) => {
  server.once("error", reject);
  server.listen(endpoint, resolve);
});

let finalResult;
let created;
try {
  const workerEnv = {
    CUSTOM_AGENT_SANDBOX_ENDPOINT: endpoint,
    CUSTOM_AGENT_SANDBOX_TOKEN: token,
    CUSTOM_AGENT_SANDBOX_SESSION_ID: sandboxSessionId,
    CUSTOM_AGENT_SANDBOX_VM_ID: vmId,
    CUSTOM_AGENT_SANDBOX_WORKER_GENERATION: "1",
    CUSTOM_AGENT_SANDBOX_POLICY_VERSION: "1",
    CUSTOM_AGENT_SANDBOX_OWNER: "0",
    CUSTOM_AGENT_PROCESS_NAME: "hub-agent-tool-worker",
    CUSTOM_AGENT_LYRA_CLI_COMMAND: `${app}\\lyra-cli.exe`,
  };
  const payload = Buffer.from(JSON.stringify({
    executablePath: `${app}\\bun-packaged-server.exe`,
    arguments: [`${runtime}\\hub-agent-tool-worker.mjs`],
    environment: Object.entries(workerEnv).map(([name, value]) => ({ name, value })),
  }), "utf8").toString("base64");
  const bootstrap = [
    "$ErrorActionPreference = 'Stop'",
    `$payloadJson = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('${payload}'))`,
    "$payload = $payloadJson | ConvertFrom-Json",
    "foreach ($entry in @($payload.environment)) { [Environment]::SetEnvironmentVariable([string]$entry.name, [string]$entry.value, [EnvironmentVariableTarget]::Process) }",
    "$startInfo = New-Object System.Diagnostics.ProcessStartInfo",
    "$startInfo.FileName = [string]$payload.executablePath",
    "$startInfo.Arguments = '" + `"${runtime}\\hub-agent-tool-worker.mjs"` + "'",
    "$startInfo.UseShellExecute = $false",
    "$targetProcess = [System.Diagnostics.Process]::Start($startInfo)",
    "$targetProcess.WaitForExit()",
    "exit [int]$targetProcess.ExitCode",
  ].join("\n");
  created = await bridge.createProcess({
    vmId,
    fullConfig: JSON.stringify(policy),
    executablePath: "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    arguments: ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", bootstrap],
    environment: [],
    currentDirectory: cwd,
    inheritParentEnvironment: true,
    inheritHandles: false,
  });
  const readyMessage = await Promise.race([
    ready,
    Bun.sleep(15000).then(() => { throw new Error("worker ready timeout"); }),
  ]);
  const now = Date.now();
  const request = {
    type: "request",
    protocolVersion: 2,
    requestId: "compile-1",
    sandboxSessionId,
    runId: "draftediting-run",
    toolCallId: "draftediting-tool",
    workerGeneration: 1,
    policyVersion: 1,
    sentAt: now,
    deadline: now + 60000,
    request: {
      sandboxSessionId,
      runId: "draftediting-run",
      toolCallId: "draftediting-tool",
      policyVersion: 1,
      toolId: "__sandbox_process_run",
      input: {
        command: `${app}\\lyra-cli.exe`,
        args: ["draft", "blueprint", "init", "--workspace", workspace],
        cwd,
        env: {},
        timeoutMs: 45000,
        label: "DraftEditing:blueprint-init",
        ownerRunId: "draftediting-run",
      },
      context: {},
    },
  };
  socket.write(`${JSON.stringify(request)}\n`);
  const responseMessage = await Promise.race([
    response,
    Bun.sleep(60000).then(() => { throw new Error("worker response timeout"); }),
  ]);
  finalResult = { created, readyMessage, responseMessage, events };
  socket.write(`${JSON.stringify({
    type: "shutdown",
    protocolVersion: 2,
    requestId: "shutdown-1",
    sandboxSessionId,
    workerGeneration: 1,
  })}\n`);
  await Bun.sleep(500);
} catch (error) {
  finalResult = { created, error: String(error), code: error?.code, stack: error?.stack, events };
} finally {
  writeFileSync("work/official-worker-result.json", JSON.stringify(finalResult, null, 2), "utf8");
  unsubscribe?.();
  socket?.destroy();
  server.close();
  await bridge.killProcess(vmId).catch(() => {});
  await bridge.shutdown();
}
