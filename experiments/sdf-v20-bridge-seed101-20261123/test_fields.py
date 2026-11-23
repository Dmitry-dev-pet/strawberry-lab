"""Pure Python tests of reused OWN Strawberry Lab v19/v20 field semantics."""
import unittest
import numpy as np
import v19_graph
from fields import wider_graph,pack_core_halo,suppression
class SourceFieldTests(unittest.TestCase):
 def test_terminal_joint_graph(self):
  anchor=np.array([(14.*np.cos(2*np.pi*j/264),14.*np.sin(2*np.pi*j/264),2.+44.*j/263) for j in range(264)],np.float32)
  graph=v19_graph.make_graph(anchor);m=v19_graph.validate_graph(graph,anchor)
  self.assertEqual(m['segments_total'],557);self.assertEqual(m['endpoints_on_achene_anchors'],264)
 def test_wide_halo_dominates_core(self):
  r=np.linspace(0,1,17,dtype=np.float32)
  c=np.maximum(0.,1.-r);h=np.maximum(c,np.exp(-.5*(r/.6)**2))
  self.assertTrue((h>=c).all());self.assertTrue((suppression(h)<=suppression(c)+1e-7).all())
 def test_packing_independent_channels(self):
  core=np.zeros((16,16,16),np.float32);core[5,6,7]=.3;halo=core.copy();halo[5,6,7]=.7
  packed=pack_core_halo(core,halo);self.assertEqual(packed.shape,(16,256,4))
  self.assertAlmostEqual(packed[6,5*16+7,0],.3,places=5);self.assertAlmostEqual(packed[6,5*16+7,1],.7,places=5)
 def test_invalid_halo_fails_closed(self):
  core=np.ones((16,16,16),np.float32);halo=np.zeros_like(core)
  with self.assertRaises(ValueError):pack_core_halo(core,halo)
 def test_wider_graph_uses_only_sigma(self):
  g=[{'id':1,'sigma_mm':.3,'amplitude':.7}];w=wider_graph(g)
  self.assertAlmostEqual(w[0]['sigma_mm'],.54);self.assertEqual(w[0]['amplitude'],g[0]['amplitude'])
if __name__=='__main__':unittest.main()
