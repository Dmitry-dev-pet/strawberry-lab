"""Private-reference audit harness; no reference graph or geometry exported.
Execute selected author functions from the owner's pinned ZIP on synthetic meshes.
The tests exercise the functions, not the unavailable commercial strawberry scene.
"""
import ast, collections, hashlib, json, sys, zipfile, types, math
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ZIP_SHA='aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877'
KIWI_SHA='98c9e957a611cfeee26f2848868755794ad4d8eb42aec33ba543547d263ea840'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_env(z,file,functions,constants=(),extra=None):
    # Select definitions at runtime; no original definitions written to disk.
    tree=ast.parse(z.read(file).decode(),filename=file)
    chosen=[]
    for n in tree.body:
        if isinstance(n,ast.FunctionDef) and n.name in functions:chosen.append(n)
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets):chosen.append(n)
    env={'bpy':bpy,**(extra or {})}
    exec(compile(ast.Module(body=chosen,type_ignores=[]),file,'exec'),env)
    assert all(f in env for f in functions)
    return env

def mesh(name,points,faces):
    m=bpy.data.meshes.new(name);m.from_pydata(points,[],faces);m.update()
    o=bpy.data.objects.new(name,m);bpy.context.scene.collection.objects.link(o);return o

def group(name,o):
    g=bpy.data.node_groups.new(name,'GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    n,l=g.nodes,g.links;i=n.new('NodeGroupInput').outputs[0];out=n.new('NodeGroupOutput').inputs[0];m=o.modifiers.new(name,'NODES');m.node_group=g;return n,l,i,out

def evaluated(o):
    bpy.context.view_layer.update();return bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))

def grid(name,separate):
    points=[];faces=[];labels=[];n=11
    # Same mixed-material boundary geometry in one mesh, or separate halves.
    # The disconnected case has an explicit small gap and no shared vertex IDs.
    for side in ([-1,1] if separate else [0]):
        cols=list(range(-5,1)) if side==-1 else list(range(0,6)) if side==1 else list(range(-5,6))
        start=len(points)
        for y in range(n):
            for x in cols:
                xx=float(x)+(.22*math.sin(y*1.7) if x==0 else 0.) + side*.06
                points.append((xx,float(y),.06*math.sin(x+y)))
        nc=len(cols)
        for y in range(n-1):
            for j in range(nc-1):
                i=start+y*nc+j;faces.append((i,i+1,i+nc+1,i+nc));labels.append(cols[j]<0)
    o=mesh(name,points,faces)
    a=bpy.data.materials.get('Probe skin') or bpy.data.materials.new('Probe skin');b=bpy.data.materials.get('Probe cap') or bpy.data.materials.new('Probe cap');o.data.materials.append(a);o.data.materials.append(b)
    for p,v in zip(o.data.polygons,labels):p.material_index=0 if v else 1
    return o,a

def seam_probe(env,separate):
    o,a=grid('Disconnected' if separate else 'Shared seam',separate);n,l,i,out=group(o.name+' probe',o);m=n.new('GeometryNodeMaterialSelection');m.inputs['Material'].default_value=a
    l.new(env['naht_glaetten'](n,l,i,m.outputs[0]),out)
    original=[v.co.copy() for v in o.data.vertices];f0=[tuple(p.vertices) for p in o.data.polygons];ev=evaluated(o);delta=[(v.co-p).length for v,p in zip(ev.vertices,original)]
    same=len(original)==len(ev.vertices) and f0==[tuple(p.vertices) for p in ev.polygons]
    assert same
    if separate:assert max(delta)<1e-7
    else:assert max(delta)>.01
    far=[d for d,p in zip(delta,original) if abs(p.x)>3.1];assert max(far)<1e-7
    r=dict(vertices=len(original),faces=len(f0),connectivity_unchanged=same,moved_vertices=sum(d>1e-6 for d in delta),max_displacement=max(delta),far_max_displacement=max(far),node_count=len(n));bpy.data.meshes.remove(ev);return r

def snap_probe(env):
    xs=[-2,-1,-.37,.43,1,2];ys=list(range(5));p=[(x,y,0) for y in ys for x in xs];w=len(xs);f=[(i+j*w,i+j*w+1,i+(j+1)*w+1,i+(j+1)*w) for j in range(4) for i in range(w-1)];o=mesh('Snap strip',p,f)
    bpy.ops.mesh.primitive_cube_add(size=2,location=(-5,0,0));cut=bpy.context.object;cut.scale=(5,20,20)
    n,l,i,out=group('Snap probe',o);info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=cut;pos=n.new('GeometryNodeInputPosition');sep=n.new('ShaderNodeSeparateXYZ');l.new(pos.outputs[0],sep.inputs[0]);cmp=n.new('FunctionNodeCompare');cmp.data_type='FLOAT';cmp.operation='LESS_THAN';l.new(sep.outputs['X'],cmp.inputs['A']);cmp.inputs['B'].default_value=0.
    l.new(env['rand_knoten'](n,l,i,cmp.outputs[0],info.outputs['Geometry']),out)
    ev=evaluated(o);v=[tuple(x.co) for x in ev.vertices];kept=[tuple(q.co) for q in o.data.vertices if q.co.x>0];vs=set(v);r=dict(before_vertices=len(p),after_vertices=len(v),before_faces=len(f),after_faces=len(ev.polygons),snapped_vertices=sum(abs(q[0])<1e-6 for q in v),retained_positive_vertices=sum(q in vs for q in kept),expected_positive_vertices=len(kept),remaining_negative_vertices=sum(q[0]<-1e-6 for q in v))
    assert r['snapped_vertices']==5 and r['retained_positive_vertices']==len(kept) and r['remaining_negative_vertices']==0,r
    return r

