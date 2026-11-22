"""Authenticate six actual Cycles frames, then label without editing their pixels."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
p=Path('build/source-seam-v1');plate=Image.new('RGB',(2250,1580),(24,27,30));draw=ImageDraw.Draw(plate);receipts=[]
for row,seed in enumerate([101,202]):
    scene=hashlib.sha256((p/f'seed{seed}.blend').read_bytes()).hexdigest();pair=[]
    for col,(quality,look) in enumerate([('exact','beauty'),('fast','clay'),('exact','clay')]):
        stem=f'seed{seed}-{quality}-{look}';png=p/(stem+'.png');r=json.loads((p/(stem+'.json')).read_text())
        assert r['source_sha256']==scene and r['quality']==quality and r['look']==look and r['frame']=='cut'
        assert (r['resolution'],r['samples'],r['seed'])==(750,12,1729)
        assert r['png_sha256']==hashlib.sha256(png.read_bytes()).hexdigest()
        im=Image.open(png).convert('RGB');assert im.size==(750,750)
        plate.paste(im,(col*750,row*790+40));draw.text((col*750+12,row*790+12),f'Seed {seed} | {quality.upper()} {look} | physical blade +0.001 mm rest-Y',fill='white')
        receipts.append(r)
        if look=='clay':pair.append(r)
    assert pair[0]['knife']==pair[1]['knife'] and pair[0]['camera']==pair[1]['camera']
plate.save(p/'comparison.png');(p/'plate-qa.json').write_text(json.dumps({'authenticated_six_slots':True,'same_clay_camera_knife':True,'receipts':receipts},indent=2)+'\n')
