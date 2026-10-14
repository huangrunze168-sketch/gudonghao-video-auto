import json,pathlib,os,subprocess
root=pathlib.Path.cwd(); src=root/'work'/'jypack-render-experiment-001'; job=root/'work'/'jypack-render-experiment-003'
if job.exists(): raise SystemExit('job exists')
job.mkdir(); j=json.loads((src/'timeline.json').read_text(encoding='utf-8'))
main=next(t for t in j['tracks'] if t.get('type')=='video')
main['segments'][1]['target_timerange']['duration']=j['duration']
(job/'timeline.json').write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
helper=job/'native-export-helper.exe'; helper.write_bytes((src/'native-export-helper.exe').read_bytes())
env=dict(os.environ); env['JY_VIDEOEDITOR_DIR']=r'C:\Users\Administrator\AppData\Local\JianyingPro\Apps\11.5.0.14471'
with (job/'native.stdout.log').open('wb') as out,(job/'native.stderr.log').open('wb') as err:
 p=subprocess.run([str(helper),'timeline.json','render.mp4','1138','640','30','3000000','600'],cwd=job,env=env,stdout=out,stderr=err,timeout=630)
print('return',p.returncode,'size',(job/'render.mp4').stat().st_size if (job/'render.mp4').exists() else 0)
