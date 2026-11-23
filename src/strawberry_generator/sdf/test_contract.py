"""Blender regression gates for saved native SDF graph, units and field bindings."""
from pathlib import Path
import sys,unittest
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from common import BODY,REST,ATLAS
class SavedSDFContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  bpy.ops.wm.open_mainfile(filepath=str(Path(sys.argv[sys.argv.index('--')+1]).resolve()),use_scripts=False);cls.body=bpy.context.scene.objects[BODY];cls.g=cls.body.modifiers[0].node_group
 def test_zero_isosurface_and_no_mesh_boolean(self):
  nodes=self.g.nodes;self.assertEqual(sum(n.bl_idname=='GeometryNodeMeshToSDFGrid' for n in nodes),2);self.assertEqual(sum(n.bl_idname=='GeometryNodeSDFGridBoolean' for n in nodes),1)
  for n in nodes:
   if n.bl_idname=='GeometryNodeGridToMesh':self.assertEqual(n.inputs['Threshold'].default_value,0)
  self.assertFalse(any(m.type=='BOOLEAN' for o in bpy.context.scene.objects for m in o.modifiers))
 def test_actual_mm_conversion(self):
  mm=bpy.context.scene.unit_settings.scale_length*1000
  for n in self.g.nodes:
   if n.bl_idname=='GeometryNodeMeshToSDFGrid':
    divide=n.inputs['Voxel Size'].links[0].from_node;self.assertEqual(divide.operation,'DIVIDE');self.assertAlmostEqual(divide.inputs[1].default_value,mm,places=5)
 def test_true_rest_field_and_one_packed_atlas(self):
  self.assertTrue(any(n.bl_idname=='GeometryNodeStoreNamedAttribute' and n.inputs['Name'].default_value==REST for n in self.g.nodes))
  cap=next(m for m in bpy.data.materials if m.name.startswith('SDF | inherited'))
  self.assertEqual({n.image.name for n in cap.node_tree.nodes if n.type=='TEX_IMAGE'},{ATLAS})
  self.assertTrue(any(n.type=='ATTRIBUTE' and n.attribute_name==REST and n.outputs['Vector'].is_linked for n in cap.node_tree.nodes))
  inverse=next(n for n in cap.node_tree.nodes if n.label=='Analytic nonlinear inverse: physical -> original PR29 rest');self.assertFalse(inverse.outputs[0].is_linked)
  self.assertEqual(sum(n.type=='TEX_VORONOI' and n.name.startswith('Own 3D wetness') for n in cap.node_tree.nodes),3)
 def test_seed_mask_uses_all_seed_vertices_not_centers(self):
  masks=[g for g in bpy.data.node_groups if g.name.startswith('SDF | live seed vertex intersection guard')]
  self.assertEqual(len(masks),1)
  stats=[n for n in masks[0].nodes if n.bl_idname=='GeometryNodeAttributeStatistic']
  self.assertEqual(len(stats),2)
  self.assertTrue(all(n.data_type=='FLOAT' and n.domain=='POINT' and n.outputs['Min'].is_linked for n in stats))
  self.assertFalse(any(n.data_type=='FLOAT_VECTOR' and n.outputs['Mean'].is_linked for n in stats))
 def test_native_saved_controls_not_embedded_runtime(self):
  self.assertEqual(self.body['sdf_mode'],0);self.assertAlmostEqual(self.body['sdf_voxel_mm'],.20)
  self.assertFalse(any(t.name.endswith('.py') for t in bpy.data.texts))
  self.assertEqual([l.name for l in bpy.context.scene.view_layers],['SDF | live'])
if __name__=='__main__':
 result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(SavedSDFContract))
 if not result.wasSuccessful():raise RuntimeError('SDF contract regression failed')
