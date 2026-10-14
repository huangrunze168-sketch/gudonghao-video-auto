"""诊断官方宿主查找：CIM 与 Get-Process 两条路径的实际返回。"""
import os
import subprocess

system_root = os.environ.get("SystemRoot", r"C:\Windows")
env = {key: os.environ[key] for key in ("TEMP", "TMP", "LOCALAPPDATA", "USERPROFILE")
       if key in os.environ}
env.update({"SystemRoot": system_root, "windir": system_root,
            "PATH": system_root + r"\System32"})

JY_EXE = r"C:\Users\Administrator\AppData\Local\JianyingPro\Apps\11.5.0.14471\JianyingPro.exe"

SCRIPTS = {
    "cim_all": r'''
Get-CimInstance Win32_Process -Filter "Name='JianyingPro.exe'" |
  Select-Object ProcessId, ParentProcessId, ExecutablePath |
  ConvertTo-Json -Compress
''',
    "cim_filtered": r'''
$items = Get-CimInstance Win32_Process -Filter "Name='JianyingPro.exe'" |
  Where-Object { $_.ExecutablePath -eq $env:JY_EXE } |
  Select-Object ProcessId, ParentProcessId, CommandLine
$items | ConvertTo-Json -Compress
''',
    "getprocess": r'''
$items = Get-Process -Name JianyingPro -ErrorAction SilentlyContinue |
  Select-Object Id, Path
$items | ConvertTo-Json -Compress
''',
}

for name, script in SCRIPTS.items():
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=dict(env, JY_EXE=JY_EXE), timeout=60,
    )
    print("=" * 20, name, "rc=", completed.returncode)
    print("stdout:", repr(completed.stdout[:1500]))
    print("stderr:", repr(completed.stderr[:1500]))
