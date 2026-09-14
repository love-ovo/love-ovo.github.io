from __future__ import annotations
import argparse, json, os, time, urllib.parse, urllib.request, subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument('--task-id',required=True); p.add_argument('--output',required=True); a=p.parse_args()
    key=os.environ.get('MINIMAX_API_KEY')
    if not key: raise RuntimeError('缺少 MINIMAX_API_KEY')
    h={'Authorization':f'Bearer {key}'}
    q=urllib.request.Request('https://api.minimaxi.com/v1/query/video_generation?'+urllib.parse.urlencode({'task_id':a.task_id}),headers=h)
    with urllib.request.urlopen(q,timeout=60) as r: state=json.loads(r.read().decode())
    if state.get('status')!='Success': raise RuntimeError(json.dumps(state,ensure_ascii=False))
    f=urllib.request.Request('https://api.minimaxi.com/v1/files/retrieve?'+urllib.parse.urlencode({'file_id':state['file_id']}),headers=h)
    with urllib.request.urlopen(f,timeout=60) as r: info=json.loads(r.read().decode())
    url=info['file']['download_url']; out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    last=None
    for _ in range(5):
        try:
            result=subprocess.run(['curl.exe','--http1.1','-L','--retry','3','--retry-all-errors','--connect-timeout','30','--max-time','300',url,'-o',str(out)],capture_output=True,text=True)
            if result.returncode==0 and out.exists() and out.stat().st_size>0: print(out.resolve()); return 0
            raise RuntimeError(result.stderr[-500:])
        except Exception as e: last=e; time.sleep(3)
    raise last
if __name__=='__main__': raise SystemExit(main())
