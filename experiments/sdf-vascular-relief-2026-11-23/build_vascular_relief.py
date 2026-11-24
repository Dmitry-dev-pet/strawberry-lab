"""Original vascular relief bridge on PR50 research scene; ARTIST only.
Reuse owned PR49 field/sampler. A=original PR50, B=cell domes attenuated near
vessels plus a narrow core and broad shoulder ridge. No material changes.
"""
from pathlib import Path
import sys,hashlib,json,zipfile,io
import bpy,numpy as np
BODY='Receptacle | canonical PR29 hull'
PIN_CELL='e22a3fe07a090724d181eadcf5a367802a74cdda8d299d25d6e681ae23a6638d'
PIN_BRIDGE='a43df0a7d38404193af313ba5faca60a1ba00ad6db6de855d54135b050a202eb'
PIN_CORE='23baa3ced5bc9172341d8ee6269671010f697f4a9226871c388029ed1cb69b1e'
PIN_HALO='6709f0e92788383b34c14eb2ad2fb78e76fa4ed961ea2634b5af5143b3df8d2e'
BOUNDS=((-25.,25.),(-25.,25.),(-2.,52.))
def sha(x):return hashlib.sha256(x).hexdigest()
def anchors():
    objs=sorted((o for o in bpy.context.scene.objects if o.get('role')=='achene'),key=lambda o:o.name)
    assert len(objs)==264
    return [(o.name,tuple(o['nonlinear_original_anchor'])) for o in objs]
