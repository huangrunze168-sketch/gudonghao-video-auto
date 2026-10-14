import json,pathlib,os,re,subprocess,sys,shutil
root=pathlib.Path.cwd(); live=pathlib.Path(r'C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft\测试 (1)'); job=root/'work'/'jypack-render-experiment-007'; src=root/'work'/'jypack-render-experiment-001'
if job.exists(): raise SystemExit('job exists')
job.mkdir(); j=json.loads((root/'work'/'live-测试 (1)-decrypted.json').read_text(encoding='utf-8'))
pat=re.compile(r'##_draftpath_placeholder_[^#]+_##[\\/]')
def rw(x):
 if isinstance(x,dict): return {k:rw(v) for k,v in x.items()}
 if isinstance(x,list): return [rw(v) for v in x]
 if isinstance(x,str): return pat.sub(live.resolve().as_posix()+'/',x)
 return x
j=rw(j); (job/'timeline.json').write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
helper=job/'native-export-helper.exe'; helper.write_bytes((src/'native-export-helper.exe').read_bytes())
env=dict(os.environ); env['JY_VIDEOEDITOR_DIR']=r'C:\Users\Administrator\AppData\Local\JianyingPro\Apps\11.5.0.14471'
with (job/'native.stdout.log').open('wb') as out,(job/'native.stderr.log').open('wb') as err:
 p=subprocess.run([str(helper),'timeline.json','render.mp4','1138','640','30','3000000','600'],cwd=job,env=env,stdout=out,stderr=err,timeout=630)
print('return',p.returncode,'size',(job/'render.mp4').stat().st_size if (job/'render.mp4').exists() else 0)
