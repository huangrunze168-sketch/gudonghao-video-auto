import { writeFileSync } from "node:fs";

const bridge = globalThis[Symbol.for("custom-agent.runtime-sandbox-bridge")];
const status = globalThis.__customAgentRuntimeAddonPreloadStatus;
writeFileSync(
  "work/bridge-probe.json",
  JSON.stringify(
    {
      status,
      bridgeKeys: bridge ? Object.keys(bridge) : [],
      capabilities: bridge?.capabilities?.(),
      basePolicy: bridge?.basePolicy?.(),
    },
    null,
    2,
  ),
  "utf8",
);
await bridge?.shutdown?.();
