"""Render the selected portfolio demo from saved observations and decisions."""
import csv
import json
from pathlib import Path
import sys
import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pushup.engine import Config
from pushup.overlay import annotate


def main():
    with (ROOT/'data/observations/pilot3B_mixed_diagnostic.csv').open() as f:
        rows=list(csv.DictReader(f))
    report=json.loads((ROOT/'results/pilot3B_mixed_validation.json').read_text())
    config=Config(**report['config'])
    cap=cv2.VideoCapture(str(ROOT/'data/raw/pilot3B_mixed.mov'))
    if not cap.isOpened():
        raise RuntimeError('Cannot open source video')
    out=ROOT/'results/pilot3B_demo_render.mp4'
    if out.exists():
        raise FileExistsError(out)
    media=ROOT/'docs/media'
    media.mkdir(exist_ok=True)
    writer=None
    try:
        for i,r in enumerate(rows):
            ok,frame=cap.read()
            if not ok:
                raise RuntimeError('Video and observations differ in length')
            t=float(r['timestamp'])
            source_t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            if abs(source_t-t)>.003:
                raise RuntimeError('Video and observation timestamps differ')
            points=[(float(r[j+'_x']),float(r[j+'_y'])) for j in ('shoulder','elbow','wrist','hip','ankle')] if r['shoulder_x'] else None
            canvas=annotate(frame,points,float(r['elbow_angle']) if r['elbow_angle'] else '',float(r['body_angle']) if r['body_angle'] else '',float(r['confidence']),t,'right',config)
            canvas=cv2.copyMakeBorder(canvas,0,90,0,0,cv2.BORDER_CONSTANT,value=(20,20,20))
            finished=[a for a in report['attempts'] if a['end_s']<=t]
            accepted=sum(a['status']=='accepted' for a in finished)
            rejected=sum(a['status']=='rejected' for a in finished)
            last=f"Last decision: {finished[-1]['status']}" if finished else 'Waiting for first completed movement'
            for k,line in enumerate((f'Completed: {len(finished)}  |  Accepted: {accepted}  |  Rejected: {rejected}',last+'  |  Saved temporal replay', 'One participant, one fresh clip; not a general accuracy claim')):
                cv2.putText(canvas,line,(12,canvas.shape[0]-65+k*25),cv2.FONT_HERSHEY_SIMPLEX,min(.55,canvas.shape[1]/1500),(255,255,255),1,cv2.LINE_AA)
            if writer is None:
                writer=cv2.VideoWriter(str(out),cv2.VideoWriter_fourcc(*'mp4v'),cap.get(cv2.CAP_PROP_FPS),(canvas.shape[1],canvas.shape[0]))
                if not writer.isOpened():
                    raise RuntimeError('Cannot create video')
            writer.write(canvas)
            if i==len(rows)-1:
                if not cv2.imwrite(str(media/'validation-demo.png'),canvas):
                    raise RuntimeError('Cannot save preview')
        if cap.read()[0]:
            raise RuntimeError('Extra source frames')
    finally:
        cap.release()
        if writer:
            writer.release()
    print(f'Rendered {len(rows)} frames to {out}')


if __name__=='__main__':
    main()
