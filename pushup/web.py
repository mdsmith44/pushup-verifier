"""Single-instance LOCAL preview server with persistent jobs and one worker.

Run on loopback only: python -m uvicorn pushup.web:app --host 127.0.0.1
Cloud deployment uses a separate durable task runner; this is not a public server.
"""
import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import re
import secrets
import signal
import shutil
import sqlite3
import subprocess
import sys
import threading
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('PUSHUP_DATA',ROOT/'results/web-jobs')).resolve()
MODEL=Path(os.environ.get('PUSHUP_MODEL',ROOT/'models/pose_landmarker_full.task')).resolve()
LIMIT=200*1024*1024
RETENTION=24*3600
FILES={'video':'annotated.mp4','chart':'chart.png','report':'report.json'}


def connection():
    db=sqlite3.connect(DATA/'jobs.sqlite',timeout=10)
    db.row_factory=sqlite3.Row
    return db


def initialize():
    DATA.mkdir(parents=True,exist_ok=True)
    with connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, side TEXT, state TEXT, created REAL, error TEXT)')
        db.execute("UPDATE jobs SET state='failed', error='Server restarted; please upload again.' WHERE state IN ('processing','uploading')")


def get_job(job_id):
    if not re.fullmatch('[a-f0-9]{32}',job_id):
        raise HTTPException(404,'Job not found')
    with connection() as db:
        row=db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
    if row is None:
        raise HTTPException(404,'Job not found or expired')
    return dict(row)


def cleanup():
    with connection() as db:
        expired=db.execute("SELECT id FROM jobs WHERE created<? AND state IN ('done','failed')",(time.time()-RETENTION,)).fetchall()
        for row in expired:
            shutil.rmtree(DATA/row['id'],ignore_errors=True)
            db.execute('DELETE FROM jobs WHERE id=?',(row['id'],))


def worker(stop):
    while not stop.is_set():
        cleanup()
        with connection() as db:
            row=db.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
            if row:
                db.execute("UPDATE jobs SET state='processing' WHERE id=?",(row['id'],))
        if not row:
            stop.wait(1)
            continue
        directory=DATA/row['id']
        try:
            with (directory/'worker.log').open('w') as log:
                command=[sys.executable,'-m','pushup.process',str(directory/'input.video'),'--output',str(directory/'output'),'--model',str(MODEL),'--side',row['side']]
                process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=log,start_new_session=True)
                deadline=time.monotonic()+1200
                while process.poll() is None:
                    if stop.wait(.5) or time.monotonic()>deadline:
                        if os.name=='posix':
                            os.killpg(process.pid,signal.SIGKILL)
                        else:
                            process.kill()
                        process.wait()
                        raise RuntimeError('Processing cancelled or timed out')
                if process.returncode:
                    raise RuntimeError('Worker failed')
            state,error='done',None
        except Exception:
            state,error='failed','Processing failed. Check the video format, framing, duration and resolution; then try again. Local diagnostic logs are available to the operator.'
        finally:
            (directory/'input.video').unlink(missing_ok=True)
        with connection() as db:
            db.execute('UPDATE jobs SET state=?,error=? WHERE id=?',(state,error,row['id']))


@asynccontextmanager
async def lifespan(app):
    initialize()
    stop=threading.Event()
    thread=threading.Thread(target=worker,args=(stop,),daemon=True)
    thread.start()
    yield
    stop.set()
    thread.join(timeout=2)


app=FastAPI(title='Pushup Verifier local preview',lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver'])


@app.middleware('http')
async def local_boundary(request,call_next):
    # Same-origin browser writes; no CORS enabled. Raw upload avoids multipart
    # spooling before the application byte limit can be enforced.
    if request.method in ('POST','DELETE'):
        origin=request.headers.get('origin')
        if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):
            return JSONResponse({'detail':'Cross-origin request denied'},status_code=403)
    response=await call_next(request)
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; frame-ancestors 'none'"
    return response


@app.get('/')
def home():
    return FileResponse(ROOT/'pushup/static/index.html')


@app.get('/static/{name}')
def static(name:str):
    if name not in ('app.js','style.css', 'pushup-example.png'):
        raise HTTPException(404)
    return FileResponse(ROOT/'pushup/static'/name)

@app.get('/demo/{kind}')
def demo_artifact(kind: str):
    demo_files = {
        'video': 'annotated.mp4',
        'chart': 'chart.png',
        'report': 'report.json',
    }

    if kind not in demo_files:
        raise HTTPException(404, 'Demo file not found')

    path = Path('/demo') / demo_files[kind]

    if not path.is_file():
        raise HTTPException(404, 'Demo file is not installed')

    return FileResponse(path)

@app.get('/health')
def health():
    return {'status':'ok','model_ready':MODEL.is_file()}


@app.post('/api/jobs',status_code=202)
async def upload(request:Request,side:str='right'):
    if side not in ('left','right'):
        raise HTTPException(422,'Choose left or right')
    if not MODEL.is_file():
        raise HTTPException(503,'Pose model is not installed')
    if request.headers.get('x-video-extension','').lower() not in ('.mov','.mp4'):
        raise HTTPException(415,'Choose a MOV or MP4 file')
    length=request.headers.get('content-length')
    if length and (not length.isdigit() or int(length)>LIMIT):
        raise HTTPException(413,'Maximum upload size is 200 MB')
    job_id=secrets.token_hex(16)
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('queued','processing','uploading')").fetchone()[0]>=3:
            raise HTTPException(429,'Queue is full. Please try again shortly.')
        db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)',(job_id,side,'uploading',time.time(),None))
    directory=DATA/job_id
    try:
        directory.mkdir()
        total=0
        async with asyncio.timeout(180):
            with (directory/'input.video').open('wb') as f:
                async for chunk in request.stream():
                    total+=len(chunk)
                    if total>LIMIT:
                        raise HTTPException(413,'Maximum upload size is 200 MB')
                    f.write(chunk)
        if not total:
            raise HTTPException(422,'The video is empty')
        with connection() as db:
            db.execute("UPDATE jobs SET state='queued' WHERE id=?",(job_id,))
    except BaseException:
        shutil.rmtree(directory,ignore_errors=True)
        with connection() as db:
            db.execute('DELETE FROM jobs WHERE id=?',(job_id,))
        raise
    return {'id':job_id,'state':'queued'}


@app.get('/api/jobs/{job_id}')
def status(job_id:str):
    row=get_job(job_id)
    result={'id':job_id,'state':row['state'],'error':row['error']}
    if row['state']=='done':
        result['report']=json.loads((DATA/job_id/'output/report.json').read_text())
    return result


@app.get('/api/jobs/{job_id}/files/{kind}')
def artifact(job_id:str,kind:str):
    row=get_job(job_id)
    if row['state']!='done' or kind not in FILES:
        raise HTTPException(404,'Result unavailable')
    return FileResponse(DATA/job_id/'output'/FILES[kind])


@app.delete('/api/jobs/{job_id}')
def delete(job_id:str):
    row=get_job(job_id)
    if row['state'] not in ('done','failed'):
        raise HTTPException(409,'Wait until processing finishes')
    shutil.rmtree(DATA/job_id,ignore_errors=True)
    with connection() as db:
        db.execute('DELETE FROM jobs WHERE id=?',(job_id,))
    return {'deleted':True}
