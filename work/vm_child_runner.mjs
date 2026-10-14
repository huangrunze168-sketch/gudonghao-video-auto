import { writeFileSync } from "node:fs";

const app = "C:\\Users\\Administrator\\AppData\\Local\\JianyingPro\\Apps\\11.5.0.14471";
const workspace = `${process.cwd()}\\work\\official-blueprint-probe`;
const proc = Bun.spawn(
  [`${app}\\lyra-cli.exe`, "draft", "blueprint", "init", "--workspace", workspace],
  { cwd: process.cwd(), stdout: "pipe", stderr: "pipe" },
);
const [stdout, stderr, exitCode] = await Promise.all([
  new Response(proc.stdout).text(),
  new Response(proc.stderr).text(),
  proc.exited,
]);
writeFileSync(
  "work/vm-child-result.json",
  JSON.stringify({ exitCode, stdout, stderr, workspace }, null, 2),
  "utf8",
);
