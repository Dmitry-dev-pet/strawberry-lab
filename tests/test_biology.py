"""Biological geometry invariants; no Blender dependency."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import unittest
from math import pi
from strawberry_biology import (P,point,radius,fields,vascular_route,vascular_graph,
                                validate_graph,sample_achenes,tissue_color,normal)

class BiologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.anchors=sample_achenes();cls.branches=vascular_graph(cls.anchors)

    def test_stable_positions(self):
        self.assertEqual(self.anchors,sample_achenes())
        self.assertGreater(len(self.anchors),450)

    def test_all_seeds_connected(self):
        ok,msg=validate_graph(self.anchors,self.branches)
        self.assertTrue(ok,msg)
        self.assertEqual(len(self.branches),len(self.anchors))

    def test_vascular_paths_end_at_corresponding_achene(self):
        for a,b in zip(self.anchors,self.branches):
            self.assertEqual(a['id'],b['achene_id'])
            self.assertEqual(b['points'][-1],b['terminal'])
            self.assertLess(sum((b['terminal'][k]-a['point'][k])**2 for k in range(3)),.002)

    def test_both_slice_axes_share_same_3d_tissue_model(self):
        # At 3D intersection (x, y=0, z=0): longitudinal and transverse cuts
        # must query precisely the same values.
        for i in range(-12,13):
            x=i*.075
            a=fields(x,0,0)
            b=fields(x,0.,0.)
            self.assertEqual(a,b)
            self.assertEqual(tissue_color(x,0,0),tissue_color(x,0.,0.))

    def test_core_vs_outer_cortex(self):
        f=fields(0.,0.,0.)
        s=fields(1.15,0.,0.)
        self.assertGreater(f['pith'],.8)
        self.assertGreater(s['cortex'],.7)
        self.assertLess(s['pith'],.01)
        self.assertFalse(fields(5,0,0)['inside'])

    def test_surface_normals_point_outward(self):
        for a in self.anchors[::7]:
            px,py,_=a['point'];nx,ny,_=a['normal']
            self.assertGreater(nx*px+ny*py,0)

    def test_tissue_color_range(self):
        for i in range(30):
            col=tissue_color(.01*i,0,-.6+i*.04)
            self.assertTrue(all(0<=x<=1 for x in col))

    def test_surface_radius_stays_positive(self):
        for t in [.01,.1,.25,.5,.75,.9,.99]:
            for i in range(19):
                self.assertGreater(radius(t,2*pi*i/19),0)

if __name__=='__main__':unittest.main()