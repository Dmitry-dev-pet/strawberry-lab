"""Independent material-only controls on PR50 shadow-transparent baseline.
All coefficients ARTIST. Positive signed clearance is a normal-direction
thickness proxy, not a volume optical path. No reference nodes or presets.
"""
import bpy,sys,hashlib,json
from pathlib import Path
PIN='361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963'
JUICE='SL Juice | clear dielectric ARTIST'; CAP='SDF | inherited 150^3 tissue + own multiscale wetness'
PREFIX='SL Field Optical | '
def add(g,typ,label):
    n=g.nodes.new(typ);n.name=n.label=PREFIX+label;return n

def tint():
    g=bpy.data.materials[JUICE].node_tree; p=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');orig=tuple(p.inputs['Base Color'].default_value);assert not p.inputs['Base Color'].is_linked
    a=add(g,'ShaderNodeAttribute','Existing signed clearance mm');a.attribute_name='sl_juice_clearance_mm';a.attribute_type='GEOMETRY'
    h=add(g,'ShaderNodeClamp','Positive bounded thickness proxy');h.inputs['Min'].default_value=0.;h.inputs['Max'].default_value=.20;g.links.new(a.outputs['Fac'],h.inputs['Value'])
    scale=add(g,'ShaderNodeMath','Normalize to 0.10 mm');scale.operation='DIVIDE';scale.inputs[1].default_value=.10;g.links.new(h.outputs['Result'],scale.inputs[0])
    col=add(g,'ShaderNodeCombineColor','Independent channel attenuation');col.mode='RGB'
    for i,k in enumerate(('Red','Green','Blue')):
        n=add(g,'ShaderNodeMath',k+' attenuation');n.operation='POWER';n.inputs[0].default_value=orig[i];g.links.new(scale.outputs[0],n.inputs[1]);g.links.new(n.outputs[0],col.inputs[k]);n.location=(-440,-180*i)
    g.links.new(col.outputs['Color'],p.inputs['Base Color']);a.location=(-880,0);h.location=(-700,0);scale.location=(-520,180);col.location=(-210,0)
    return {'material':JUICE,'target':'Base Color','reference_thickness_mm':.10,'max_mm':.20,'old_linear_rgba':orig,'model':'C(h)=C0**clamp(h/0.10,0,2)','attribute':'sl_juice_clearance_mm'}

def scatter():
    g=bpy.data.materials[CAP].node_tree;p=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');s=p.inputs['Subsurface Scale'];assert not s.is_linked and abs(s.default_value-.012)<1e-7
    rest=next(n for n in g.nodes if n.type=='ATTRIBUTE' and n.attribute_name=='sdf_rest_position')
    xy=add(g,'ShaderNodeVectorMath','Rest-space radial projection');xy.operation='MULTIPLY';xy.inputs[1].default_value=(1.,1.,0.);g.links.new(rest.outputs['Vector'],xy.inputs[0])
    rad=add(g,'ShaderNodeVectorMath','Radius from fruit axis');rad.operation='LENGTH';g.links.new(xy.outputs['Vector'],rad.inputs[0])
    remap=add(g,'ShaderNodeMapRange','Smooth radial scattering scale');remap.clamp=True;remap.interpolation_type='SMOOTHERSTEP';g.links.new(rad.outputs['Value'],remap.inputs['Value'])
    for k,v in [('From Min',.12),('From Max',.75),('To Min',.006),('To Max',.020)]:remap.inputs[k].default_value=v
    g.links.new(remap.outputs['Result'],s);xy.location=(-900,-900);rad.location=(-680,-900);remap.location=(-440,-900)
    return {'material':CAP,'target':'Subsurface Scale','attribute':'sdf_rest_position','radial_limits_BU':[.12,.75],'scale_BU':[.006,.020],'weight_unchanged':p.inputs['Subsurface Weight'].default_value,'old_scale_BU':s.default_value}
if __name__=='__main__':
    src,variant,out=sys.argv[sys.argv.index('--')+1:];src=Path(src);out=Path(out);assert not out.exists() and hashlib.sha256(src.read_bytes()).hexdigest()==PIN
    bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);assert not bpy.data.objects['SL Juice | independent pool surface'].visible_shadow
    report={'variant':variant,'source_sha256':PIN,'changes':{'B':[tint],'C':[scatter]}[variant]}
    report['changes']=[f() for f in report['changes']];bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()));report['scene_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
