import os,tempfile,unittest,pathlib,subprocess,json
from unittest.mock import patch
TMP=tempfile.TemporaryDirectory()
os.environ['K9_DATA']=TMP.name
import server
from downloader import canonical,verify

class ServerTest(unittest.TestCase):
    def setUp(self):
        self.c=server.app.test_client()
        server.jobs.clear();server.busy=False;server.failures.clear()
    def login(self):
        self.assertEqual(self.c.post('/login',json={'key':server.TOKEN}).status_code,200)
    def test_access_required(self):
        self.assertEqual(self.c.get('/status').status_code,401)
        self.assertEqual(self.c.get('/files/anything').status_code,401)
    def test_login_and_logout(self):
        self.login();self.assertEqual(self.c.get('/status').status_code,200)
        self.c.post('/logout',json={});self.assertEqual(self.c.get('/status').status_code,401)
    def test_bad_key_throttled(self):
        for _ in range(5):self.assertEqual(self.c.post('/login',json={'key':'bad'}).status_code,401)
        self.assertEqual(self.c.post('/login',json={'key':'bad'}).status_code,429)
    def test_cross_origin_blocked(self):
        self.assertEqual(self.c.post('/login',json={'key':server.TOKEN},headers={'Origin':'https://evil.example'}).status_code,403)
    def test_wrong_host(self):
        self.assertEqual(self.c.get('/',headers={'Host':'evil.example'}).status_code,403)
    def test_invalid_url(self):
        self.login()
        self.assertEqual(self.c.post('/jobs',json={'url':'https://evil.example','permitted':True}).status_code,400)
    def test_permission_required(self):
        self.login()
        self.assertEqual(self.c.post('/jobs',json={'url':'https://youtu.be/WhNIFLcvDUA'}).status_code,400)
    def test_busy(self):
        self.login();server.busy=True
        self.assertEqual(self.c.post('/jobs',json={'url':'https://youtu.be/WhNIFLcvDUA','permitted':True}).status_code,409)
    def test_job_created_without_shell(self):
        self.login()
        with patch.object(server.threading.Thread,'start'):
            r=self.c.post('/jobs',json={'url':'https://youtu.be/WhNIFLcvDUA','mode':'fast','permitted':True})
            self.assertEqual(r.status_code,202)
            self.assertEqual(self.c.get('/files/'+r.json['id']).status_code,404)
    def test_completed_job_download(self):
        self.login();v=pathlib.Path(TMP.name)/'videos';v.mkdir(exist_ok=True)
        target=v/'WhNIFLcvDUA-fast.mp4'
        subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=s=180x320:d=1','-f','lavfi','-i','sine=duration=1','-c:v','libx264','-c:a','aac','-shortest',str(target)],check=True)
        result=verify(target,{'audio':True,'duration':1,'width':180,'height':320},720)
        server.jobs['test']={'id':'test','video_id':'WhNIFLcvDUA','mode':'fast','state':'working'}
        payload={'status':'verified','path':str(target),**result}
        with patch.object(server.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(payload),'')):
            server.perform('test','https://youtu.be/WhNIFLcvDUA','fast')
        self.assertEqual(server.jobs['test']['state'],'done')
        r=self.c.get('/files/test');self.assertEqual(r.status_code,200)
        self.assertEqual(r.mimetype,'video/mp4');self.assertEqual(r.data,target.read_bytes());r.close()
    def test_failed_job_not_downloadable(self):
        self.login();server.jobs['bad']={'id':'bad','video_id':'WhNIFLcvDUA','mode':'fast','state':'working'}
        with patch.object(server.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'{"status":"failed","message":"Không khả dụng"}','')):
            server.perform('bad','https://youtu.be/WhNIFLcvDUA','fast')
        self.assertEqual(self.c.get('/files/bad').status_code,404)
    def test_urls(self):
        self.assertEqual(canonical('https://youtube.com/shorts/WhNIFLcvDUA?list=x')[0],'WhNIFLcvDUA')
        for u in ['https://youtube.com.evil.com/watch?v=WhNIFLcvDUA','https://youtube.com/playlist?list=x','https://a@youtube.com/watch?v=WhNIFLcvDUA']:
            with self.assertRaises(ValueError):canonical(u)

if __name__=='__main__':unittest.main()
