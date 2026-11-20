#!/usr/bin/env python3
"""Sample an explicitly supplied reference MP4 locally into dated keyframes.

This utility never retrieves media from URLs or republishes frames. The user
must supply a legitimately accessible original video file. The resulting
frame sheet is for visual analysis, not redistribution.

Usage:
  python3 scripts/extract_reference_frames.py /path/to/frucht_intro.mp4 --out /tmp/frucht-shots
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def probe(video):
    x=json.loads(command('ffprobe', '-v', 'error', '-select_streams', 'v:0',
                          '-show_entries', 'stream=width,height,r_frame_rate:format=duration',
                          '-of', 'json',str(video)))
    stream=x['streams'][0]
    n,d=map(int,stream['r_frame_rate'].split('/'))
    return {'duration_seconds':round(float(x['format']['duration']),3),
            'fps': round(n/d,5), 'width':stream['width'], 'height':stream['height']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('video',type=Path,help='Existing local reference film (MP4/MOV/WEBM)')
    p.add_argument('--out',type=Path,required=True,help='Local private output directory')
    p.add_argument('--interval',type=float,default=1.0,help='Seconds per sample, default 1.0')
    p.add_argument('--cols',type=int,default=5)
    args=p.parse_args()
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        p.error('ffmpeg and ffprobe are required')
    if not args.video.is_file(): p.error('Video file not found')
    if args.interval<=0 or args.interval>60 or args.cols<1 or args.cols>10: p.error('Invalid interval or columns')
    try: from PIL import Image, ImageOps, ImageDraw, ImageFont
    except ImportError: p.error('Pillow is required for contact sheets')
    args.out.mkdir(parents=True,exist_ok=True)
    metadata=probe(args.video)
    dur=metadata['duration_seconds']
    if dur<=0 or dur>3600: p.error('Video duration must be between 0 and 3600 seconds')
    if math.ceil(dur/args.interval)>600: p.error('Too many frames: increase interval')
    frame_dir=args.out/'frames'
    frame_dir.mkdir(exist_ok=True)
    samples=[]
    t=0.0
    i=0
    while t<dur:
        name=f'frame_{i:04d}_{t:06.2f}s.jpg'
        dest=frame_dir/name
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin',
                        '-ss',f'{t:.3f}','-i',str(args.video),'-frames:v','1','-q:v','3',
                        '-y',str(dest)],check=True)
        if not dest.exists(): raise RuntimeError(f'Missing frame at {t:.2f}s')
        samples.append({'time_seconds':round(t,3),'file':f'frames/{name}'})
        i+=1
        t=i*args.interval
    sheetw=260
    sheeth=180
    cols=args.cols
    rows=math.ceil(len(samples)/cols)
    sheet=Image.new('RGB',(cols*sheetw,rows*sheeth),(22,25,29))
    draw=ImageDraw.Draw(sheet)
    for i,s in enumerate(samples):
        img=Image.open(args.out/s['file']).convert('RGB')
        img.thumbnail((sheetw-12,sheeth-31))
        x=(i%cols)*sheetw+(sheetw-img.width)//2
        y=(i//cols)*sheeth+4
        sheet.paste(img,(x,y))
        draw.text(((i%cols)*sheetw+9,(i//cols)*sheeth+sheeth-23),
                  f"{s['time_seconds']:05.1f}s",fill=(245,245,245))
    sheet.save(args.out/'contact-sheet.jpg',quality=90)
    with args.video.open('rb') as f: metadata['source_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
    metadata.update({'source_filename':args.video.name,'sample_interval_seconds':args.interval,
                     'frame_count':len(samples),'frames':samples,
                     'copyright_note':'Research reference; do not commit captured frames or original video to public GitHub without author permission.'})
    (args.out/'reference-manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frames':len(samples),'contact_sheet':str(args.out/'contact-sheet.jpg'),
                      'manifest':str(args.out/'reference-manifest.json')},ensure_ascii=False))


if __name__=='__main__':main()