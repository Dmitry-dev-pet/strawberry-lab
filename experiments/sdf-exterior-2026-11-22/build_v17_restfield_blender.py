"""Real Blender 5.2.4 scenes from verified v12, source 3D rest-field only.

Safe: never overwrite v12, do not modify GN group/geometry/material settings,
only bind new source-specific packed RGB atlas through 2 shader + 2 GN samplers.
Two alternatives: remap only and same remap after source-space Gaussian smooth.
No Frucht/GPL nodes, original video, generated image or other third-party assets.
"""
import bpy,numpy as np,json,hashlib,time,os
from pathlib import Path
BASE=Path('/mnt/data/strawberry-diagnostics/v12.blend')
OUT=Path('/mnt/data/strawberry-v17')
BASE_SHA='300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_SHA
start=time.monotonic()
report={'blender':bpy.app.version_string,'input_blend_sha256':BASE_SHA,'versions':{},'field_only':True,'source_atlas':'SDF proof v4 | 192^3 sparse volume and continuous branches','voxel_dimensions':[192,192,192],
    'no_geometry_material_node_modifications':True,'science':'ARTIST, not microscopic reconstruction'}
for variant in ('v17a','v17b'):
    dest=OUT/f'strawberry-{variant}-restfield.blend'
    png=OUT/f'packed-{variant}-restfield192.png'
    assert not dest.exists() and not png.exists(), 'Refusing overwrite original research artifacts'
    bpy.ops.wm.open_mainfile(filepath=str(BASE),use_scripts=False)
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    original=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
    assert original.packed_file and list(original.size)==[3072,2304] and original.colorspace_settings.name=='Non-Color'
    field=np.load(OUT/f'{variant}-source-R-192.npy')
    assert field.shape==(192,192,192) and np.all((field>=0)&(field<=1))
    pixels=np.empty((2304,3072,4),np.float32)
    original.pixels.foreach_get(pixels.ravel())
    g_b_before=pixels[:,:,:].copy() # read-only verification below
    for z in range(192):
        row=z//16;col=z%16
        pixels[row*192:(row+1)*192,col*192:(col+1)*192,0]=field[z]
    assert np.array_equal(pixels[:,:,1:4],g_b_before[:,:,1:4])
    img=bpy.data.images.new(f'Strawberry {variant} | original 192^3 RGB rest-space (ARTIST)',width=3072,height=2304,alpha=True,float_buffer=False)
    img.colorspace_settings.name='Non-Color'
    img.pixels.foreach_set(pixels.ravel());img.update()
    img.filepath_raw=str(png);img.file_format='PNG';img.save();img.pack()
    image_count={'shader':0,'gn':0}
    for mat in bpy.data.materials:
        if not mat.use_nodes:continue
        for node in mat.node_tree.nodes:
            if node.bl_idname=='ShaderNodeTexImage' and node.image==original:
                node.image=img;image_count['shader']+=1
    for group in bpy.data.node_groups:
        if group.bl_idname!='GeometryNodeTree':continue
        for node in group.nodes:
            if node.bl_idname=='GeometryNodeImageTexture' and node.inputs['Image'].default_value==original:
                node.inputs['Image'].default_value=img;image_count['gn']+=1
    assert image_count=={'shader':2,'gn':2},image_count
    scene=bpy.context.scene
    scene[f'{variant}_hypothesis']='Same source rest-space atlas, original A/B geometry + shader, new bounded 3D vessel signal only'
    scene[f'{variant}_biology']='ARTIST, not histological validation or Frucht source code'
    scene.frame_set(20)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    # Ignore Blender-generated temporary .blend1 backups, not created with save_version=0.
    report['versions'][variant]={'blend':dest.name,'blend_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
      'image':png.name,'image_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),
      'binding_counts':image_count,'source_R_sha256':hashlib.sha256((OUT/f'{variant}-source-R-192.npy').read_bytes()).hexdigest(),
      'image_packed':bool(img.packed_file)}
    print('V17_SAVED',variant,json.dumps(report['versions'][variant],ensure_ascii=False),flush=True)
report['seconds']=round(time.monotonic()-start,2)
(OUT/'v17-build.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('V17_BUILD_COMPLETE',json.dumps({'seconds':report['seconds'],'variants':list(report['versions'])},ensure_ascii=False))
