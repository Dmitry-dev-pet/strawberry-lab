"""Render the bounded v21 comparison; optionally reuse verified v20B originals.

Without --reuse-baseline, all six images are freshly rendered. Reuse verifies
the previous scene and image hashes and preserves the original render receipts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--blender', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--reuse-baseline', type=Path)
    p.add_argument('--shots', nargs='+', choices=['macro', 'plane', 'bite'],
                   default=['macro', 'plane', 'bite'])
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).with_name('render_material.py')
    records = []
    baseline_sha = digest(a.baseline)
    for shot in a.shots:
        for variant, scene in [('a', a.baseline), ('b', a.candidate)]:
            output = a.out / f'cycles-v21{variant}-{shot}.png'
            receipt = output.with_suffix('.json')
            assert not output.exists() and not receipt.exists(), output
            if variant == 'a' and a.reuse_baseline:
                original = a.reuse_baseline / f'cycles-v20b-{shot}.png'
                original_receipt = original.with_suffix('.json')
                data = json.loads(original_receipt.read_text())
                assert data['source_sha256'] == baseline_sha
                assert data['image_sha256'] == digest(original)
                assert data['blender'] == '5.2.4 LTS'
                shutil.copyfile(original, output)
                shutil.copyfile(original_receipt, receipt)
                records.append({
                    'variant': variant, 'shot': shot,
                    'status': 'reused original v20B actual Cycles image',
                    'original_image': original.name,
                    'comparison_image': output.name,
                    'source_scene_sha256': baseline_sha,
                    'image_sha256': digest(output),
                    'original_receipt_copied_unchanged': True,
                })
                print('VERIFIED_BASELINE_REUSE', json.dumps(records[-1]), flush=True)
                continue
            macro = shot == 'macro'
            cmd = [str(a.blender.resolve()), '--background', '--threads', '4',
                   '--factory-startup', '--disable-autoexec', '--python-exit-code', '1',
                   '--python', str(script.resolve()), '--', '--scene', str(scene.resolve()),
                   '--shot', shot, '--out', str(output.resolve()),
                   '--size', '1024' if macro else '640',
                   '--samples', '32' if macro else '24']
            log = output.with_suffix('.log')
            print('START', variant, shot, flush=True)
            start = time.perf_counter()
            with log.open('w') as stream:
                result = subprocess.run(cmd, stdout=stream, stderr=subprocess.STDOUT)
            assert result.returncode == 0, f'{shot} failed: {log}'
            data = json.loads(receipt.read_text())
            assert data['source_sha256'] == digest(scene)
            assert data['image_sha256'] == digest(output)
            records.append({'variant': variant, 'shot': shot, 'status': 'fresh actual Cycles',
                            'receipt': receipt.name, 'wall_seconds': time.perf_counter()-start,
                            'command': cmd})
            print('COMPLETE', variant, shot, records[-1]['wall_seconds'], flush=True)
    name = 'render-batch-' + '-'.join(a.shots) + '.json'
    (a.out / name).write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
