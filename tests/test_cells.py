"""Unit tests for reproducibility and 3D slice invariance in M1b."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import unittest
from strawberry_cells import (cell_properties,cell_measure,micro_tissue_color,
                              sample_slice_longitudinal,sample_slice_transverse)
from strawberry_biology import fields,tissue_color,P


class VolumetricCellTests(unittest.TestCase):
    def test_same_plane_intersection(self):
        # At intersection line (x, y=0, z=0), both orthogonal planes see
        # EXACT same 3D cell geometry; there are no orientation-specific maps.
        for k in range(-20,21):
            x=k*.051
            self.assertEqual(sample_slice_longitudinal(x,0),sample_slice_transverse(x,0))

    def test_not_2d_extruded(self):
        # Third coordinate changes F1/F2 and cell id; no xy-only pattern.
        a=cell_measure(.36,.21,.17)
        b=cell_measure(.36,.21,.49)
        self.assertNotEqual(a,b)
        self.assertNotEqual(a[2],b[2])

    def test_deterministic(self):
        a=cell_properties(.25,-.58,.72)
        self.assertEqual(a,cell_properties(.25,-.58,.72))
        self.assertNotEqual(a,cell_properties(.25,-.58,.72,seed=1730))

    def test_valid_wall_and_center(self):
        for i in range(-10,11):
            p=cell_properties(i*.07,.22,-.14)
            self.assertTrue(0<=p['wall']<=1)
            self.assertTrue(0<=p['centre']<=1)
            self.assertLessEqual(p['d1'],p['d2'])

    def test_no_cells_outside_receptacle(self):
        for x in [0,.4,.7,1.,2.,3.,5.]:
            f=fields(x,0,0)
            w=1. if f['inside'] else 0.
            base=tissue_color(x,0,0)
            col,recess,diag=micro_tissue_color(x,0,0,base,inside_weight=w)
            self.assertEqual(len(col),4)
            self.assertTrue(all(0<=c<=1 for c in col))
            if not f['inside']:
                self.assertAlmostEqual(recess,0)
                self.assertAlmostEqual(diag['wall'],0)

    def test_recess_is_real_3d_scalar(self):
        out=micro_tissue_color(.12,.3,.23,(.8,.3,.3,1))
        self.assertTrue(-.01<out[1]<.020)
        self.assertEqual(len(out[2]['cell_id']),3)

    def test_spacing_error(self):
        with self.assertRaises(ValueError):cell_measure(0,0,0,spacing=0.)


if __name__=='__main__':unittest.main()