"""Independent juice-pool experiment on PR50 cell + vascular scene.
Three smooth spatial pool fields share original rest coordinates. A local free
surface intersects the relief below the cell crests. Open optical interfaces,
not a closed fluid volume or measured liquid simulation. All values ARTIST.
No third-party nodes/code/parameters imported.
"""
import bpy,sys,hashlib,json
from pathlib import Path
BODY='Receptacle | canonical PR29 hull'; JUICE='SL Juice | independent pool surface'
PIN='2ccb17510bf46ae7ae3fa1a09eac144144dffb5a5f10c193dae9832b70760973'

def install(body):
    s=bpy.context.scene;mm=s.unit_settings.scale_length*1000;assert 20<mm<25
    mat=bpy.data.materials.new('SL Juice | clear dielectric ARTIST');mat.use_nodes=True
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.94,.87,.80,1);bs.inputs['Roughness'].default_value=.13;bs.inputs['IOR'].default_value=1.333;bs.inputs['Transmission Weight'].default_value=1.;bs.inputs['Specular IOR Level'].default_value=.5
    mat.diffuse_color=(.95,.87,.80,.6)
    mesh=bpy.data.meshes.new('SL Juice procedural input');obj=bpy.data.objects.new(JUICE,mesh);s.collection.objects.link(obj)
    g=bpy.data.node_groups.new('SL Juice | rest-surface pooled interfaces','GeometryNodeTree')
    for direction in ('INPUT','OUTPUT'):g.interface.new_socket(name='Geometry',in_out=direction,socket_type='NodeSocketGeometry')
    N,L=g.nodes,g.links
    def n(typ,name):
        x=N.new(typ);x.name=x.label=name;return x
    def w(a,b):
        if isinstance(a,(float,int,bool,tuple)):b.default_value=a
        else:L.new(a,b)
    def m(op,a,b,name):
        x=n('ShaderNodeMath',name);x.operation=op;w(a,x.inputs[0]);w(b,x.inputs[1]);return x.outputs[0]
    def v(op,a,b,name):
        x=n('ShaderNodeVectorMath',name);x.operation=op;w(a,x.inputs[0]);w(b,x.inputs['Scale'] if op=='SCALE' else x.inputs[1]);return x.outputs['Value' if op in ('DISTANCE','DOT_PRODUCT') else 'Vector']
    def attr(name,typ='FLOAT'):
        x=n('GeometryNodeInputNamedAttribute','Read '+name);x.data_type=typ;x.inputs['Name'].default_value=name;return x.outputs['Attribute']
    def store(geo,name,value,typ='FLOAT'):
        x=n('GeometryNodeStoreNamedAttribute',name);x.data_type=typ;x.domain='POINT';x.inputs['Name'].default_value=name;w(geo,x.inputs['Geometry']);w(value,x.inputs['Value']);return x.outputs['Geometry']
    def remap(a,lo,hi,b,c,name):
        x=n('ShaderNodeMapRange',name);x.clamp=True;x.interpolation_type='SMOOTHERSTEP';w(a,x.inputs['Value']);x.inputs['From Min'].default_value=lo;x.inputs['From Max'].default_value=hi;x.inputs['To Min'].default_value=b;x.inputs['To Max'].default_value=c;return x.outputs['Result']
    def driven(key):
        x=n('ShaderNodeValue',key);d=x.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';var=d.variables.new();var.name='value';var.type='SINGLE_PROP';var.targets[0].id=body;var.targets[0].data_path='["'+key+'"]';return x.outputs[0]
    body['juice_surface_gain']=0.;body.id_properties_ui('juice_surface_gain').update(min=0.,max=1.,description='0 no liquid, 1 original pooled optical surface')
    gain=driven('juice_surface_gain');mode=driven('sdf_mode');cells=driven('cell_surface_gain')
    inp=n('NodeGroupInput','Empty control');out=n('NodeGroupOutput','Separate liquid only');info=n('GeometryNodeObjectInfo','Read evaluated own fruit');info.transform_space='RELATIVE';info.inputs['Object'].default_value=body
    cap=n('GeometryNodeMaterialSelection','Exposed flesh only');cap.inputs['Material'].default_value=body.data.materials[1]
    sep=n('GeometryNodeSeparateGeometry','Separate actual cap and skin');sep.domain='FACE';w(info.outputs['Geometry'],sep.inputs['Geometry']);w(cap.outputs[0],sep.inputs['Selection']);geo=sep.outputs['Selection']
    pos=n('GeometryNodeInputPosition','Existing cell surface').outputs[0];base=attr('sl_cell_reference_position','FLOAT_VECTOR');norm=attr('sl_cell_reference_normal','FLOAT_VECTOR');q=n('ShaderNodeVectorMath','Normalize original smooth normal');q.operation='NORMALIZE';w(norm,q.inputs[0]);normal=q.outputs['Vector']
    rest=attr('sdf_rest_position','FLOAT_VECTOR');rxy=v('MULTIPLY',rest,(1.,1.,0.),'Radial rest coordinate');q=n('ShaderNodeVectorMath','Radial distance');q.operation='LENGTH';w(rxy,q.inputs[0]);rad=q.outputs['Value']
    prox=n('GeometryNodeProximity','Distance from skin');prox.target_element='FACES';w(sep.outputs['Inverted'],prox.inputs['Target']);w(base,prox.inputs['Source Position']);edge=remap(prox.outputs['Distance'],.65/mm,1.65/mm,0.,1.,'Stay inside cut')
    center=remap(rad,.08,.54,.38,1.,'Reduced wetness near axis')
    noise=n('ShaderNodeTexNoise','Independent low-frequency spatial variation');noise.noise_dimensions='3D';w(rest,noise.inputs['Vector']);noise.inputs['Scale'].default_value=5.1;noise.inputs['Detail'].default_value=2.
    warp=v('SCALE',v('SUBTRACT',noise.outputs['Color'],(.5,.5,.5),'Centred warp'),.034,'Gentle warp');coords=v('ADD',rest,warp,'Warped original coordinates');coords=v('MULTIPLY',coords,(1.,1.,.76),'Elongated liquid pattern')
    lobes=[]
    for i,(freq,amplitude,radius,shift) in enumerate([(12.,1.,.61,(.13,.71,.29)),(24.,.79,.49,(.57,.23,.82)),(46.,.61,.40,(.31,.93,.17))]):
        shifted=v('ADD',coords,shift,f'Independent scale {i+1} seed');vor=n('ShaderNodeTexVoronoi',f'Smooth centres scale {i+1}');vor.voronoi_dimensions='3D';vor.feature='SMOOTH_F1';w(shifted,vor.inputs['Vector']);vor.inputs['Scale'].default_value=freq;vor.inputs['Smoothness'].default_value=.24
        lobe=remap(vor.outputs['Distance'],.14,radius,1.,0.,f'Pool envelope {i+1}');lobes.append(m('MULTIPLY',lobe,amplitude,f'Level weight {i+1}'))
    envelope=m('MAXIMUM',m('MAXIMUM',lobes[0],lobes[1],'Large and medium pools'),lobes[2],'All three scales')
    envelope=m('MULTIPLY',m('MULTIPLY',envelope,edge,'Edge falloff'),center,'Regional wetness')
    # Absolute height above SMOOTH pre-relief surface, not a duplicate displaced sheet.
    # Outer rims are deliberately submerged below the tissue; cell crowns can protrude.
    variation=remap(noise.outputs['Fac'],.24,.76,.12,.22,'ARTIST pool level mm')
    level=m('SUBTRACT',m('MULTIPLY',m('MULTIPLY',envelope,variation,'Local free surface level'),gain,'Amount'),.025,'Submerged rim mm')
    # Use actual relief displacement, rather than assuming the stored height scalar is exact.
    diff=v('SUBTRACT',pos,base,'Actual tissue displacement');height=m('MULTIPLY',v('DOT_PRODUCT',diff,normal,'Height along smooth normal'),mm,'Measured tissue height mm')
    clearance=m('SUBTRACT',level,height,'Optical surface minus actual tissue mm')
    geo=store(geo,'sl_juice_tissue_position',pos,'FLOAT_VECTOR');geo=store(geo,'sl_juice_clearance_mm',clearance);geo=store(geo,'sl_juice_envelope',envelope);geo=store(geo,'sl_juice_level_mm',level)
    # Include a submerged border around each connected patch. Face-domain threshold
    # uses the field, not a separate plane or point-scattered lens.
    a=m('GREATER_THAN',envelope,.035,'Pool support');b=m('GREATER_THAN',edge,.05,'Exclude skin');select=m('MULTIPLY',a,b,'Liquid patch support')
    patch=n('GeometryNodeSeparateGeometry','Connected patches from cap mesh');patch.domain='FACE';w(geo,patch.inputs['Geometry']);w(select,patch.inputs['Selection'])
    # Patch topology is now known: force every open boundary vertex into tissue.
    # No dangling elevated edge. Existing tissue position is the actual source.
    neighbors=n('GeometryNodeInputMeshVertexNeighbors','Boundary has more edges than faces');boundary=m('LESS_THAN',neighbors.outputs['Face Count'],neighbors.outputs['Vertex Count'],'Boundary point')
    tissue_height=m('MULTIPLY',v('DOT_PRODUCT',v('SUBTRACT',attr('sl_juice_tissue_position','FLOAT_VECTOR'),base,'Stored tissue minus smooth reference'),normal,'Actual height'),mm,'Height in mm')
    oldlevel=attr('sl_juice_level_mm');buried=m('MINIMUM',oldlevel,m('SUBTRACT',tissue_height,.018,'Tuck border below tissue'),'Bounded buried edge')
    choose=n('GeometryNodeSwitch','Only patch boundary is tucked');choose.input_type='FLOAT';w(boundary,choose.inputs['Switch']);w(oldlevel,choose.inputs['False']);w(buried,choose.inputs['True']);geo=store(patch.outputs['Selection'],'sl_juice_final_level_mm',choose.outputs['Output']);geo=store(geo,'sl_juice_clearance_mm',m('SUBTRACT',attr('sl_juice_final_level_mm'),tissue_height,'Final clearance'))
    offset=v('SCALE',normal,m('DIVIDE',attr('sl_juice_final_level_mm'),mm,'Level in object units'),'Smooth-reference liquid height');target=v('ADD',base,offset,'Liquid free surface position')
    move=n('GeometryNodeSetPosition','Reconstruct from smooth reference');w(geo,move.inputs['Geometry']);w(target,move.inputs['Position']);smooth=n('GeometryNodeSetShadeSmooth','Smooth liquid');smooth.domain='FACE';w(move.outputs['Geometry'],smooth.inputs['Geometry']);material=n('GeometryNodeSetMaterial','Independent dielectric material');material.inputs['Material'].default_value=mat;w(smooth.outputs['Geometry'],material.inputs['Geometry'])
    sw=n('GeometryNodeSwitch','Off and whole are empty');sw.input_type='GEOMETRY';enabled=m('MULTIPLY',m('GREATER_THAN',gain,1e-6,'Juice on'),m('MULTIPLY',m('GREATER_THAN',mode,.5,'Cut active'),m('GREATER_THAN',cells,1e-6,'Reference present'),'Valid surface'),'Enable output');w(enabled,sw.inputs['Switch']);w(inp.outputs[0],sw.inputs['False']);w(material.outputs['Geometry'],sw.inputs['True']);w(sw.outputs[0],out.inputs[0])
    for i,x in enumerate(N):x.location=((i//9)*225,-(i%9)*175)
    mod=obj.modifiers.new('SL Juice | native optical pool surface','NODES');mod.node_group=g
    s['SL Juice status']='Research open connected optical interfaces, ARTIST; no liquid volume solver or Frucht code.'
    return obj,g
if __name__=='__main__':
    src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists();assert hashlib.sha256(src.read_bytes()).hexdigest()==PIN
    bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);obj,g=install(bpy.data.objects[BODY]);bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()));print(json.dumps({'nodes':len(g.nodes),'scene_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}),flush=True)
