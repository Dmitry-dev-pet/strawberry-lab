"""Explicit physical cutter bias; no cap welding or changes to source geometry/CDT."""
BIAS_REST_Y_MM=.001
KNIFE='LIVE CUT | move or rotate this Empty'
def apply_policy(scene):
    knife=scene.objects[KNIFE]
    knife.delta_location.y=BIAS_REST_Y_MM/(scene.unit_settings.scale_length*1000)
    knife['physical_rest_y_bias_mm']=BIAS_REST_Y_MM
    knife['bias_note']='Physical translation +0.001mm in rest-Y; requested location/euler remain user pose. Matrix world is the real blade plane.'
    scene['Physical blade offset']='Explicit +0.001mm rest-Y via native delta_location; applies in Fast and Exact, including scripts-disabled rendering'
    scene['Generator Fast only']=False
    text=__import__('bpy').data.texts['TISSUE_ZONES__RUN.py'];code=text.as_string()
    needle='        layout = self.layout\n        if context.scene.get(\'Generator Fast only\'):'
    assert code.count(needle)==1
    code=code.replace(needle,"        layout = self.layout\n        layout.label(text='Physical blade offset: +0.001 mm rest-Y')\n        if context.scene.get('Generator Fast only'):")
    text.clear();text.write(code)

def validate_exact_caps(scene):
    """Gate newly generated output with float64 physical metrics and original Exact checks."""
    from validate_pits import activate_runtime,activate,body_mesh,pose_knife,flush_callback,measure,KNIFE
    from validate_exact_cut import surface
    from strawberry_generator.seam_fix.probe import metrics
    import bpy
    r=activate_runtime();session=r['session'];body=scene.objects['Receptacle | canonical PR29 hull'];activate(scene,'matched');rows=[]
    for pose in [(0,0,0),(.08,29,32),(-.26,0,0)]:
        bpy.ops.strawberry.exact_quality(exact=False);pose_knife(scene.objects[KNIFE],pose);bpy.context.view_layer.update();fast=body_mesh(body);skin=surface(fast);fm=metrics(fast)
        if not fm['closed_connected_positive'] or fm['zero_edges_all'] or fm['zero_polygon_faces'] or fm['zero_render_triangles']:raise ValueError('Unsafe native cap for requested pose '+str(pose))
        if bpy.ops.strawberry.exact_quality(exact=True)!={'FINISHED'}:raise ValueError('Original Exact CDT failed '+str(session.error))
        if bpy.app.timers.is_registered(r['timer']):flush_callback(r)
        else:session.refresh()
        exact=body_mesh(body);em=metrics(exact)
        if not em['closed_connected_positive'] or em['zero_edges_all'] or em['zero_polygon_faces'] or em['zero_render_triangles']:raise ValueError('Unsafe Exact geometry for requested pose '+str(pose))
        assert surface(exact)==skin
        displacement,_=measure(scene,body,exact);assert displacement['max_displacement_mm']>.01
        rows.append({'requested_pose':pose,'physical_knife_matrix':[list(row) for row in scene.objects[KNIFE].matrix_world],'physical_rest_y_bias_mm':BIAS_REST_Y_MM,'Fast':fm,'Exact':em,'displacement':displacement})
    bpy.ops.strawberry.exact_quality(exact=False);activate(scene,'whole')
    return {'status':'PASS_FOR_TESTED_POSES_WITH_EXPLICIT_PHYSICAL_OFFSET','poses':rows}
