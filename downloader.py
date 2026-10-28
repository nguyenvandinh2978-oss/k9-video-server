"""K9 extension; original workflow credit: Dung Nguyễn. No shell interpolation."""
import argparse, hashlib, importlib.util, json, pathlib, re, shutil, subprocess, sys, time
from urllib.parse import urlsplit, parse_qs

def canonical(url):
    u=urlsplit(url.strip())
    if u.scheme!='https' or u.username or u.password or u.port not in (None,443):
        raise ValueError('Chỉ nhận URL HTTPS YouTube hợp lệ.')
    host=u.hostname
    if host=='youtu.be': ident=u.path.strip('/')
    elif host in ('youtube.com','www.youtube.com','m.youtube.com'):
        if u.path=='/watch': ident=parse_qs(u.query).get('v',[''])[0]
        elif re.fullmatch(r'/(shorts|embed)/[A-Za-z0-9_-]{11}/?',u.path): ident=u.path.strip('/').split('/')[1]
        else: ident=''
    else: ident=''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',ident): raise ValueError('URL không hợp lệ; không nhận playlist.')
    return ident,'https://www.youtube.com/watch?v='+ident

def run(args, timeout=120):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout,shell=False)
    if p.returncode:
        err=p.stderr.lower()
        if '429' in err or 'too many requests' in err: raise RuntimeError('RATE_LIMIT')
        raise RuntimeError('Công cụ thất bại: mạng bị chặn, video không khả dụng hoặc định dạng không phù hợp. Không vượt quyền truy cập; không xuất nhật ký chứa URL media.')
    return p.stdout

def check_env():
    missing=[x for x in ('ffmpeg','ffprobe') if not shutil.which(x)]
    if not importlib.util.find_spec('yt_dlp'): missing.append('yt-dlp[default]')
    if missing: raise RuntimeError('Thiếu công cụ: '+', '.join(missing))

def verify(path, expected, cap):
    if not path.is_file() or path.stat().st_size==0: raise ValueError('Tệp rỗng hoặc không tồn tại.')
    data=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
    vs=[s for s in data['streams'] if s['codec_type']=='video']
    audio=any(s['codec_type']=='audio' for s in data['streams'])
    if not vs or (expected['audio'] and not audio): raise ValueError('Thiếu luồng hình/tiếng.')
    v=vs[0]; dur=float(data['format']['duration'])
    if min(v['width'],v['height'])>cap: raise ValueError('Vượt giới hạn độ phân giải.')
    if expected.get('width') and (v['width'],v['height'])!=(expected['width'],expected['height']): raise ValueError('Kích thước khác luồng nguồn.')
    if abs(dur-expected['duration'])>max(1,expected['duration']*.01): raise ValueError('Thời lượng không khớp.')
    run(['ffmpeg','-v','error','-xerror','-i',str(path),'-map','0:v:0','-map','0:a?','-f','null','-'],timeout=max(120,min(1800,int(dur*2))))
    return {'bytes':path.stat().st_size,'duration':dur,'width':v['width'],'height':v['height'],'audio':audio}

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def download(url,mode,out):
    ident,url=canonical(url); check_env(); start=time.monotonic()
    out=pathlib.Path(out).resolve(); out.mkdir(parents=True,exist_ok=True)
    cap=720 if mode=='fast' else 1080
    dest=out/f'{ident}-{mode}.mp4'; receipt=dest.with_suffix('.json')
    if dest.exists() and receipt.exists():
        r=json.loads(receipt.read_text())
        if r.get('id')==ident and r.get('mode')==mode and digest(dest)==r.get('sha256'):
            result=verify(dest,r['expected'],cap)
            return dict(status='verified',reused=True,path=str(dest),**result)
    if shutil.disk_usage(out).free<1024**3: raise RuntimeError('Cần tối thiểu 1 GB dung lượng trống.')
    base=[sys.executable,'-m','yt_dlp','--ignore-config','--no-plugin-dirs','--no-playlist','--socket-timeout','20','--retries','2','--fragment-retries','2','--extractor-retries','1','--abort-on-unavailable-fragments','--no-progress','--no-warnings']
    if shutil.which('node'): base+=['--js-runtimes','node']
    elif not shutil.which('deno'): raise RuntimeError('Thiếu JavaScript runtime: cài Node.js hoặc Deno.')
    meta=json.loads(run(base+['--dump-single-json','--skip-download','--',url],90))
    if meta.get('id')!=ident or meta.get('is_live') or not meta.get('duration'): raise ValueError('Không hỗ trợ live hoặc không xác minh được video.')
    fs=meta.get('formats',[])
    has_audio=any(f.get('acodec') not in (None,'none') for f in fs)
    videos=[f for f in fs if f.get('ext')=='mp4' and str(f.get('vcodec','')).startswith('avc1') and f.get('width') and f.get('height') and min(f['width'],f['height'])<=cap and not f.get('has_drm')]
    combined=[f for f in videos if f.get('acodec') not in (None,'none')]
    separate=[f for f in videos if f.get('acodec')=='none']
    audios=[f for f in fs if f.get('ext')=='m4a' and f.get('vcodec')=='none' and not f.get('has_drm')]
    key=lambda f:(min(f['width'],f['height']),f.get('fps') or 0,f.get('tbr') or 0)
    choices=combined if mode=='fast' and combined else combined+(separate if audios or not has_audio else [])
    if not choices: raise ValueError('Không có luồng MP4 H.264 tương thích trong giới hạn; không tự chuyển mã.')
    v=max(choices,key=key); fmt=str(v['format_id'])
    if v.get('acodec')=='none' and has_audio:
        a=max(audios,key=lambda f:f.get('abr') or 0); fmt+='+'+str(a['format_id'])
    expected={'audio':has_audio,'duration':float(meta['duration']),'width':v['width'],'height':v['height']}
    # Unique job folder prevents accidentally reusing an unverified destination.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='k9-job-',dir=out) as job:
        target=pathlib.Path(job)/'video.mp4'
        args=['-f',fmt,'--merge-output-format','mp4','--max-filesize','2G','-o',str(pathlib.Path(job)/'video.%(ext)s')]
        try: run(base+['-N','4']+args+['--',url],600)
        except RuntimeError as e:
            if str(e)!='RATE_LIMIT': raise
            time.sleep(5)
            run(base+['-N','1','--limit-rate','2M']+args+['--',url],600)
        result=verify(target,expected,cap)
        shutil.move(str(target),str(dest))
    r={'id':ident,'mode':mode,'expected':expected,'sha256':digest(dest)}
    receipt.write_text(json.dumps(r),encoding='utf-8')
    return dict(status='verified',reused=False,path=str(dest),elapsed_seconds=round(time.monotonic()-start,2),**result)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('url'); p.add_argument('--mode',choices=['fast','sharp'],default='fast'); p.add_argument('--out',default='downloads'); a=p.parse_args()
    try: print(json.dumps(download(a.url,a.mode,a.out),ensure_ascii=False))
    except Exception as e:
        message='Hết thời gian chờ; chưa có tệp đạt kiểm tra.' if isinstance(e,subprocess.TimeoutExpired) else str(e)
        print(json.dumps({'status':'failed','message':message},ensure_ascii=False)); sys.exit(1)
