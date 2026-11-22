from pathlib import Path
import sys,json,hashlib
import bpy
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'src')]
from fruit_platform import make_context
from fruit_morphometry import load_catalog
from controls import SharedDeformation
SHA='24a3f7a2b9b157aac3b5a8aa30aa1b84d2404be64df67f74705665de3dbf74b4'
source,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert hashlib.sha256(source.read_bytes()).hexdigest()==SHA
out.mkdir(parents=True,exist_ok=False)
catalog=load_catalog(ROOT/'data/morphometry/measurements-v1.json')
reports=[]
for name,width,height in [('elongated',.80,1.15),('round',1.10,.90)]:
    control=SharedDeformation(make_context(catalog,'Camarosa','unified-'+name),width,height)
    bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),use_scripts=False)
    scene=bpy.context.scene;root=scene.objects['Strawberry | PR29 rest space']
    assert all(o.parent==root for o in scene.objects if o.get('role') in {'receptacle','achene','sepal','pedicel'} or o.type=='CURVE')
    root['unified_width_factor']=width;root['unified_height_factor']=height
    for key in ['unified_width_factor','unified_height_factor']:
        root.id_properties_ui(key).update(min=.65,max=1.35,description='ARTIST affine morphology, not measured cultivar size')
    for axis,key in enumerate(['unified_width_factor','unified_width_factor','unified_height_factor']):
        driver=root.driver_add('scale',axis).driver;driver.type='AVERAGE'
        var=driver.variables.new();var.type='SINGLE_PROP';var.name='control'
        var.targets[0].id=root;var.targets[0].data_path='["'+key+'"]'
    root.update_tag();bpy.context.view_layer.update()
    scene['Unified context record']=json.dumps(control.record(),sort_keys=True)
    scene['Unified control digest']=control.digest()
    scene['Shared mapping limitation']='539diagnostic endpoints are not connected to264realachenes; affine coherence only'
    points=[scene.objects['Receptacle | canonical PR29 hull'].matrix_world@v.co
            for v in scene.objects['Receptacle | canonical PR29 hull'].data.vertices]
    mm=scene.unit_settings.scale_length*1000
    dims=[(max(p[i] for p in points)-min(p[i] for p in points))*mm for i in range(3)]
    record=control.record();record.update(source_sha256=SHA,control_digest=control.digest(),actual_body_dimensions_mm=dims,
        reference_mm_per_model_unit=mm,world_from_reference=[list(row) for row in root.matrix_world])
    path=out/(name+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path.resolve()),compress=True)
    record['scene_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    (out/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n');reports.append(record)
(out/'controls-manifest.json').write_text(json.dumps(reports,indent=2)+'\n')
