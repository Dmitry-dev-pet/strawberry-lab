"""Restore Exact only with a strict collision fallback; source scenes are authenticated."""
from pathlib import Path
import json,hashlib
import bpy
ROOT=Path(__file__).resolve().parents[3]
for seed in [101,202]:
 source=ROOT.parent/'strawberry-generator/build/generator-v1-final'/f'seed{seed}/strawberry.blend'
 expected=json.loads((ROOT/'src/strawberry_generator/readback.json').read_text())['full_downloaded_sha256'][f'seed{seed}.blend'];assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
 out=ROOT/'build/generator-exact-v2'/f'seed{seed}.blend';assert not out.exists()
 bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);text=bpy.data.texts['TISSUE_ZONES__RUN.py'];code=text.as_string()
 anchor='def make_mesh(';assert code.count(anchor)==1;code=code.replace(anchor,(Path(__file__).parent/'conforming_cap.py').read_text()+'\n\n'+anchor)
 anchor='        patch = cap_patch(bm, body_to_knife, mm_per_unit)';assert code.count(anchor)==1
 code=code.replace(anchor,"""        triangulation='CDT'
        try:
            patch = cap_patch(bm, body_to_knife, mm_per_unit)
        except ValueError as error:
            if str(error)!='The triangulator merged distinct seam vertices':raise
            # CDT has already modified its BMesh. Retry from the untouched native Boolean.
            bm.free();bm=bmesh.new();bm.from_mesh(base)
            rest_layer=bm.verts.layers.float_vector.new(REST_ATTRIBUTE)
            bm.verts.index_update();bm.normal_update()
            patch=conforming_cap_patch(bm,body_to_knife,mm_per_unit)
            triangulation='conforming-centroids'
""")
 anchor='            "cap": True, "fast_vertices":';assert code.count(anchor)==1;code=code.replace(anchor,'            "inherited_boundary_degenerates": getattr(conforming_cap_patch,"last_boundary_degenerates",0) if triangulation!="CDT" else 0, "triangulation": triangulation, "cap": True, "fast_vertices":')
 text.clear();text.write(code);bpy.context.scene['Generator Fast only']=False;bpy.context.scene['Generator Exact status']='CDT baseline; conforming interior centroid fallback only on distinct-seam collision'
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
