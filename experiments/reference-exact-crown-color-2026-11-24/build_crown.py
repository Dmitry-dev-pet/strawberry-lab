"""Independent crown continuation on verified Exact exterior. Reuses owned generator.
All dimensions ARTIST. Never changes source file or preexisting geometry.
Usage: blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python build_crown.py -- source.blend stock264.json output.blend owned_src_dir split_helpers_dir
"""
import bpy,bmesh,hashlib,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def blob(p):
    b=Path(p).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

PIN='d8f86ac4a3fbe69d34ae43a6410583c16c6ddc7d8805886bc28d65d7ed27974a'
STOCK_PIN='23beb6082f419148578ed556cc8dee0b83799b83f499df6453b161d9bb79bde6'

def main():
    src,stock,out,owned,helper=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and sha(stock)==STOCK_PIN and not out.exists()
    assert blob(owned/'build_strawberry_exterior.py')=='d38ab90b84bd99015b80b9063dd100ee5a64033b'
    assert blob(owned/'exterior_shape.py')=='90bb7874680c55f2940d3ff899e6ab555b9b55e7'
    sys.path[:0]=[str(owned.resolve()),str(helper.resolve())]
    from exterior_shape import ExteriorShape,ExteriorParams
    from build_strawberry_exterior import emit_calyx
    from build_split import Graph,ROOT,SKIN,CUTTER
    bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False)
    receipt=json.loads(stock.read_text());root=bpy.data.objects[ROOT];assert root['neutral_stock_key']==receipt['stock_key'] and root['count']==264
    skin=bpy.data.objects[SKIN];shape=ExteriorShape(ExteriorParams(**receipt['recipe']))
    assert (skin.data.vertices[-2].co-__import__('mathutils').Vector(shape.point(0.,0.))).length<1e-5
    collection=bpy.data.collections.new('SL Crown | sepals and pedicel');bpy.context.scene.collection.children.link(collection)
    emit_calyx(shape,collection)
    organs=list(collection.objects);assert len(organs)==9 and sum(o.get('role')=='sepal' for o in organs)==8
    shared=bpy.data.node_groups['SL | common shape map v1']
    graph=Graph('SL Crown | shared actual cutter clip',root)
    cut=graph.info(bpy.data.objects[CUTTER]).outputs['Geometry'];bo=graph.node('GeometryNodeMeshBoolean','Closed organ minus same actual cutter');bo.operation='DIFFERENCE';bo.solver='MANIFOLD';graph.w(graph.input,bo.inputs['Mesh 1']);graph.w(cut,bo.inputs['Mesh 2']);result=graph.switch(graph.math('GREATER_THAN',graph.driven('split_mode'),.5),graph.input,bo.outputs['Mesh'])
    for i,o in enumerate(organs):
        # Apply the existing thickness operation to the neutral stock before the common map.
        bpy.context.view_layer.objects.active=o;o.select_set(True)
        for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
        o.select_set(False)
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold and e.is_contiguous for e in bm.edges);assert bm.calc_volume(signed=True)>0;bm.to_mesh(o.data);bm.free();o.data.update()
        attr=o.data.attributes.new('sl_rest_position','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',[c for v in o.data.vertices for c in v.co])
        o['neutral_stock_key']=root['neutral_stock_key'];o['crown_experiment']='original owned curved sepals and stalk, ARTIST'
        mod=o.modifiers.new('SL Common forward shape','NODES');mod.node_group=shared
        if i==0:graph.finish(o,result)
        else:mod=o.modifiers.new(graph.g.name,'NODES');mod.node_group=graph.g
    bpy.context.view_layer.objects.active=root;root.select_set(True);bpy.context.scene['scope']='Independent ARTIST crown continuation; source body, seeds, tissues and optics retained';root.update_tag();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
    print('BUILT',json.dumps({'source_sha':PIN,'scene_sha':sha(out),'organs':[{'name':o.name,'role':o.get('role'),'vertices':len(o.data.vertices)} for o in organs],'common_map':shared.name,'cutter_nodes':len(graph.g.nodes)}),flush=True)
if __name__=='__main__':main()
