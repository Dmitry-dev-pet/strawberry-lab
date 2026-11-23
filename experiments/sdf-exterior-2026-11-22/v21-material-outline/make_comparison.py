"""Arrange original Cycles pixels; labels only, no image retouching or resizing."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(root, shot):
    paths = [root / f'cycles-v21{v}-{shot}.png' for v in ('a', 'b')]
    receipts = [json.loads(p.with_suffix('.json').read_text()) for p in paths]
    assert receipts[0]['settings'] == receipts[1]['settings'], shot
    for path, receipt in zip(paths, receipts):
        assert digest(path) == receipt['image_sha256'], path
    arrays = [np.asarray(Image.open(p).convert('RGB'), dtype=np.float32)/255 for p in paths]
    delta = np.abs(arrays[0]-arrays[1])
    return {'shot': shot, 'camera_light_render_settings_identical': True,
            'mean_absolute_srgb_difference': float(delta.mean()),
            'fraction_pixels_max_rgb_difference_gt_0_01': float((delta.max(axis=2)>.01).mean()),
            'interpretation': 'Image difference only, not a realism or accuracy score.'}


def montage(root, shots, size, name):
    header, band, footer = 88, 44, 44
    canvas = Image.new('RGB', (size*2, header+len(shots)*(size+band)+footer), '#181b1e')
    draw = ImageDraw.Draw(canvas)
    path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font = ImageFont.truetype(path, 20 if size == 640 else 28)
    small = ImageFont.truetype(path, 16 if size == 640 else 22)
    draw.text((16, 10), 'V21 | A: ORIGINAL OUTLINES    B: 80% LOWER COLOR-OUTLINE GAIN', font=font, fill='white')
    draw.text((16, 42), f'Actual Cycles | {size} px | identical geometry, bump, roughness, camera and light', font=small, fill='#c6d5dc')
    sources = []
    for row, shot in enumerate(shots):
        for col, variant in enumerate(('a', 'b')):
            file = root / f'cycles-v21{variant}-{shot}.png'
            im = Image.open(file).convert('RGB')
            assert im.size == (size, size), file
            x, y = col*size, header+row*(size+band)
            label = f'{variant.upper()} | {shot.upper()} | gain ' + ('0.10' if variant == 'a' else '0.02')
            draw.text((x+14, y+10), label, font=font, fill='white')
            canvas.paste(im, (x, y+band))
            sources.append({'file': file.name, 'sha256': digest(file), 'resized': False})
    draw.text((16, canvas.height-footer+12), 'Only pale cell-color overlay changes. Core/halo fields and wetness settings are unchanged.', font=small, fill='#c6d5dc')
    output = root / name
    assert not output.exists(), output
    canvas.save(output)
    return {'sheet': name, 'sha256': digest(output), 'source_images': sources,
            'processing': 'original image pixels, unchanged scale; labels and arrangement only'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = {
        'comparisons': [compare(a.out, s) for s in ('macro', 'plane', 'bite')],
        'sheets': [
            montage(a.out, ['plane', 'bite'], 640, 'v21-cycles-A-B-comparison.png'),
            montage(a.out, ['macro'], 1024, 'v21-macro-A-B-comparison.png'),
        ],
        'baseline_provenance': 'A images are actual v20B Cycles outputs. See render-batch receipt for whether reused or freshly rendered.',
    }
    (a.out/'comparison-evidence.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
