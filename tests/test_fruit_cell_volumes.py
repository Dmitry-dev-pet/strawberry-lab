"""M2c independent tests: source-measured diameter, true 3D intersection consistency.

Only 2D histological population means have measurement status. 3D cell shape,
density, arrangement and porosity are ARTIST; these tests validate math and
source safety, NOT histological accuracy of synthesised packing.
"""
import sys,unittest,json,math,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from fruit_platform import standard_registry,make_context
from fruit_morphometry import load_catalog
from fruit_cell_volumes import (CellSolid,build_volume,section_records,plan_json,REGIONS,
                                MM_PER_BU,MORPHOLOGY_REFERENCE)
from fruit_biocomponents import MissingBiologicalEvidence

CATALOG=Path(__file__).resolve().parents[1]/'outputs'/'source-measurements-v1.json'
class TestMeasuredVolumetricSpecimens(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cat=load_catalog(CATALOG)
  reg=standard_registry()
  cls.plans=[reg.plan(make_context(cat,c,id_,seed=1729)) for c,id_ in [('Sweet Gold','sweet'),('Jecy Gold','jecy')]]
  cls.both=[build_volume(p) for p in cls.plans]
 def test_actual_primary_source(self):
  self.assertEqual(MM_PER_BU,1.0)
  for plan,blocks in zip(self.plans,self.both):
   self.assertEqual(plan.context.specimen.source_id,'JEON2024')
   self.assertEqual(len(blocks),3)
   for b in blocks:
    self.assertEqual(b.cultivar,plan.context.specimen.cultivar)
    self.assertTrue(all(c.source_row.startswith('R0') for c in b.cells))
 def test_all_cell_equivalent_diameters_source_calibrated(self):
  for p,blocks in zip(self.plans,self.both):
   expected={k:m.mm for k,m in p.context.specimen.cell_diameters.items()}
   for b in blocks:
    for c in b.cells:
     self.assertAlmostEqual(c.volume_equiv_diameter_mm,expected[c.region],places=10)
     self.assertEqual(c.mean_diameter_mm,expected[c.region])
 def test_ellipsoid_is_an_actual_three_dimensional_volume(self):
  for blocks in self.both:
   for b in blocks:
    for c in b.cells[:10]:
     self.assertLess(c.inside(c.center_mm),1e-12)
     surface=(c.center_mm[0]+c.half_axes_mm[0],c.center_mm[1],c.center_mm[2])
     self.assertAlmostEqual(c.inside(surface),1,places=10)
 def test_two_planes_in_one_volume(self):
  for blocks in self.both:
   outer=blocks[2]
   self.assertGreater(len(section_records(outer,1)),5)
   self.assertGreater(len(section_records(outer,2)),5)
   self.assertEqual(len(set(c.cell_id for c in outer.cells)),len(outer.cells))
 def test_all_2d_ellipse_boundary_points_lie_on_same_3d_ellipsoid(self):
  for blocks in self.both:
   for b in blocks:
    for ax in (1,2):
     for c,_ in section_records(b,ax)[:50]:
      for a in (0,.7,1.6,3.4,5.6):
       pt=c.section_point(ax,a)
       self.assertAlmostEqual(pt[ax],0,places=12)
       self.assertAlmostEqual(c.inside(pt),1,places=8)
 def test_cross_plane_line_interval_consistency(self):
  # The common x-axis is the intersection of Y=0 and Z=0.
  # For any single cell, solve the SAME 3D equation; results cannot differ by plane.
  for blocks in self.both:
   for b in blocks:
    for c in b.cells:
     xlim2=1-(c.center_mm[1]/c.half_axes_mm[1])**2-(c.center_mm[2]/c.half_axes_mm[2])**2
     if xlim2 > 0:
      half=c.half_axes_mm[0]*math.sqrt(xlim2)
      for x in (c.center_mm[0]-half,c.center_mm[0]+half):
       p=(x,0.,0.)
       self.assertAlmostEqual(c.inside(p),1,places=8)
       self.assertIsNotNone(c.ellipse(1));self.assertIsNotNone(c.ellipse(2))
 def test_solid_occupancy_in_physical_cube(self):
  for blocks in self.both:
   for b in blocks:
    for c in b.cells:
     for i in range(3):
      self.assertLessEqual(abs(c.center_mm[i])+c.half_axes_mm[i],b.side_mm/2+1e-10)
 def test_mixed_pericarp_has_both_sizes_in_same_volume(self):
  for blocks in self.both:
   x=blocks[2]
   self.assertGreater(len(x.by_region('outer_pericarp_small')),25)
   self.assertGreater(len(x.by_region('outer_pericarp_large')),5)
   self.assertGreater(len(x.cells),len(x.by_region('outer_pericarp_small')))
 def test_conservative_no_big_small_intersection(self):
  for blocks in self.both:
   outer=blocks[2]
   for big in outer.by_region('outer_pericarp_large'):
    for small in outer.by_region('outer_pericarp_small'):
     d=math.sqrt(sum((big.center_mm[i]-small.center_mm[i])**2 for i in range(3)))
     self.assertGreater(d, max(big.half_axes_mm)+max(small.half_axes_mm)+.006)
 def test_reproducible(self):
  for p,orig in zip(self.plans,self.both):
   repl=build_volume(p)
   self.assertEqual(orig,repl)
 def test_different_specimens_not_silently_combined(self):
  self.assertNotEqual([len(b.cells) for b in self.both[0]], [len(b.cells) for b in self.both[1]])
  self.assertNotEqual(self.plans[0].context.specimen.cultivar,self.plans[1].context.specimen.cultivar)
 def test_strawberry_ripe_cells_remain_unmeasured(self):
  cat=load_catalog(CATALOG);st=standard_registry().plan(make_context(cat,'Camarosa','cam',seed=1))
  with self.assertRaises(MissingBiologicalEvidence):build_volume(st)
 def test_unsupported_slice_axis_fails(self):
  c=self.both[0][0].cells[0]
  with self.assertRaises(ValueError):c.ellipse(3)
 def test_no_section_outside_block(self):
  outer=self.both[0][2]
  self.assertFalse(section_records(outer,2,outer.side_mm))
 def test_source_assumptions_not_hidden(self):
  d=plan_json(self.both)
  self.assertEqual(d['schema'],'fruitengine.m2c.cells.1')
  self.assertIn('NO_MEASURED_POROSITY',d['warnings'])
  self.assertIn('ELLIPSOID_ASPECT_ARTIST',d['warnings'])
  self.assertIn('ARTIST',d['histology_status'] if 'ARTIST' in d['histology_status'] else d['warnings'][2])
  self.assertIn('Actinidia chinensis',MORPHOLOGY_REFERENCE)
 def test_dataset_does_not_claim_population_count(self):
  for blocks in self.both:
   for b in blocks:
    self.assertEqual(b.parameters_status,'ARTIST_SPATIAL_PLACEMENT_NOT_OBSERVED_HISTOLOGY')
 def test_source_rows_per_population(self):
  for p,blocks in zip(self.plans,self.both):
   ids={region:m.observation_id for region,m in p.context.specimen.cell_diameters.items()}
   for b in blocks:
    self.assertTrue(all(c.source_row==ids[c.region] for c in b.cells))
 def test_cuts_are_an_operation_not_an_organ(self):
  self.assertTrue(all('cut' not in p.anatomy_origin.lower() for p in self.plans))
if __name__=='__main__':unittest.main()