def install(body,core,halo,pack_core_halo,make_sampler):
    mm=bpy.context.scene.unit_settings.scale_length*1000
    assert abs(mm-22.22222276)<1e-5
    g=next(m.node_group for m in body.modifiers if m.type=='NODES' and m.node_group.name.startswith('SL Cell Surface'))
    N,L=g.nodes,g.links
    def label(s):return next(n for n in N if n.label==s)
    def n(t,s):
        x=N.new(t);x.name=x.label=s;return x
    def w(a,b):
        if isinstance(a,(float,int,tuple)):b.default_value=a
        else:L.new(a,b)
    def m(op,a,b,s):
        x=n('ShaderNodeMath',s);x.operation=op;w(a,x.inputs[0]);w(b,x.inputs[1]);return x.outputs[0]
    def attr(s,t='FLOAT'):
        x=n('GeometryNodeInputNamedAttribute','Read '+s);x.data_type=t;x.inputs['Name'].default_value=s;return x.outputs['Attribute']
    def store(geo,s,val):
        x=n('GeometryNodeStoreNamedAttribute',s);x.data_type='FLOAT';x.domain='POINT';x.inputs['Name'].default_value=s;w(geo,x.inputs['Geometry']);w(val,x.inputs['Value']);return x.outputs['Geometry']
    def curve(a,lo,hi,b,c,s):
        x=n('ShaderNodeMapRange',s);x.clamp=True;x.interpolation_type='SMOOTHERSTEP';w(a,x.inputs['Value']);x.inputs['From Min'].default_value=lo;x.inputs['From Max'].default_value=hi;x.inputs['To Min'].default_value=b;x.inputs['To Max'].default_value=c;return x.outputs['Result']
    body['vascular_relief_gain']=0.;body.id_properties_ui('vascular_relief_gain').update(min=0.,max=1.,description='0 exact PR50 cell surface, 1 coupled vascular relief')
    gain=n('ShaderNodeValue','Vascular relief independent A/B');d=gain.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';v=d.variables.new();v.name='value';v.type='SINGLE_PROP';v.targets[0].id=body;v.targets[0].data_path='["vascular_relief_gain"]';gain=gain.outputs[0]
    cellgain=label('cell_surface_gain').outputs[0]
    height_store=label('sl_cell_height_mm');dome_store=label('sl_cell_dome');move=label('Cap-only dome displacement');scale=move.inputs['Offset'].links[0].from_node
    old_height=scale.inputs['Scale'].links[0].from_socket
    dome_fade=dome_store.inputs['Value'].links[0].from_node
    assert dome_fade.operation=='MULTIPLY'
    fade=dome_fade.inputs[1].links[0].from_socket
    geometry=height_store.inputs['Geometry'].links[0].from_socket
    pixels=pack_core_halo(core,halo)
    img=bpy.data.images.new('SL Vascular Relief | owned 192 cube core halo',width=3072,height=2304,alpha=True,float_buffer=True)
    img.colorspace_settings.name='Non-Color';img.pixels.foreach_set(pixels.ravel());img.update();img.pack()
    img['source']='Own PR49 seed101 atlas, same 264 rest anchors; R narrow core / G broad halo; ARTIST'
    sampler=make_sampler(img,BOUNDS)
    rest=attr('sdf_rest_position','FLOAT_VECTOR')
    trans=n('ShaderNodeVectorMath','Same rest xyz to graph millimetres');trans.operation='MULTIPLY_ADD';w(rest,trans.inputs[0]);trans.inputs[1].default_value=(mm,mm,mm);trans.inputs[2].default_value=(0.,0.,27.)
    sample=n('GeometryNodeGroup','Owned trilinear core and halo');sample.node_tree=sampler;w(trans.outputs['Vector'],sample.inputs['rest_xyz_mm'])
    geometry=store(geometry,'sl_vascular_core',sample.outputs['core']);geometry=store(geometry,'sl_vascular_halo',sample.outputs['halo'])
    R=attr('sl_vascular_core');H=attr('sl_vascular_halo')
    suppression=curve(H,.04,.48,1.,.12,'Flatten cellular domes around vessels')
    factor=m('ADD',1.,m('MULTIPLY',gain,m('SUBTRACT',suppression,1.,'Suppression minus baseline'),'Live suppression delta'),'Cell multiplier')
    ridge=m('ADD',m('MULTIPLY',R,.12,'Narrow core lift mm'),m('MULTIPLY',H,.045,'Broad shoulder lift mm'),'Combined ridge mm')
    ridge=m('MULTIPLY',m('MULTIPLY',ridge,fade,'Original skin seam fade'),m('MULTIPLY',gain,cellgain,'Both gains'),'Effective vascular height mm')
    geometry=store(geometry,'sl_vascular_cell_multiplier',factor);geometry=store(geometry,'sl_vascular_ridge_mm',ridge)
    eff=attr('sl_vascular_cell_multiplier');rmm=attr('sl_vascular_ridge_mm')
    combined=m('ADD',m('MULTIPLY',old_height,eff,'Attenuated cell height BU'),m('DIVIDE',rmm,mm,'Vascular height BU'),'Coupled total height BU')
    sw=n('GeometryNodeSwitch','Exact PR50 height when disabled');sw.input_type='FLOAT';w(m('GREATER_THAN',gain,0.,'Vascular enabled'),sw.inputs['Switch']);w(old_height,sw.inputs['False']);w(combined,sw.inputs['True']);height=sw.outputs['Output']
    w(geometry,height_store.inputs['Geometry']);w(m('MULTIPLY',height,mm,'Actual combined height mm'),height_store.inputs['Value']);w(height,scale.inputs['Scale'])
    for i,x in enumerate(N):x.location=((i//8)*220,-(i%8)*180)
    bpy.context.scene['SL Vascular Relief status']='Original PR50 cells + owned PR49 core/halo, geometry-only, ARTIST; research'
    return g,sampler,img
if __name__=='__main__':
    cell,archive,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists();assert sha(cell.read_bytes())==PIN_CELL;assert sha(archive.read_bytes())==PIN_BRIDGE
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td,zipfile.ZipFile(archive) as z:
        for f in ('source/fields.py','source/sampler.py','scene/v20-bridge-portable.blend'):z.extract(f,td)
        sys.path.insert(0,str(Path(td)/'source'));from fields import pack_core_halo;from sampler import make_sampler
        a=np.load(io.BytesIO(z.read('fields/seed101-own-core-halo-192.npz')));core,halo=a['core'],a['halo'];assert sha(core.tobytes())==PIN_CORE and sha(halo.tobytes())==PIN_HALO and np.all(halo>=core)
        bpy.ops.wm.open_mainfile(filepath=str(Path(td)/'scene/v20-bridge-portable.blend'),use_scripts=False);old=anchors()
        bpy.ops.wm.open_mainfile(filepath=str(cell.resolve()),use_scripts=False);new=anchors();assert old==new,'Source seed anchors changed'
        body=bpy.data.objects[BODY];g,sampler,img=install(body,core,halo,pack_core_halo,make_sampler)
        bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()));print(json.dumps({'scene_sha':sha(out.read_bytes()),'anchors_identical':len(new),'cell_nodes':len(g.nodes),'sampler_nodes':len(sampler.nodes),'core_sha':PIN_CORE,'halo_sha':PIN_HALO,'packed_image_sha':sha(bytes(img.packed_file.data))}),flush=True)
