"""Conforming cap fallback: triangulate original faces, insert only interior centroids.
Embedded after the existing CDT routine. Never weld/split/move a boundary vertex/edge.
"""
def conforming_cap_patch(bm, body_to_knife, mm_per_unit):
    faces=[f for f in bm.faces if f.material_index==CAP]
    if not faces:return None
    outward=body_to_knife.to_3x3().transposed()@Vector((0.,-1.,0.));outward.normalize()
    seam={e for f in faces for e in f.edges if any(g.material_index!=CAP for g in e.link_faces)}
    seam_vertices={v for e in seam for v in e.verts};original_positions={v:tuple(v.co) for v in seam_vertices}
    if not seam:raise ValueError('Conforming cap has no skin boundary')
    for f in faces:
        if f.normal.dot(outward)<.99:raise ValueError('Conforming cap winding mismatch')
        if any(abs((body_to_knife@v.co).y)>PLANE_EPS for v in f.verts):raise ValueError('Conforming cap not on physical plane')
    bmesh.ops.triangulate(bm,faces=faces,quad_method='BEAUTY',ngon_method='BEAUTY')
    triangles=[f for f in bm.faces if f.material_index==CAP]
    vertices={v for f in triangles for v in f.verts}
    if len(vertices)>MAX_CAP_VERTICES:raise ValueError('Original cap exceeds vertex budget')
    target_area=.5*(STEP_MM/mm_per_unit)**2
    inherited=set(triangles);boundary_degenerates=0
    stack=list(triangles)
    while stack:
        f=stack.pop();f.smooth=True
        if len(f.verts)!=3:raise ValueError('Fallback left non-triangle cap face')
        area=f.calc_area()
        if area<=0:
            # These triangles contain only unchanged original boundary vertices.
            # A zero-length native seam edge cannot acquire nonzero triangle area
            # without moving/welding that edge. Retain it; create no new degenerate face.
            if f not in inherited or any(v not in seam_vertices for v in f.verts):
                raise ValueError('Fallback produced a NEW degenerate triangle')
            boundary_degenerates+=1
            continue
        longest=max(e.calc_length()**2 for e in f.edges)
        # Keep tiny inherited slivers, but never multiply them into a refinement cascade.
        if area<=target_area or area/max(longest,1e-30)<1e-6:continue
        if len(vertices)>=MAX_CAP_VERTICES:raise ValueError('Conforming cap exceeds vertex budget')
        a,b,c=tuple(f.verts);point=bm.verts.new((a.co+b.co+c.co)/3);vertices.add(point)
        bm.faces.remove(f)
        for x,y in ((a,b),(b,c),(c,a)):
            child=bm.faces.new((x,y,point));child.material_index=CAP;child.smooth=True;stack.append(child)
    for v,p in original_positions.items():
        if not v.is_valid or tuple(v.co)!=p:raise ValueError('Conforming cap moved a seam vertex')
    if not all(e.is_valid and e.is_manifold for e in seam):raise ValueError('Conforming cap changed a seam edge')
    for e in seam:e.smooth=False
    conforming_cap_patch.last_boundary_degenerates=boundary_degenerates
    return outward,vertices,seam_vertices,seam