def bvh(me):
    me.calc_loop_triangles();return BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)

def flesh_probe(env):
    # Synthetic units and scratch parameters, not author's fruit defaults.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,radius=2);hull=bpy.context.object;hull.name='Probe original envelope'
    bpy.ops.mesh.primitive_cube_add(size=2,location=(0,-5,0));cut=bpy.context.object;cut.scale=(5,5,5)
    source=mesh('Probe remeshed source',[],[]);g=env['_gruppe_fleisch_quelle'](hull);source.modifiers.new('probe','NODES').node_group=g
    o=mesh('Probe separate flesh',[],[]);n,l,i,out=group('Flesh probe',o);ci=n.new('GeometryNodeObjectInfo');ci.transform_space='RELATIVE';ci.inputs['Object'].default_value=cut;l.new(env['fleisch_knoten'](n,l,source,ci.outputs['Geometry']),out)
    a=evaluated(source);b=evaluated(o);at=b.attributes['schnitt_rand_abstand'];t1=bvh(a);t2=bvh(hull.data);errors_grid=[];errors_original=[];diff=[]
    for v,w in zip(b.vertices,at.data):
        x=t1.find_nearest(v.co)[3];y=t2.find_nearest(v.co)[3];errors_grid.append(abs(x-w.value));errors_original.append(abs(y-w.value));diff.append(abs(x-y))
    r=dict(original_vertices=len(hull.data.vertices),remeshed_reference_vertices=len(a.vertices),flesh_vertices=len(b.vertices),distance_samples=len(diff),max_grid_error=max(errors_grid),max_original_error=max(errors_original),max_distance_difference=max(diff),grid_node_count=len(g.nodes),flesh_node_count=len(n))
    assert max(errors_grid)<1e-4 and max(diff)>.001,r
    return r

def kiwi_probe(path):
    assert sha(path)==KIWI_SHA;bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    out={}
    for key in ['SCHNELL KIWI | Körper','SCHNELL KIWI | Fleisch Quelle','SCHNELL KIWI | Schnittfläche']:
        o=bpy.data.objects[key];m=o.modifiers.get('Live') if key.endswith('Körper') else o.modifiers.get('Fast Mode');g=m.node_group;c=collections.Counter(n.bl_idname for n in g.nodes)
        out[key]=dict(nodes=len(g.nodes),mesh_boolean=c['GeometryNodeMeshBoolean'],grid_to_mesh=c['GeometryNodeGridToMesh'],sample_grid=c['GeometryNodeSampleGrid'],set_position=c['GeometryNodeSetPosition'],delete_geometry=c['GeometryNodeDeleteGeometry'],sdf_boolean=c['GeometryNodeSDFGridBoolean'])
    a=out['SCHNELL KIWI | Körper'];assert a['grid_to_mesh']==a['mesh_boolean']==a['set_position']==0 and a['delete_geometry']==2
    return out

def main():
    archive,kiwi,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(archive)==ZIP_SHA and not out.exists()
    with zipfile.ZipFile(archive) as z:
        # Directly inspect species declarations and evaluate the name-sensitive dispatch predicate.
        f=ast.parse(z.read('fruechte.py').decode());rows={}
        for n in f.body:
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='Frucht':
                for t in n.targets:
                    if isinstance(t,ast.Name):rows[t.id]=[k.arg for k in n.value.keywords]
        assert 'kante_sauber' not in rows['ERDBEERE'] and 'kante_sauber' not in rows['KIWI'] and 'kante_sauber' in rows['KIRSCHE']
        fast=types.SimpleNamespace(ART='ERDBEERE',S='Probe');env=source_env(z,'schnitte.py',['_rand_glatt','rand_knoten','_trennen','_gruppe_fleisch_quelle','fleisch_knoten'],extra={'GRUPPE':'SCHNITTE • Entfernen','fast':fast,'P':{'voxel_fleisch':.16,'band':3,'schale':0.},'MARKHOEHLE':'','FLEISCH':'Probe flesh'})
        dispatch={k:env['_rand_glatt'](k) for k in ['SCHNITTE • Entfernen','SCHNELL • Live Entfernen']};assert list(dispatch.values())==[True,False]
        seam=source_env(z,'gliederung.py',['naht_glaetten'],['NAHT_SCHRITTE','NAHT_BREITE'])
        actual=kiwi_probe(kiwi);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.data.materials.new('Probe flesh')
        result=dict(archive_sha=ZIP_SHA,kiwi_sha=KIWI_SHA,blender=bpy.app.version_string,build_hash=bpy.app.build_hash.decode(),species_explicit_clean_clip={'strawberry':False,'kiwi':False,'cherry':True},strawberry_name_dispatch=dispatch,kiwi_runtime_graph=actual,synthetic_connected=seam_probe(seam,False),synthetic_disconnected=seam_probe(seam,True),synthetic_snap=snap_probe(env),synthetic_flesh=flesh_probe(env),scope='Original isolated functions with synthetic inputs; no commercial Strawberry scene execution or new Strawberry geometry.')
        out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
