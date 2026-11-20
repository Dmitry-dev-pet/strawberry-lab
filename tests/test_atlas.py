"""Pure-Python tests for synthetic rest-space 3D tissue atlas (no Blender)."""
import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from bake_rest_atlas import N, BOUNDS,field,generate
class AtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.atlas=generate()
    def test_atlas_shape(self):self.assertEqual(self.atlas.shape,(512,512,3))
    def test_repeatability(self):self.assertTrue(np.array_equal(self.atlas,generate()))
    def test_center_pith_vs_outer(self):
        self.assertGreater(float(field(0,0,0)[2]),float(field(1,1,0)[2]))
    def test_distinct_layer_information(self):
        self.assertGreater(int(self.atlas[:,:,0].max()),int(self.atlas[:,:,0].min())+100)
        self.assertGreater(int(self.atlas[:,:,2].max()),int(self.atlas[:,:,2].min())+100)
    def test_3d_slices_change(self):
        # Atlas uses bottom-left tile 0, z-indexed; every tile is a unique axial plane.
        tile0=self.atlas[7*N:8*N,0:N]
        tile30=self.atlas[(7-3)*N:(8-3)*N,6*N:7*N]
        self.assertFalse(np.array_equal(tile0,tile30))
    def test_tile_orientation_channel_samples(self):
        coords=np.linspace(BOUNDS[0],BOUNDS[1],N,dtype=np.float32)
        for iz in (0,9,31,63):
            for ix,iy in ((0,0),(20,25),(63,63)):
                a,b,c=field(coords[ix],coords[iy],coords[iz]);sample=np.array([a,b,c])
                ty=iz//8;tx=iz%8
                got=self.atlas[(7-ty)*N+(N-1-iy),tx*N+ix].astype(float)/255
                self.assertLess(np.max(np.abs(got-sample)),.005)
if __name__=='__main__':unittest.main()