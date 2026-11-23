"""One-factor ARTIST 3D rest-space fibril / wet-glint shader A/B for own SDF cut.

Creates editable .blend files with one identical node graph and a single gain
parameter 0.0 vs 1.0; source/recipe/geom/material elsewhere unchanged.
No dependence on Frucht code, meshes or textures.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy

PIN_SOURCE = 'bfecf691df67cafff020971368f1afc877f4bac1165e851520bdcc1773f85ce1'
REST = 'sdf_rest_position'
CAP = 'SDF | inherited 150^3 tissue + own multiscale wetness'
GAIN = 'ARTIST v1 rest-fibril gain (0 A / 1 B)'

def node(graph, type_name, name):
    n=graph.nodes.new(type_name)
    n.name=name
    n.label=name
    return n

def link(graph, source, destination):
    graph.links.new(source, destination)

def build_graph():
    mat=bpy.data.materials.get(CAP)
    assert mat is not None and mat.use_nodes, CAP
    g=mat.node_tree
    assert GAIN not in g.nodes
    rest=next(n for n in g.nodes if n.type=='ATTRIBUTE' and n.attribute_name==REST)
    bs=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED')
    assert len(bs.inputs['Normal'].links)==1 and len(bs.inputs['Roughness'].links)==1
    orig_normal=bs.inputs['Normal'].links[0].from_socket
    orig_roughness=bs.inputs['Roughness'].links[0].from_socket

    gain=node(g,'ShaderNodeValue',GAIN)
    gain.outputs[0].default_value=0

    # A shared 3D field: small elongated tissue strands with source-space axes.
    stretch=node(g,'ShaderNodeVectorMath','ARTIST | anisotropic rest XYZ')
    stretch.operation='MULTIPLY'
    stretch.inputs[1].default_value=(120,108,26)
    link(g,rest.outputs['Vector'],stretch.inputs[0])
    noise=node(g,'ShaderNodeTexNoise','ARTIST | coherent 3D tissue filaments')
    noise.noise_dimensions='3D'
    noise.inputs['Scale'].default_value=1.0
    noise.inputs['Detail'].default_value=2.3
    noise.inputs['Roughness'].default_value=0.60
    noise.inputs['Distortion'].default_value=0.05
    link(g,stretch.outputs['Vector'],noise.inputs['Vector'])
    contrast=node(g,'ShaderNodeMapRange','ARTIST | smooth wet filament pockets')
    contrast.clamp=True
    contrast.inputs['From Min'].default_value=.34
    contrast.inputs['From Max'].default_value=.68
    contrast.inputs['To Min'].default_value=0
    contrast.inputs['To Max'].default_value=1
    link(g,noise.outputs['Fac'],contrast.inputs['Value'])

    # Same one gain controls tiny geometric appearance (shader normals, no mesh).
    strength=node(g,'ShaderNodeMath','ARTIST | normal field strength')
    strength.operation='MULTIPLY'
    strength.inputs[1].default_value=.23
    link(g,gain.outputs[0],strength.inputs[0])
    bump=node(g,'ShaderNodeBump','ARTIST | sub-mm wet fibril normal')
    bump.inputs['Distance'].default_value=.0019 # Blender BU: ~0.042 mm
    link(g,strength.outputs[0],bump.inputs['Strength'])
    link(g,contrast.outputs['Result'],bump.inputs['Height'])
    link(g,orig_normal,bump.inputs['Normal'])
    link(g,bump.outputs['Normal'],bs.inputs['Normal'])

    # Inverse coupling of microtexture to roughness: glossy pockets not global wax.
    micro=node(g,'ShaderNodeMath','ARTIST | wet-glint roughness shift')
    micro.operation='MULTIPLY'
    micro.inputs[1].default_value=.075
    link(g,contrast.outputs['Result'],micro.inputs[0])
    on=node(g,'ShaderNodeMath','ARTIST | apply one gain to roughness')
    on.operation='MULTIPLY'
    link(g,micro.outputs[0],on.inputs[0])
    link(g,gain.outputs[0],on.inputs[1])
    rough=node(g,'ShaderNodeMath','ARTIST | wetness roughness')
    rough.operation='SUBTRACT'
    link(g,orig_roughness,rough.inputs[0])
    link(g,on.outputs[0],rough.inputs[1])
    link(g,rough.outputs[0],bs.inputs['Roughness'])
    # Shader-only source-space path: named attr -> anisotropic noise -> all outputs.
    return gain,mat

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--source',type=Path,required=True)
    a.add_argument('--outdir',type=Path,required=True)
    args=a.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=args.source.resolve(); outdir=args.outdir.resolve()
    assert hashlib.sha256(source.read_bytes()).hexdigest()==PIN_SOURCE,'wrong source .blend'
    assert not outdir.exists(), 'Do not overwrite output'
    outdir.mkdir(parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
    src_mats={m.name for m in bpy.data.materials}
    gain,mat=build_graph()
    reports=[]
    for label,g in [('A',0.0),('B',1.0)]:
        gain.outputs[0].default_value=g
        bpy.context.scene['ARTIST RestFibril A/B']='Same underlying shader graph; gain 0=OFF A, gain 1=ON B; rest-space anisotropic 3D field. Geometry unchanged.'
        path=outdir/f'pr49-rest-fibril-{label}.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
        reports.append({'variant':label,'source_sha256':PIN_SOURCE,'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'gain':g,'bytes':path.stat().st_size})
    (outdir/'build-receipt.json').write_text(json.dumps({'blender':bpy.app.version_string,'material':mat.name,'key':GAIN,'variants':reports,'baseline_materials':sorted(src_mats),'warnings':['ARTIST fields; no biological cell size or pore measurements','shader-only surface not solid fibrils']},indent=2))
    print('ARTIST_REST_FIBRIL_BUILT',json.dumps(reports),flush=True)

if __name__=='__main__':main()
