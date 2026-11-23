"""Independent saved-scene A/B validation; checks shader-only intervention.

Not a histology validator and not an exhaustive cutter/triangle intersection proof.
"""
from pathlib import Path
import hashlib,json,sys
import bpy,bmesh

BODY='Receptacle | canonical PR29 hull'
CAP='SDF | inherited 150^3 tissue + own multiscale wetness'
GAIN='ARTIST v1 rest-fibril gain (0 A / 1 B)'

def sha(b):return hashlib.sha256(b).hexdigest()
def raw_geom_signature():
    h=hashlib.sha256();count=0
    for o in sorted((o for o in bpy.data.objects if o.type=='MESH'),key=lambda o:o.name):
        count+=1
        h.update(o.name.encode())
        h.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
        for v in o.data.vertices:h.update(repr(tuple(v.co)).encode())
        for p in o.data.polygons:h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest(),count

def scene_stats(p):
    bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False)
    s=bpy.context.scene; m=bpy.data.materials[CAP];gn=m.node_tree
    ctrl=gn.nodes[GAIN]
    assert ctrl.type=='VALUE'
    gain=float(ctrl.outputs[0].default_value)
    # Every dependency of added field must be anchored in rest-space from the evaluated mesh.
    anis=gn.nodes['ARTIST | anisotropic rest XYZ'];rest=anis.inputs[0].links[0].from_node
    assert rest.type=='ATTRIBUTE' and rest.attribute_name=='sdf_rest_position'
    noise=gn.nodes['ARTIST | coherent 3D tissue filaments'];assert noise.inputs['Vector'].links[0].from_node==anis
    bump=gn.nodes['ARTIST | sub-mm wet fibril normal']; bs=next(n for n in gn.nodes if n.type=='BSDF_PRINCIPLED')
    assert bs.inputs['Normal'].links[0].from_node==bump
    mats=[]
    for n in sorted(gn.nodes,key=lambda n:n.name):
        vals=[]
        for socket in n.inputs:
            if not socket.is_linked:
                try:v=list(socket.default_value) if hasattr(socket.default_value,'__len__') else float(socket.default_value)
                except Exception:v=None
                vals.append((socket.identifier,v))
        if n.type=='VALUE':vals.append(('output',0 if n.name==GAIN else float(n.outputs[0].default_value)))
        mats.append((n.name,n.bl_idname,getattr(n,'operation',None),getattr(n,'noise_dimensions',None),vals))
    links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in gn.links)
    mat_sh=sha(repr((mats,links)).encode())
    img_sh=sha(bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'].packed_file.data)
    geom_sh,count=raw_geom_signature()
    poses=[]
    for mode,label in [(1,'plane'),(2,'bite')]:
        body=s.objects[BODY]
        body['sdf_mode']=mode
        body['sdf_voxel_mm']=.32  # bounded QA, source run at .20 verified
        body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
        o=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=o.to_mesh()
        points=tuple(tuple(v.co) for v in mesh.vertices)
        bm=bmesh.new();bm.from_mesh(mesh)
        metric={'pose':label,'verts':len(mesh.vertices),'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True),'geometry_sha':sha(repr(points).encode())}
        bm.free();o.to_mesh_clear()
        assert metric['nonmanifold']==0 and metric['volume']>0
        poses.append(metric)
    return {'gain':gain,'materials_sha_excluding_gain':mat_sh,'raw_geometry_sha':geom_sh,'mesh_objects':count,'packed_atlas_sha':img_sh,'poses':poses,'scene_sha':sha(p.read_bytes())}

a,b,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists();A=scene_stats(a);B=scene_stats(b)
for key in ['materials_sha_excluding_gain','raw_geometry_sha','mesh_objects','packed_atlas_sha']:
    assert A[key]==B[key],key
for p,q in zip(A['poses'],B['poses']):
    assert p==q, (p,q)
assert A['gain']==0 and B['gain']==1
result={'status':'PASS_SHADER_ONLY_AB','blender':bpy.app.version_string,'A':A,'B':B,'identical_pose_geometry':True,'same_packed_atlas':True,'only_gain_diff_mat_graph':True,'caveats':['Bump/roughness shader only, no new cells or physical fluid','Tested plane and bite at 0.32mm only; inherited PR48 validation covers 8 previous geometry states']}
out.write_text(json.dumps(result,indent=2))
print('PASS_SHADER_ONLY_AB',json.dumps({'A':A['gain'],'B':B['gain'],'raw_geo':A['raw_geometry_sha'],'plane_v':A['poses'][0]['verts'],'bite_v':A['poses'][1]['verts']}),flush=True)
