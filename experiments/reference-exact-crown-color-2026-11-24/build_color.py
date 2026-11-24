"""Bounded ARTIST pigment revision on exact-crown. Reuse the existing shared skin,
regional flesh and foliage networks; keep geometry, SSS, roughness and lights fixed.
Separate output copy preserves the original palette and all prior research.
"""
import bpy, sys, json, hashlib
from pathlib import Path
PIN='6e7d052440772337dbc9f74b4603d8199f86517d39e7da5463c0bc26945b6984'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def linear(h):
    a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1.,)
def main():
    src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists()
    bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False)
    rows=[]
    def change(tree,node,index,value):
        n=tree.nodes[node];s=n.inputs[index];assert not s.is_linked,(tree.name,node,index)
        before=tuple(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value
        s.default_value=value;after=tuple(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value
        rows.append({'tree':tree.name,'node':node,'socket':s.identifier,'before':before,'after':after})
    skin=bpy.data.node_groups['SL Pigment | shared warm skin foundation v2'];p='Pigment v2 | '
    # Redder and darker ripe skin; preserve existing spatial ripeness and speckle masks.
    change(skin,p+'ripe red patches',1,linear('920E17'));change(skin,p+'ripe red patches',2,linear('D01B22'))
    change(skin,p+'stem colour',2,linear('C45832'));change(skin,p+'lighter stem shoulder','To Max',.36)
    # More saturated cortex, keep unchanged spatial ring/core/halo transitions and wall shading.
    flesh=bpy.data.node_groups['SL Pigment | regional tissue v2']
    change(flesh,p+'warm red cortex',1,linear('B91A19'));change(flesh,p+'warm red cortex',2,linear('E33B2C'))
    change(flesh,p+'narrow warm edge',2,linear('D53A2C'))
    # Existing foliage gradients, independent of fruit grade: darker green, less yellow.
    for name,dark,light in [('Calyx • folded olive green','244918','58832D'),('Pedicel • green','315523','648738')]:
        t=bpy.data.materials[name].node_tree;n=next(n for n in t.nodes if n.label=='Leaf colour')
        for i,h in enumerate((dark,light)):
            e=n.color_ramp.elements[i];old=tuple(e.color);e.color=linear(h);rows.append({'tree':t.name,'node':n.name,'ramp_element':i,'before':old,'after':tuple(e.color)})
    t=bpy.data.materials['Calyx • folded olive green'].node_tree;n=next(n for n in t.nodes if n.label=='Midrib and secondary veins');change(t,n.name,2,linear('819A41'))
    # No geometry changes. No claim of measured reference RGB or true biology.
    bpy.context.scene['scope']='ARTIST regional palette revision on crown; unchanged tissue fields, geometry and optical coefficients'
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
    rec={'source_sha':PIN,'scene_sha':sha(out),'changed_values':rows,'scope':'material palette only; frozen existing procedural fields, shaders, geometry, lighting; no calibrated author RGB'}
    out.with_suffix('.json').write_text(json.dumps(rec,indent=2)+'\n');print('BUILT',json.dumps(rec),flush=True)
if __name__=='__main__':main()
