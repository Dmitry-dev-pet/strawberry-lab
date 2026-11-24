"""Standalone native Blender Geometry Nodes trilinear R/G sampling of an owned 192^3 atlas.

Portable reconstruction of the already-audited Strawberry Lab V8/V20 coordinate
method: bilinear slice samples from a tiled 16×12 Non-Color 2D float image,
then a linear mix of z-neighbor slices. No dependency on private source .blend,
commercial/GPL Frucht node templates, or per-cutter image baking.
"""
import bpy

def make_sampler(image,bounds,n=192,columns=16):
    assert n==192 and columns==16 and image.size[:]==(3072,2304)
    rows=n//columns
    g=bpy.data.node_groups.new('V20 bridge | independent source 192-cube RGB atlas sampler', 'GeometryNodeTree')
    g.interface.new_socket(name='rest_xyz_mm',in_out='INPUT',socket_type='NodeSocketVector')
    for name in ('core','halo'): g.interface.new_socket(name=name,in_out='OUTPUT',socket_type='NodeSocketFloat')
    inp=g.nodes.new('NodeGroupInput');out=g.nodes.new('NodeGroupOutput')
    def wire(a,b):g.links.new(a,b)
    def math(op,a,b=None,name=None):
        x=g.nodes.new('ShaderNodeMath');x.operation=op
        if name:x.name=x.label=name
        for i,value in enumerate([a,b]):
            if value is None:continue
            if isinstance(value,(int,float)):x.inputs[i].default_value=value
            else:wire(value,x.inputs[i])
        return x.outputs[0]
    trans=g.nodes.new('ShaderNodeVectorMath');trans.name='V20 bridge | physical mm to normalized XYZ';trans.operation='MULTIPLY_ADD'
    wire(inp.outputs['rest_xyz_mm'],trans.inputs[0])
    trans.inputs[1].default_value=tuple(1/(b[1]-b[0]) for b in bounds)
    trans.inputs[2].default_value=tuple(-b[0]/(b[1]-b[0]) for b in bounds)
    xyz=g.nodes.new('ShaderNodeSeparateXYZ');wire(trans.outputs['Vector'],xyz.inputs[0])
    def clamp(a):return math('MINIMUM',math('MAXIMUM',a,0.),1.)
    x=clamp(xyz.outputs['X']);y=clamp(xyz.outputs['Y']);z=clamp(xyz.outputs['Z'])
    gx=math('ADD', math('MULTIPLY',x,(n-1)/n),.5/n)
    gy=math('ADD', math('MULTIPLY',y,(n-1)/n),.5/n)
    iz=math('MULTIPLY',z,n-1)
    low=math('FLOOR',iz);high=math('MINIMUM',math('ADD',low,1.),n-1)
    fz=math('SUBTRACT',iz,low)
    samples=[]
    for j,k in enumerate([low,high]):
        tile_col=math('FLOORED_MODULO',k,columns)
        tile_row=math('FLOOR',math('DIVIDE',k,columns))
        u=math('DIVIDE',math('ADD',tile_col,gx),columns)
        v=math('DIVIDE',math('ADD',tile_row,gy),rows)
        uv=g.nodes.new('ShaderNodeCombineXYZ');wire(u,uv.inputs['X']);wire(v,uv.inputs['Y'])
        image_node=g.nodes.new('GeometryNodeImageTexture');image_node.name=f'V20 bridge | image tile {j}'
        image_node.inputs['Image'].default_value=image
        wire(uv.outputs['Vector'],image_node.inputs['Vector'])
        split=g.nodes.new('FunctionNodeSeparateColor');split.mode='RGB'
        wire(image_node.outputs['Color'],split.inputs['Color'])
        samples.append(split)
    for channel,label in [('Red','core'),('Green','halo')]:
        val=math('ADD',math('MULTIPLY',samples[0].outputs[channel],math('SUBTRACT',1.,fz)),math('MULTIPLY',samples[1].outputs[channel],fz))
        wire(val,out.inputs[label])
    g['source']='own preexisting V8/V20 XY bilinear + Z lerp algorithm, reconstructed independently'
    g['grid_bounds_mm']=repr(bounds)
    return g
