"""Run in Blender: regression for physical degeneracy, separate from topology."""
import sys, unittest
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from probe import metrics
class PhysicalMetrics(unittest.TestCase):
    def check_mesh(self, vertices, faces):
        mesh=bpy.data.meshes.new('metric-regression')
        try:
            mesh.from_pydata(vertices,[],faces)
            return metrics(mesh)
        finally:bpy.data.meshes.remove(mesh)
    def test_coincident_ids_are_not_clean(self):
        m=self.check_mesh([(0,0,0),(0,0,0),(1,1,0)],[(0,1,2)])
        self.assertEqual(m['zero_edges_all'],1)
        self.assertEqual(m['zero_render_triangles'],1)
    def test_collinear_face_without_zero_edges(self):
        m=self.check_mesh([(0,0,0),(1,0,0),(2,0,0)],[(0,1,2)])
        self.assertEqual(m['zero_edges_all'],0)
        self.assertEqual(m['zero_polygon_faces'],1)
        self.assertEqual(m['zero_render_triangles'],1)
    def test_small_nonzero_is_distinct(self):
        m=self.check_mesh([(0,0,0),(1e-12,0,0),(0,1,0)],[(0,1,2)])
        self.assertEqual(m['zero_edges_all'],0)
        self.assertEqual(m['zero_polygon_faces'],0)
        self.assertEqual(m['zero_render_triangles'],0)
if __name__=='__main__':
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(PhysicalMetrics))
    if not result.wasSuccessful():raise RuntimeError('physical metrics regression failed')
