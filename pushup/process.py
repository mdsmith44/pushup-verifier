"""Portable single-job worker: normalize, extract, replay, render and chart."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def run(command, log):
    subprocess.run(command, stdout=log, stderr=log, check=True, timeout=600)


def add_counts_panel(canvas, values, uncertain, partial):
    """Keep labels, counts and notes in separate rows using font metrics."""
    import cv2
    font = cv2.FONT_HERSHEY_SIMPLEX
    width = canvas.shape[1]
    column_width = width / 3
    labels = ('Completed', 'Accepted', 'Rejected')
    label_scale = min(1.1, width / 760)
    number_scale = min(2.0, width / 390)
    label_scale = min(label_scale, *(label_scale * (column_width - 16) /
        cv2.getTextSize(label, font, label_scale, 2)[0][0] for label in labels))
    # Fixed metrics keep frame dimensions constant as counts increase.
    number_scale = min(number_scale, number_scale * (column_width - 16) /
        cv2.getTextSize('9999', font, number_scale, 2)[0][0])
    (_, label_height), label_base = cv2.getTextSize('Completed', font, label_scale, 2)
    (_, number_height), number_base = cv2.getTextSize('0123456789', font, number_scale, 2)
    label_y = 16 + label_height
    number_y = label_y + label_base + 14 + number_height
    note_scale = min(.6, width / 1500)
    (_, note_height), note_base = cv2.getTextSize('Assessment', font, note_scale, 1)
    note_y = number_y + number_base + 16 + note_height
    note_step = note_height + note_base + 8
    panel_height = note_y + note_step + note_base + 28
    top = canvas.shape[0]
    canvas = cv2.copyMakeBorder(canvas, 0, panel_height, 0, 0,
        cv2.BORDER_CONSTANT, value=(20, 20, 20))
    for column, (label, value) in enumerate(zip(labels, values)):
        center = round((column + .5) * column_width)
        for text, scale, y in ((label, label_scale, label_y), (str(value), number_scale, number_y)):
            text_width = cv2.getTextSize(text, font, scale, 2)[0][0]
            cv2.putText(canvas, text, (center - text_width // 2, top + y),
                font, scale, (255, 255, 255), 2, cv2.LINE_AA)
    notes = (
        f'Unassessable segments: {uncertain} | Partial returns: {partial}',
        'Completed does not mean valid form. Experimental assessment.',
    )
    for index, text in enumerate(notes):
        text_width = cv2.getTextSize(text, font, note_scale, 1)[0][0]
        scale = min(note_scale, note_scale * (width - 24) / text_width)
        cv2.putText(canvas, text, (12, top + note_y + index * note_step),
            font, scale, (255, 255, 255), 1, cv2.LINE_AA)
    # H.264 requires even dimensions.
    if canvas.shape[0] % 2:
        canvas = cv2.copyMakeBorder(canvas, 0, 1, 0, 0, cv2.BORDER_CONSTANT, value=(20, 20, 20))
    return canvas


def render(video, observations, report, side, destination):
    import cv2
    from .engine import Config
    from .overlay import annotate
    config=Config(**report['config'])
    cap=cv2.VideoCapture(str(video))
    writer=None
    try:
        for row in observations:
            ok, frame=cap.read()
            if not ok:
                raise ValueError('Observation/video frame mismatch')
            t=float(row['timestamp'])
            points=[(float(row[j+'_x']),float(row[j+'_y'])) for j in ('shoulder','elbow','wrist','hip','ankle')] if row['shoulder_x'] else None
            canvas=annotate(frame,points,float(row['elbow_angle']) if row['elbow_angle'] else '',float(row['body_angle']) if row['body_angle'] else '',float(row['confidence']),t,side,config)
            finished=[a for a in report['attempts'] if a['end_s']<=t]
            values=(sum(a.get('completed',False) and a.get('start_observed',True) for a in finished),sum(a['status']=='accepted' for a in finished),sum(a['status']=='rejected' for a in finished))
            partial=sum(a.get('completed',False) and not a.get('start_observed',True) for a in finished)
            uncertain=sum(a['status']=='unable_to_assess' for a in finished)
            canvas=add_counts_panel(canvas,values,uncertain,partial)
            if writer is None:
                writer=cv2.VideoWriter(str(destination),cv2.VideoWriter_fourcc(*'mp4v'),30,(canvas.shape[1],canvas.shape[0]))
                if not writer.isOpened():
                    raise RuntimeError('Video encoder unavailable')
            writer.write(canvas)
        if cap.read()[0]:
            raise ValueError('Extra video frames')
    finally:
        cap.release()
        if writer:
            writer.release()


def process(source, output, model, side):
    import cv2
    import imageio_ffmpeg
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    start=time.monotonic()
    if side not in ('left','right'):
        raise ValueError('Side must be left or right')
    if not model.is_file():
        raise ValueError('Pose model is not installed')
    output.mkdir(parents=True,exist_ok=True)
    report_path=output/'report.json'
    if report_path.exists():
        raise FileExistsError('Use a new job directory')
    cap=cv2.VideoCapture(str(source))
    fps=cap.get(cv2.CAP_PROP_FPS)
    frames=cap.get(cv2.CAP_PROP_FRAME_COUNT)
    width,height=cap.get(cv2.CAP_PROP_FRAME_WIDTH),cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    valid=cap.isOpened()
    cap.release()
    if not valid or not all(math.isfinite(x) and x>0 for x in (fps,frames,width,height)):
        raise ValueError('Cannot read video metadata')
    if frames/fps>120 or width*height>4096*2160:
        raise ValueError('Use a clip up to 120 seconds and 4K resolution')
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    normalized=output/'normalized.mp4'
    raw=output/'render.mp4'
    csv_path=output/'observations.csv'
    config=ROOT/'config/pilot2_frozen.json'
    with (output/'processing.log').open('w') as log:
        # Normalize phone rotation, variable frame rate, dimensions, and codecs.
        run([ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-y','-threads','2','-protocol_whitelist','file,pipe','-i',str(source),'-t','121','-map','0:v:0','-vf',"scale=1280:1280:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=30",'-an','-map_metadata','-1','-c:v','libx264','-threads','2','-pix_fmt','yuv420p',str(normalized)],log)
        probe=cv2.VideoCapture(str(normalized))
        duration=probe.get(cv2.CAP_PROP_FRAME_COUNT)/30
        probe.release()
        if duration>120 or duration<=0:
            raise ValueError('Decoded video must be between 0 and 120 seconds')
        run([sys.executable,'-m','pushup.extract',str(normalized),'--model',str(model),'--side',side,'--config',str(config),'--include-landmarks','--include-confidence','--output',str(csv_path)],log)
        run([sys.executable,'-m','pushup.replay',str(csv_path),'--config',str(config),'--mode','temporal','--separate-alignment','--partial-start','--output',str(report_path)],log)
        report=json.loads(report_path.read_text())
        with csv_path.open() as f:
            observations=list(csv.DictReader(f))
        render(normalized,observations,report,side,raw)
        run([ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-y','-i',str(raw),'-c:v','libx264','-threads','2','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart','-an','-map_metadata','-1',str(output/'annotated.mp4')],log)
    fig,ax=plt.subplots(figsize=(11,4.5),layout='constrained')
    ax.plot([float(r['timestamp']) for r in observations],[float(r['elbow_angle']) if r['elbow_angle'] else float('nan') for r in observations],label='Measured elbow angle',color='royalblue')
    for value,color,label in ((report['config']['bottom_angle'],'green','Depth'),(report['config']['top_angle'],'red','Top')):
        ax.axhline(value,color=color,linestyle='--',label=f'{label} threshold: {value:g}°')
    ax.set(title=f'{side.title()} elbow angle throughout the recording',xlabel='Time (seconds)',ylabel='Elbow angle (degrees)',ylim=(0,180))
    ax.grid(alpha=.2)
    ax.legend()
    fig.savefig(output/'chart.png',dpi=150)
    plt.close(fig)
    report['input']='uploaded video'
    report['deployment']={'side':side,'normalized_fps':30,'max_dimension':1280,'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),'processing_seconds':round(time.monotonic()-start,2),'versions':{p:importlib.metadata.version(p) for p in ('mediapipe','opencv-python','matplotlib')}}
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    normalized.unlink()
    raw.unlink()
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--side',choices=('left','right'),required=True)
    a=p.parse_args()
    process(a.source.resolve(),a.output.resolve(),a.model.resolve(),a.side)
