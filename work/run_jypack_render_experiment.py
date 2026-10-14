import io,json,os,pathlib,re,subprocess,sys,zipfile,hashlib
ROOT=pathlib.Path.cwd(); sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import jypack_inspect as ji
from windows_native_toolchain import compile_helper
import windows_runtime
src=pathlib.Path(r'C:\Users\Administrator\Desktop\剪映测试\测试.jypack')
job=ROOT/'work'/'jypack-render-experiment-001'
if job.exists(): raise SystemExit('job exists')
job.mkdir(parents=True); (job/'assets').mkdir(); (job/'compiler-tmp').mkdir()
raw,_=ji.decode_container(src.read_bytes())
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 name_map,_=ji.safe_names(z)
 timeline,_=ji.decrypt_timeline(z.read(name_map['draft_content.json']))
 replacements={}
 for logical,actual in name_map.items():
  if logical.endswith('/') or logical=='draft_content.json': continue
  b=z.read(actual); ext=pathlib.PurePosixPath(logical).suffix
  out=job/'assets'/(hashlib.sha256(logical.encode()).hexdigest()[:20]+ext)
  out.write_bytes(b)
  replacements[logical]=out.resolve().as_posix()
pat=re.compile(r'##_draftpath_placeholder_[^#]+_##[\\/]([^"\\]+)')
def rw(x):
 if isinstance(x,dict): return {k:rw(v) for k,v in x.items()}
 if isinstance(x,list): return [rw(v) for v in x]
 if isinstance(x,str):
  def sub(m):
   logical=m.group(1).replace('\\','/')
   if logical not in replacements: raise ValueError('missing '+logical)
   return replacements[logical]
  return pat.sub(sub,x)
 return x
timeline=rw(timeline)
(job/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
helper=job/'native-export-helper.exe'
result,toolchain=compile_helper(ROOT/'engine'/'native_export_windows.cpp',helper,job/'compiler-tmp')
(job/'compiler.stdout.log').write_bytes(result.stdout); (job/'compiler.stderr.log').write_bytes(result.stderr)
print('compile',result.returncode,toolchain)
if result.returncode: raise SystemExit(result.returncode)
runtime=windows_runtime.validate_runtime()
env=dict(os.environ); env['JY_VIDEOEDITOR_DIR']=runtime['install_dir']
cmd=[str(helper),'timeline.json','render.mp4','1138','640','30','3000000','600']
with (job/'native.stdout.log').open('wb') as out,(job/'native.stderr.log').open('wb') as err:
 p=subprocess.run(cmd,cwd=job,env=env,stdout=out,stderr=err,timeout=630)
print('render return',p.returncode,'exists',(job/'render.mp4').exists(),'size',(job/'render.mp4').stat().st_size if (job/'render.mp4').exists() else 0)
print((job/'native.stdout.log').read_text(encoding='utf-8',errors='replace')[-2000:])
print((job/'native.stderr.log').read_text(encoding='utf-8',errors='replace')[-2000:])
