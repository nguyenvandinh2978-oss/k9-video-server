"""Personal MP4 server. Source workflow: Dung Nguyễn; implementation: K9."""
import json, os, pathlib, secrets, subprocess, sys, threading, time, uuid
from urllib.parse import urlsplit
from flask import Flask, request, session, jsonify, send_file
from downloader import canonical

ROOT = pathlib.Path(__file__).resolve().parent
DATA = pathlib.Path(os.environ.get('K9_DATA', str(ROOT / 'data'))).resolve()
DATA.mkdir(parents=True, exist_ok=True)
KEY = DATA / 'access-key.txt'
if not KEY.exists():
    with KEY.open('x', encoding='utf-8') as f: f.write(secrets.token_urlsafe(32))
    try: KEY.chmod(0o600)
    except OSError: pass
TOKEN = KEY.read_text(encoding='utf-8').strip()
app = Flask(__name__)
app.secret_key = TOKEN
app.config.update(MAX_CONTENT_LENGTH=4096, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Strict', PERMANENT_SESSION_LIFETIME=86400)
lock = threading.Lock()
jobs = {}
busy = False
failures = {}

@app.before_request
def guard():
    host = request.host.split(':')[0].lower()
    if host not in ('127.0.0.1','localhost') and not host.endswith('.ts.net'):
        return jsonify(error='Host không được phép.'), 403
    if request.method == 'POST':
        origin = request.headers.get('Origin')
        if origin and urlsplit(origin).netloc != request.host:
            return jsonify(error='Nguồn yêu cầu không hợp lệ.'), 403
        if not request.is_json:
            return jsonify(error='Cần JSON.'), 415
    if request.path not in ('/','/login') and not session.get('ok'):
        return jsonify(error='Vui lòng nhập mã truy cập.'), 401

@app.after_request
def headers(response):
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    return response

@app.get('/')
def home(): return send_file(ROOT/'index.html')

@app.post('/login')
def login():
    ip = request.remote_addr or 'unknown'
    now = time.monotonic()
    with lock:
        attempts = [t for t in failures.get(ip,[]) if now-t<60]
        if len(attempts)>=5: return jsonify(error='Chờ 60 giây rồi thử lại.'),429
        candidate = str((request.get_json(silent=True) or {}).get('key',''))
        if not secrets.compare_digest(candidate,TOKEN):
            failures[ip]=attempts+[now]
            return jsonify(error='Mã truy cập chưa đúng.'),401
        failures.pop(ip,None)
    session.clear(); session['ok']=True; session.permanent=True
    return jsonify(ok=True)

@app.post('/logout')
def logout():
    session.clear(); return jsonify(ok=True)

@app.get('/status')
def status():
    with lock: return jsonify(busy=busy,jobs=list(jobs.values()))

def perform(job_id,url,mode):
    global busy
    try:
        output = subprocess.run([sys.executable,str(ROOT/'downloader.py'),url,
            '--mode',mode,'--out',str(DATA/'videos')],capture_output=True,text=True,
            encoding='utf-8',errors='replace',timeout=1500,shell=False,
            env={**os.environ,'PYTHONIOENCODING':'utf-8'})
        lines=output.stdout.strip().splitlines()
        result=json.loads(lines[-1]) if lines else {}
        if output.returncode or result.get('status')!='verified':
            raise RuntimeError(result.get('message','Tải hoặc kiểm tra thất bại.'))
        p=pathlib.Path(result['path']).resolve()
        if p.parent != (DATA/'videos').resolve() or not p.is_file():
            raise RuntimeError('Không tìm thấy tệp đã kiểm tra.')
        with lock:
            jobs[job_id].update(state='done',bytes=result['bytes'],width=result['width'],
              height=result['height'],duration=result['duration'],audio=result['audio'])
    except Exception as e:
        # Never expose stderr, signed media URLs or credentials.
        message=str(e) if isinstance(e,RuntimeError) else 'Quá thời gian hoặc không kiểm tra được tệp. Thử lại sau.'
        with lock: jobs[job_id].update(state='error',message=message[:350])
    finally:
        with lock: busy=False

@app.post('/jobs')
def create_job():
    global busy
    data=request.get_json(silent=True) or {}
    try:
        ident,url=canonical(str(data.get('url','')))
        mode=data.get('mode','fast')
        if mode not in ('fast','sharp'): raise ValueError('Chế độ không hợp lệ.')
        if data.get('permitted') is not True: raise ValueError('Cần xác nhận quyền tải video.')
    except ValueError as e: return jsonify(error=str(e)),400
    with lock:
        if busy: return jsonify(error='Đang xử lý một video. Chờ xong rồi gửi tiếp.'),409
        if len(jobs)>=20: jobs.pop(next(iter(jobs)))
        job_id=uuid.uuid4().hex
        jobs[job_id]={'id':job_id,'video_id':ident,'mode':mode,'state':'working'}
        busy=True
    threading.Thread(target=perform,args=(job_id,url,mode),daemon=True).start()
    return jsonify(id=job_id),202

@app.get('/files/<job_id>')
def file(job_id):
    with lock: job=dict(jobs.get(job_id,{}))
    if job.get('state')!='done': return jsonify(error='Tệp chưa đạt kiểm tra.'),404
    p=DATA/'videos'/f"{job['video_id']}-{job['mode']}.mp4"
    if not p.is_file(): return jsonify(error='Tệp đã được di chuyển hoặc xoá.'),404
    return send_file(p,mimetype='video/mp4',as_attachment=True,download_name=p.name,conditional=True)

if __name__=='__main__':
    from waitress import serve
    print('K9 đang chạy: http://127.0.0.1:8765',flush=True)
    print('Mã truy cập nằm trong data/access-key.txt. Không gửi mã lên GitHub.',flush=True)
    serve(app,host='127.0.0.1',port=8765,threads=6)
