import sys, unittest, pathlib, dataclasses, numpy as np
from neutral_contract import *
from fruit_morphometry import load_catalog
from fruit_platform import make_context
CATALOG=pathlib.Path(sys.argv.pop(1))
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=make_context(load_catalog(CATALOG),'Camarosa','neutral-101',seed=101)
        cls.a=make_stock(cls.ctx,264);cls.b=make_stock(cls.ctx,326);cls.repeat=make_stock(cls.ctx,264)
        cls.s=ShapeState(.16,-.10,1.12)
    def test_repeat(self):self.assertEqual(self.a,self.repeat)
    def test_counts(self):self.assertEqual((len(self.a.anchors),len(self.b.anchors)),(264,326))
    def test_count_invalidates(self):
        self.assertNotEqual(self.a.anchor_digest,self.b.anchor_digest);self.assertNotEqual(self.a.stock_key,self.b.stock_key)
        self.assertNotEqual(self.a.vessel_dependency_key({'test':1}),self.b.vessel_dependency_key({'test':1}))
        self.assertFalse(set(self.a.anchor_id(i) for i in range(264)) & set(self.b.anchor_id(i) for i in range(326)))
    def test_shape_does_not_rebuild_stock(self):
        self.assertEqual(self.a.anchor_digest,self.repeat.anchor_digest);self.assertNotEqual(self.a.shape_key(ShapeState()),self.a.shape_key(self.s))
    def test_roundtrip(self):
        p=np.array([a.point for a in self.a.anchors]);q=self.s.forward(p,48);self.assertLess(np.max(np.abs(self.s.inverse(q,48)-p)),1e-12)
        self.assertGreater(np.max(np.linalg.norm(q-p,axis=-1)),2)
    def test_normals(self):
        p=np.array([a.point for a in self.a.anchors]);n=np.array([a.normal for a in self.a.anchors]);u=np.array([a.long_axis for a in self.a.anchors]);v=np.array([a.side_axis for a in self.a.anchors]);nn=self.s.normal(p,n,48)
        for t in (u,v):
            dp=(self.s.forward(p+1e-5*t,48)-self.s.forward(p-1e-5*t,48))/2e-5
            self.assertLess(np.max(np.abs(np.sum(nn*dp,axis=-1))),1e-8)
    def test_immutable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError): self.a.stock_key='oops'
    def test_bad_count(self):
        for count in (0,True,501):
            with self.assertRaises(ValueError): make_stock(self.ctx,count)
    def test_bad_map(self):
        with self.assertRaises(ValueError):ShapeState(-1,0,1)
if __name__=='__main__':unittest.main(verbosity=2)
