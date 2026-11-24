"""Independent diagnostic cell relief for the accepted Strawberry Lab SDF body.
Original construction; no Frucht graph/code/material imported. All values ARTIST.
Subdivide the connected mesh globally at one level only while cutting to avoid
T-junctions; cap-local refinement remains a future optimization.
"""
import bpy,sys,hashlib,math
from pathlib import Path
BODY='Receptacle | canonical PR29 hull'
EXPECTED='c27ebc88e17e5172c80b3d4dbc3882a78be690fcc7a8f0af68d697d18addbc4f'

def install(body):
    mm=bpy.context.scene.unit_settings.scale_length*1000
    assert 20 < mm < 25, mm
    cap=body.data.materials[1]
    assert cap.name.startswith('SDF | inherited')
    g=bpy.data.node_groups.new('SL Cell Surface | smooth centre field research','GeometryNodeTree')
    for direction in ('INPUT','OUTPUT'): g.interface.new_socket(name='Geometry',in_out=direction,socket_type='NodeSocketGeometry')
    N,L=g.nodes,g.links
    def n(t,label):
        a=N.new(t);a.label=label;return a
    def w(a,b):
        if isinstance(a,(int,float,bool,tuple)): b.default_value=a
        else:L.new(a,b)
    def m(op,a,b=None,label=''):
        q=n('ShaderNodeMath',label or op);q.operation=op;w(a,q.inputs[0]);
        if b is not None:w(b,q.inputs[1])
        return q.outputs[0]
    def v(op,a,b,label=''):
        q=n('ShaderNodeVectorMath',label or op);q.operation=op;w(a,q.inputs[0]);w(b,q.inputs['Scale'] if op=='SCALE' else q.inputs[1]);return q.outputs['Value' if op in {'DISTANCE','DOT_PRODUCT','LENGTH'} else 'Vector']
    def store(geo,name,typ,value):
        q=n('GeometryNodeStoreNamedAttribute',name);q.data_type=typ;q.domain='POINT';q.inputs['Name'].default_value=name;w(geo,q.inputs['Geometry']);w(value,q.inputs['Value']);return q.outputs['Geometry']
    def attr(name,typ):
        q=n('GeometryNodeInputNamedAttribute',name);q.data_type=typ;q.inputs['Name'].default_value=name;return q.outputs['Attribute']
    def remap(x,lo,hi,a,b):
        q=n('ShaderNodeMapRange','Smooth bounded transition');q.clamp=True;q.interpolation_type='SMOOTHERSTEP';w(x,q.inputs['Value']);q.inputs['From Min'].default_value=lo;q.inputs['From Max'].default_value=hi;q.inputs['To Min'].default_value=a;q.inputs['To Max'].default_value=b;return q.outputs['Result']
    def driven(key):
        q=n('ShaderNodeValue',key);f=q.outputs[0].driver_add('default_value');d=f.driver;d.type='AVERAGE';a=d.variables.new();a.name='value';a.type='SINGLE_PROP';a.targets[0].id=body;a.targets[0].data_path='["'+key+'"]';return q.outputs[0]
    inp=n('NodeGroupInput','Accepted SDF mesh');out=n('NodeGroupOutput','Refined native body');geo=inp.outputs[0]
    body['cell_surface_gain']=0.0;body.id_properties_ui('cell_surface_gain').update(min=0.,max=1.,description='0 baseline; 1 diagnostic variable-size smooth cell relief')
    body['cell_surface_detail']=1;body.id_properties_ui('cell_surface_detail').update(min=0,max=1,description='Global conforming subdivision on cut only; bounded to 1')
    gain=driven('cell_surface_gain');detail=driven('cell_surface_detail');mode=driven('sdf_mode')
    pos=n('GeometryNodeInputPosition','Current body position').outputs[0];normal=n('GeometryNodeInputNormal','Original surface normal').outputs[0]
    smooth=store(geo,'sl_cell_reference_position','FLOAT_VECTOR',pos);smooth=store(smooth,'sl_cell_reference_normal','FLOAT_VECTOR',normal)
    q=n('GeometryNodeSubdivideMesh','Conforming refinement: no separate cap seam');w(smooth,q.inputs['Mesh']);w(detail,q.inputs['Level']);refined=q.outputs['Mesh']
    sel=n('GeometryNodeMaterialSelection','Cap material only');sel.inputs['Material'].default_value=cap
    sep=n('GeometryNodeSeparateGeometry','Unaltered skin used for edge fade');sep.domain='FACE';w(geo,sep.inputs['Geometry']);w(sel.outputs[0],sep.inputs['Selection'])
    prox=n('GeometryNodeProximity','Distance to original skin surface');prox.target_element='FACES';w(sep.outputs['Inverted'],prox.inputs['Target'])
    fade=remap(prox.outputs['Distance'],0.04/mm,1.05/mm,0.,1.)
    rest=attr('sdf_rest_position','FLOAT_VECTOR');xy=v('MULTIPLY',rest,(1.,1.,0.));radius=n('ShaderNodeVectorMath','Rest radial distance');radius.operation='LENGTH';w(xy,radius.inputs[0]);r=radius.outputs['Value']
    # Continuous radial warp gives smaller cells toward the core without changing
    # the region or reseeding a separate lattice on each cut.
    exponent=m('MULTIPLY',m('MULTIPLY',r,r),-1/(.38**2));inner=m('POWER',math.e,exponent);local=m('ADD',1.,m('MULTIPLY',inner,.55))
    noise=n('ShaderNodeTexNoise','Low frequency 3D coordinate warp');noise.noise_dimensions='3D';w(rest,noise.inputs['Vector']);noise.inputs['Scale'].default_value=4.3;noise.inputs['Detail'].default_value=2.
    warp=v('SCALE',v('SUBTRACT',noise.outputs['Color'],(.5,.5,.5)),.022);warped=v('ADD',rest,warp);anis=v('MULTIPLY',warped,(1.,1.,.87));coords=v('SCALE',anis,local)
    vor=n('ShaderNodeTexVoronoi','Smooth nearest centre, not edge-distance');vor.voronoi_dimensions='3D';vor.feature='SMOOTH_F1';w(coords,vor.inputs['Vector']);vor.inputs['Scale'].default_value=29.;vor.inputs['Smoothness'].default_value=.34
    dome=remap(vor.outputs['Distance'],.18,.81,1.,0.)
    height=m('MULTIPLY',m('MULTIPLY',m('MULTIPLY',dome,fade),gain),.145/mm)
    # Store the actual scalar for later optical A/B, not a second random field.
    refined=store(refined,'sl_cell_dome','FLOAT',m('MULTIPLY',dome,fade));refined=store(refined,'sl_cell_height_mm','FLOAT',m('MULTIPLY',height,mm))
    q=n('ShaderNodeVectorMath','Normalize the original normal');q.operation='NORMALIZE';w(attr('sl_cell_reference_normal','FLOAT_VECTOR'),q.inputs[0]);delta=v('SCALE',q.outputs['Vector'],height)
    move=n('GeometryNodeSetPosition','Cap-only dome displacement');w(refined,move.inputs['Geometry']);w(sel.outputs[0],move.inputs['Selection']);w(delta,move.inputs['Offset'])
    switch=n('GeometryNodeSwitch','Keep whole fruit and gain=0 exactly unchanged');switch.input_type='GEOMETRY';w(m('MULTIPLY',m('GREATER_THAN',mode,.5),m('GREATER_THAN',gain,1e-7)),switch.inputs['Switch']);w(geo,switch.inputs['False']);w(move.outputs['Geometry'],switch.inputs['True']);w(switch.outputs[0],out.inputs[0])
    # Simple left-to-right placement for inspecting the independent group.
    for i,q in enumerate(N):q.location=((i//8)*220,-(i%8)*180)
    mod=body.modifiers.new('SL Cell Surface | research A/B','NODES');mod.node_group=g
    return g

if __name__=='__main__':
    src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists();assert hashlib.sha256(src.read_bytes()).hexdigest()==EXPECTED
    bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);body=bpy.data.objects[BODY];g=install(body)
    bpy.context.scene['SL Cell Surface status']='Research; global conforming refinement for cut mode; ARTIST; visual acceptance pending.'
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()));print('BUILT',len(g.nodes),hashlib.sha256(out.read_bytes()).hexdigest())
