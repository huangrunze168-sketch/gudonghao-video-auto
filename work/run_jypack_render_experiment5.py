import json,pathlib,os,subprocess,uuid,copy
root=pathlib.Path.cwd(); src=root/'work'/'jypack-render-experiment-001'; job=root/'work'/'jypack-render-experiment-005'
j=json.loads((src/'timeline.json').read_text(encoding='utf-8'))
photo=copy.deepcopy(next(x for x in j['materials']['videos'] if x.get('type')=='photo'))
photo['id']=str(uuid.uuid4()).upper(); photo['path']=(job/'transparent.png').resolve().as_posix(); photo['width']=16; photo['height']=16; photo['material_name']='transparent-duration-anchor.png'; photo['duration']=j['duration']
j['materials']['videos'].append(photo)
seg={'id':str(uuid.uuid4()).upper(),'material_id':photo['id'],'target_timerange':{'start':j['duration'],'duration':j['duration']},'source_timerange':{'duration':j['duration']},'clip':{'flip':{},'scale':{'x':1,'y':1},'transform':{'x':0,'y':0}},'enable_adjust_mask':False,'enable_hsl':False,'extra_material_refs':[],'hdr_settings':{'mode':1},'render_timerange':{},'responsive_layout':{},'source':'segmentsourcenormal','track_attribute':1,'uniform_scale':{},'volume':0}
main=next(t for t in j['tracks'] if t.get('type')=='video'); main['segments'].append(seg)
(job/'timeline.json').write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
helper=job/'native-export-helper.exe'; helper.write_bytes((src/'native-export-helper.exe').read_bytes())
env=dict(os.environ); env['JY_VIDEOEDITOR_DIR']=r'C:\Users\Administrator\AppData\Local\JianyingPro\Apps\11.5.0.14471'
with (job/'native.stdout.log').open('wb') as out,(job/'native.stderr.log').open('wb') as err:
 p=subprocess.run([str(helper),'timeline.json','render.mp4','1138','640','30','3000000','600'],cwd=job,env=env,stdout=out,stderr=err,timeout=630)
print('return',p.returncode,'size',(job/'render.mp4').stat().st_size if (job/'render.mp4').exists() else 0)
