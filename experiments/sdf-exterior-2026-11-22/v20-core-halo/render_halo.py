"""Actual matched CPU Cycles renders of the saved independent halo experiment."""
import argparse,hashlib,json,sys,time,resource
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector

def camera_record(scene):
    c=scene.camera
    return {'name':c.name,'matrix_world':[list(r) for r in c.matrix_world],
            'type':c.data.type,'ortho_scale':c.data.ortho_scale,'lens':c.data.lens}

def main():
    p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True)
    p.add_argument('--shot',choices=['whole','plane','bite','macro','bite_macro'],required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--size',type=int,default=640)
    p.add_argument('--samples',type=int,default=24);p.add_argument('--clay',action='store_true')
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);t0=time.perf_counter()
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    assert not a.out.exists(),a.out
    a.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()),use_scripts=False)
    s=bpy.context.scene;s.frame_set(1 if a.shot=='whole' else 40 if a.shot.startswith('bite') else 20)
    original_camera=camera_record(s);macro_target=None
    bodyname='Receptacle | sculpted skin and achene pits' if a.shot=='whole' else 'SDF visible body | '+('bite' if a.shot.startswith('bite') else 'planar')
    if 'macro' in a.shot:
        ob=bpy.data.objects[bodyname];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
        rest=np.empty((len(m.vertices),3),np.float32);m.attributes['fruit_rest'].data.foreach_get('vector',rest.ravel())
        mask=np.empty(len(m.vertices),np.float32);m.attributes['v20_cap_rim'].data.foreach_get('value',mask)
        ids=np.flatnonzero(mask>.99);assert len(ids)>0
        desired=np.array([5.,22.],np.float32)
        j=ids[np.argmin(np.sum((rest[ids][:,[0,2]]-desired)**2,axis=1))]
        # Use identical REST coordinates, not A/B-displaced positions, for framing.
        target=ob.matrix_world@Vector(rest[j].tolist());macro_target=target[:]
        ev.to_mesh_clear()
        cam=s.camera;assert cam.data.type=='ORTHO'
        direction=cam.rotation_euler.to_quaternion()@Vector((0,0,-1))
        distance=(cam.location-target).length;cam.location=target-direction*distance
        cam.data.ortho_scale=12.0  # ARTIST diagnostic field of view, identical A/B.
    if a.clay:
        for ob in s.objects:
            if ob.type in {'MESH','CURVE','CURVES','VOLUME','SURFACE','META','FONT'}:
                ob.hide_render=(ob.name!=bodyname)
        mat=bpy.data.materials.new('V20 diagnostic neutral clay; no bump or coat');mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.35,.35,.35,1.)
        bsdf.inputs['Roughness'].default_value=.62;bsdf.inputs['Subsurface Weight'].default_value=0.
        bsdf.inputs['Coat Weight'].default_value=0.
        for layer in s.view_layers:layer.material_override=mat
    s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples
    s.render.resolution_x=a.size;s.render.resolution_y=a.size;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.film_transparent=False
    s.render.filepath=str(a.out.resolve())
    bpy.context.view_layer.update()
    settings={'frame':s.frame_current,'camera':camera_record(s),'original_camera':original_camera,'macro_rest_target_world':macro_target,
              'resolution':[a.size,a.size],'samples':a.samples,'seed':s.cycles.seed,'denoising':s.cycles.use_denoising,
              'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,
              'lights':[{'name':o.name,'matrix_world':[list(r) for r in o.matrix_world],'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT']}
    t=time.perf_counter();bpy.ops.render.render(write_still=True);elapsed=time.perf_counter()-t
    d={'variant':s.get('v20_variant'),'shot':a.shot,'clay':a.clay,'engine':'Cycles CPU','blender':bpy.app.version_string,
       'source':a.scene.name,'source_sha256':hashlib.sha256(a.scene.read_bytes()).hexdigest(),
       'image':a.out.name,'image_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'bytes':a.out.stat().st_size,
       'settings':settings,'render_seconds':elapsed,'total_script_seconds':time.perf_counter()-t0,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    a.out.with_suffix('.json').write_text(json.dumps(d,indent=2)+'\n')
    print('V20_ACTUAL_CYCLES',json.dumps({k:v for k,v in d.items() if k!='settings'}),flush=True)

if __name__=='__main__':main()
