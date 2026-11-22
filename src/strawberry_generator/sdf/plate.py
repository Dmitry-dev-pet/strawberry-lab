"""Authenticate native frames; owner reference comparison is PRIVATE only."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[3];p=root/'build/sdf-slice-v1/final';sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();scene=sha(p/'strawberry-sdf.blend');kinds=['whole','plane','sphere','oblique','macro','plane-coarse'];plate=Image.new('RGB',(2700,1900),(22,25,28));draw=ImageDraw.Draw(plate);records=[]
for i,kind in enumerate(kinds):
 receipt=json.loads((p/f'{kind}.json').read_text());assert receipt['scene_sha256']==scene and receipt['png_sha256']==sha(p/f'{kind}.png');assert receipt['kind']==('plane' if kind=='plane-coarse' else kind);assert receipt['samples']==16 and receipt['resolution']==900 and receipt['voxel_mm']==(.32 if kind=='plane-coarse' else .20)
 image=Image.open(p/f'{kind}.png').convert('RGB');assert image.size==(900,900);x=i%3*900;y=i//3*950;plate.paste(image,(x,y+50));draw.text((x+16,y+15),f'{kind.upper()} | voxel {receipt["voxel_mm"]:.2f} mm | Cycles 900px / 16 samples',fill='white');records.append(receipt)
assert all(records[i]['camera']==records[0]['camera'] for i in [1,2,3,5]);assert records[1]['plane']==records[5]['plane'];plate.save(p/'comparison.png')
reference=root.parent/'strawberry-tissue-zones/build/visual-audit-report-pr33-20261121/reference';manifest=json.loads((reference/'reference-manifest.json').read_text());private=Image.new('RGB',(1800,1900),(22,25,28));d=ImageDraw.Draw(private)
for row,(time,ours) in enumerate([(4,'whole'),(10,'plane')]):
 frame=next(f for f in manifest['frames'] if f['time_seconds']==time);path=reference/frame['png'];assert sha(path)==frame['sha256'];im=Image.open(path).convert('RGB');im.thumbnail((900,900));private.paste(im,((900-im.width)//2,row*950+50));private.paste(Image.open(p/f'{ours}.png').convert('RGB'),(900,row*950+50));d.text((14,row*950+15),f'PRIVATE owner Frucht reference {time:02}s | different camera/light, qualitative only',fill='white');d.text((915,row*950+15),f'Our SDF {ours} | original Cycles',fill='white')
private.save(p/'PRIVATE-reference-comparison.png');(p/'plate-qa.json').write_text(json.dumps({'all_six_slots_authenticated':True,'same_camera_primary_states':True,'same_pose_voxel_pair':True,'receipts':records,'reference_mp4_sha256':manifest['mp4_sha256'],'reference_times_seconds':[4,10],'reference_comparison_private_only':True},indent=2)+'\n')
