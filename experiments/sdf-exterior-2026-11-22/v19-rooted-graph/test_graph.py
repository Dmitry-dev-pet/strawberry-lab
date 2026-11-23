import unittest, numpy as np, hashlib
from v19_graph import make_graph,validate_graph,rasterize_graph
class V19GraphTests(unittest.TestCase):
  def setUp(self):
    k=np.arange(264)
    self.anchors=np.stack([12*np.cos(k*2.39996),12*np.sin(k*2.39996),3+42*(k+.5)/264],axis=1).astype(np.float32)
  def test_rooted_graph(self):
    self.assertTrue(validate_graph(make_graph(self.anchors),self.anchors)['all_connected_to_one_root'])
  def test_repeatable(self):
    a=make_graph(self.anchors);b=make_graph(self.anchors)
    self.assertTrue(all(np.array_equal(x['points'],y['points']) for x,y in zip(a,b)))
  def test_all_anchors_and_joints_exact(self):
    s=make_graph(self.anchors);d=validate_graph(s,self.anchors)
    self.assertEqual(d['endpoints_on_achene_anchors'],264)
    self.assertEqual(d['parent_joint_max_error_mm'],0)
  def test_small_volume_finite(self):
    seg=make_graph(self.anchors)
    f,d=rasterize_graph(seg,64)
    self.assertEqual(f.shape,(64,64,64));self.assertGreater(d['field_max'],0.3)
    self.assertTrue(np.isfinite(f).all())
if __name__=='__main__': unittest.main()
