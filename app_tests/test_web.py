import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from pushup import web


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        model=root/'model.task'
        model.write_bytes(b'test')
        self.patches=[patch.object(web,'DATA',root/'jobs'),patch.object(web,'MODEL',model),patch.object(web,'worker',lambda stop:stop.wait())]
        for p in self.patches:p.start()
        self.client=TestClient(web.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None,None,None)
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def upload(self,content=b'fake',**kwargs):
        return self.client.post('/api/jobs?side=right',content=content,headers={'x-video-extension':'.MOV'},**kwargs)

    def test_queue_and_status(self):
        r=self.upload()
        self.assertEqual(r.status_code,202)
        job=r.json()['id']
        self.assertEqual(self.client.get('/api/jobs/'+job).json()['state'],'queued')
        self.assertEqual((web.DATA/job/'input.video').read_bytes(),b'fake')
        self.assertEqual(self.client.get('/api/jobs/'+job+'/files/video').status_code,404)

    def test_queue_bounded(self):
        for _ in range(3):self.assertEqual(self.upload().status_code,202)
        self.assertEqual(self.upload().status_code,429)

    def test_empty_and_large_upload_rejected_and_cleaned(self):
        self.assertEqual(self.upload(b'').status_code,422)
        with patch.object(web,'LIMIT',2):
            self.assertEqual(self.upload(b'abc').status_code,413)
        with web.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],0)

    def test_invalid_side_extension_and_origin(self):
        self.assertEqual(self.client.post('/api/jobs?side=bad').status_code,422)
        self.assertEqual(self.client.post('/api/jobs',content=b'x',headers={'x-video-extension':'.exe'}).status_code,415)
        self.assertEqual(self.client.post('/api/jobs',headers={'origin':'https://evil.invalid'}).status_code,403)
        self.assertEqual(self.client.get('/health',headers={'host':'evil.invalid'}).status_code,400)

    def test_unknown_id_and_artifact_allowlist(self):
        self.assertEqual(self.client.get('/api/jobs/not-a-job').status_code,404)
        job=self.upload().json()['id']
        self.assertEqual(self.client.get('/api/jobs/'+job+'/files/worker.log').status_code,404)

    def test_deletion_and_restart_recovery(self):
        job=self.upload().json()['id']
        self.assertEqual(self.client.delete('/api/jobs/'+job).status_code,409)
        with web.connection() as db:db.execute("UPDATE jobs SET state='processing'")
        web.initialize()
        self.assertEqual(web.get_job(job)['state'],'failed')
        self.assertEqual(self.client.delete('/api/jobs/'+job).status_code,200)
        self.assertFalse((web.DATA/job).exists())

    def test_expiration(self):
        job=self.upload().json()['id']
        with web.connection() as db:db.execute("UPDATE jobs SET state='done',created=?",(time.time()-90000,))
        web.cleanup()
        self.assertEqual(self.client.get('/api/jobs/'+job).status_code,404)
