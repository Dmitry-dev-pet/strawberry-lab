"""Verifies derived dimensions and that scientific unknowns remain unknown."""
import unittest,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fruit_engine import get_specimen,provenance_dict,EvidenceError,MM_PER_BLENDER_UNIT
from fe_geometry import strawberry_surface_mesh, achene_anchor_positions,kiwi_region_rings

DATA=json.loads((ROOT/'data'/'morphometry'/'measurements-v1.json').read_text())

class EvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=get_specimen(DATA,'Camarosa');cls.s=get_specimen(DATA,'Sweet Gold');cls.j=get_specimen(DATA,'Jecy Gold')
    def test_real_world_scale(self):self.assertEqual(MM_PER_BLENDER_UNIT,1.0)
    def test_exact_source_context(self):
        self.assertEqual((self.c.source_id,self.c.taxon,self.c.stage,self.c.treatment),
        ('ARIZA2011','Fragaria × ananassa','field_harvest','fruit_shape=well_formed'))
    def test_camarosa_mm_dims(self):
        self.assertEqual((self.c.fruit_height.mm,self.c.fruit_width.mm),(48.,32.5))
        self.assertEqual((self.c.fruit_height.observation_id,self.c.fruit_width.observation_id),('R0015','R0016'))
    def test_achenes_source_vs_drawing(self):
        self.assertEqual(self.c.achene_mean,325.6)
        self.assertEqual(self.c.display_achene_count,326)
        self.assertEqual(self.c.achene_mean_id,'R0017')
    def test_kiwi_radial_region_bounds(self):
        self.assertEqual(self.s.region_boundaries_mm,(3.6,14.0,21.3))
        self.assertEqual(self.j.region_boundaries_mm,(3.0,11.6,20.7))
    def test_cells_only_in_kiwi(self):
        self.assertEqual(tuple(self.s.cell_diameters),('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large'))
        self.assertAlmostEqual(self.s.cell_diameters['outer_pericarp_large'].mm,.1646)
        self.assertAlmostEqual(self.j.cell_diameters['inner_pericarp'].mm,.0855)
        self.assertEqual(len(self.c.cell_diameters),0)
    def test_no_invented_kiwi_height_or_seeds(self):
        for p in (self.s,self.j):
            self.assertIsNone(p.fruit_height)
            self.assertIsNone(p.display_achene_count)
            self.assertEqual(p.reproductive_plan,'internal_locular_seeds')
    def test_distinct_developmental_origins(self):
        self.assertNotEqual(self.c.developmental_origin,self.s.developmental_origin)
    def test_no_cross_cultivar_fallback(self):
        for bad in ('Hayward','Kiwi','generic','Cambridge Vigour','Flair'):
            with self.assertRaises(EvidenceError):get_specimen(DATA,bad)
    def test_missing_measurement_is_explicit(self):
        self.assertIn('vascular_diameter',provenance_dict(self.s)['unmeasured'])
        self.assertIsNone(provenance_dict(self.s)['height'])
    def test_strict_source_region_total(self):
        copy=json.loads(json.dumps(DATA))
        for r in copy['observations']:
            if r['id']=='R0112':r['value']=7.4
        with self.assertRaises(EvidenceError):get_specimen(copy,'Sweet Gold')
    def test_strawberry_exterior_dimensions(self):
        verts,faces=strawberry_surface_mesh(height_mm=48.,width_mm=32.5,rings=48,sectors=64)
        self.assertEqual((min(p[2] for p in verts),max(p[2] for p in verts)),(-24.,24.))
        self.assertAlmostEqual(max((p[0]**2+p[1]**2)**.5 for p in verts),16.25,delta=.015)
        self.assertGreater(len(faces),2000)
    def test_achene_anchor_count_and_bounds(self):
        coords=achene_anchor_positions(height_mm=48,width_mm=32.5,count=326)
        self.assertEqual(len(coords),326)
        self.assertTrue(all(-24<z<24 and math.hypot(x,y)<=16.25+.001 for x,y,z in coords))
    def test_kiwi_annulus_true_radius(self):
        for b in (self.s.region_boundaries_mm,self.j.region_boundaries_mm):
            verts,faces,regions=kiwi_region_rings(b,sectors=60)
            self.assertEqual(len(faces),180)
            self.assertEqual([regions.count(i) for i in range(3)],[60,60,60])
            self.assertAlmostEqual(max((x*x+z*z)**.5 for x,_,z in verts),b[-1])
    def test_not_interpreting_density_as_cell_count(self):
        self.assertEqual(self.s.cell_diameters['core'].unit_original,'µm')
        self.assertEqual(self.s.cell_diameters['core'].observation_id,'R0174')

if __name__=='__main__':unittest.main()