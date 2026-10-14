"""在 ASCII 可写工作区执行官方在线素材命令，保存完整证据，不自动替代。"""
import argparse
import json
import sys
import tempfile
import uuid
from pathlib import Path


def execute(project, args, session=None):
    project = Path(project).resolve()
    sys.path.insert(0, str(project / 'engine'))
    import draftediting_runtime as runtime
    session = Path(session) if session else Path(tempfile.gettempdir()) / 'jy-online' / uuid.uuid4().hex
    session.mkdir(parents=True, exist_ok=True)
    if not str(session).isascii():
        raise ValueError('官方工作区必须使用 ASCII 路径')
    record = {'command': args, 'workspace': str(session), 'status': '未验证'}
    try:
        result = runtime.run_lyra(args, session, 300, [session], [], extra_env={
            'LYRA_CLI_ALLOW_DEV_JIANYING_APP': '1', 'DSH_LYRA_ALLOW_NETWORK': '1'})
        record.update(status='官方返回成功', envelope=result)
    except Exception as error:
        record.update(status='失败，禁止自动替代', error=str(error))
    record['files'] = [{'path': str(p), 'bytes': p.stat().st_size}
                       for p in session.rglob('*') if p.is_file() and p.name != 'evidence.json']
    (session / 'evidence.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description='官方在线素材搜索与下载验证')
    parser.add_argument('--project', required=True)
    parser.add_argument('--type', required=True)
    parser.add_argument('--prompt')
    parser.add_argument('--resource-id')
    parser.add_argument('--limit', type=int, default=5)
    options = parser.parse_args()
    session = Path(tempfile.gettempdir()) / 'jy-online' / uuid.uuid4().hex
    if options.resource_id:
        args = ['material', 'download', '--type', options.type, '--resource-id', options.resource_id,
                '--resource-dir', str(session / 'downloads')]
    elif options.prompt:
        args = ['material', 'search', '--type', options.type, '--prompt', options.prompt,
                '--limit', str(options.limit)]
    else:
        parser.error('请指定搜索词或资源 ID')
    record = execute(options.project, args, session)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['status'] == '官方返回成功' else 1


if __name__ == '__main__':
    raise SystemExit(main())
