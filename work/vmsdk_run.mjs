import { writeFileSync } from "node:fs";

const outputPath = "work/vmsdk-run-result.json";
const bridge = globalThis[Symbol.for("custom-agent.runtime-sandbox-bridge")];
const events = [];
const unsubscribe = bridge.subscribeEvents((event) => events.push(event));
const vmId = `draftediting-probe-${Date.now()}`;
const app = "C:\\Users\\Administrator\\AppData\\Local\\JianyingPro\\Apps\\11.5.0.14471";
let result;
try {
  const policy = JSON.parse(bridge.basePolicy().fullConfig);
  policy.rules.push({ file_path: process.cwd(), process_name: "", type: "read_write" });
  const created = await bridge.createProcess({
    vmId,
    fullConfig: JSON.stringify(policy),
    executablePath: `${app}\\bun.exe`,
    arguments: [`${process.cwd()}\\work\\vm_child_runner.mjs`],
    environment: [],
    currentDirectory: process.cwd(),
    inheritParentEnvironment: true,
    inheritHandles: false,
  });
  await Bun.sleep(10000);
  result = { created, events };
} catch (error) {
  result = { error: String(error), code: error?.code, stack: error?.stack, events };
} finally {
  unsubscribe?.();
  await bridge.killProcess(vmId).catch(() => {});
  writeFileSync(outputPath, JSON.stringify(result, (_key, value) => value instanceof Uint8Array ? Buffer.from(value).toString("utf8") : value, 2));
  await bridge.shutdown();
}
