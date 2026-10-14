"""打印最近一次工作流层报告。"""
import glob
import json

path = sorted(glob.glob('work/functional-test/evidence/functional-workflow-*.json'))[-1]
data = json.load(open(path, encoding='utf-8'))
print('report', path)
print('context', json.dumps(data.get('context', {}), ensure_ascii=False)[:260])
print('summary', json.dumps(data['workflow']['summary'], ensure_ascii=False))
for step in data['workflow']['steps']:
    print(f"{step['step']:16s} {step['state']:22s} exit={step.get('exit_code')} "
          f"changed={step.get('draft_changed')}")
    if step['state'] != 'ok':
        print('     ', (step.get('message') or '')[:170])
    for key in ('found_ids', 'segment_ids', 'outputs', 'seed_steps'):
        if step.get(key):
            print(f"      {key}: {json.dumps(step[key], ensure_ascii=False)[:220]}")
