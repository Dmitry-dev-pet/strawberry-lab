import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(Path(__file__).parent)]
from fruit_platform import make_context,FruitContext
from fruit_morphometry import load_catalog
from controls import SharedDeformation
class ControlsTests(unittest.TestCase):
    def setUp(self):self.context=make_context(load_catalog(ROOT/'data/morphometry/measurements-v1.json'),'Camarosa','test')
    def test_original_context_and_determinism(self):
        a=SharedDeformation(self.context,.8,1.15);b=SharedDeformation(self.context,.8,1.15)
        self.assertIsInstance(a.context,FruitContext);self.assertEqual(a.digest(),b.digest())
        self.assertNotEqual(a.digest(),SharedDeformation(self.context,1.1,.9).digest())
    def test_inverse_and_incidence(self):
        a=SharedDeformation(self.context,.8,1.15)
        for p in [(1,2,3),(-.7,0,.2),(0,0,0)]:
            for x,y in zip(p,a.inverse(a.forward(p))):self.assertAlmostEqual(x,y)
        self.assertEqual(a.forward((0,0,0)),(0,0,0))
    def test_invalid_factors(self):
        for x in [True,float('nan'),float('inf'),.64,1.36,0,-1]:
            with self.assertRaises(ValueError):SharedDeformation(self.context,x,1)
    def test_seed_regeneration_is_rejected(self):
        from dataclasses import replace
        with self.assertRaises(ValueError):SharedDeformation(replace(self.context,seed=4),1,1)
    def test_units_and_unresolved_mapping(self):
        r=SharedDeformation(self.context,1,1).record()
        self.assertEqual(r['measured_specimen_reference_mm'],{'height':48.,'width':32.5})
        self.assertIn('UNRESOLVED',r['vascular_connection_constraint'])
if __name__=='__main__':unittest.main()
