from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from fruit_engine_anatomy import strawberry_anatomy,kiwi_anatomy,export_anatomy,Anatomy,Organ,Connection

class AnatomyTests(unittest.TestCase):
 def test_strawberry_achemes_are_external_fruits(self):
  a=strawberry_anatomy();self.assertIn('achene',[o.organ_class for o in a.organs]);self.assertNotIn('locule',[o.organ_class for o in a.organs])
 def test_kiwi_internal_seed_topology(self):
  a=kiwi_anatomy();c={o.organ_class for o in a.organs};self.assertIn('locule',c);self.assertIn('internal_seed',c);self.assertNotIn('achene',c)
 def test_two_graphs_have_different_vascular_paths(self):
  s=strawberry_anatomy();k=kiwi_anatomy();self.assertNotEqual({(e.source,e.target) for e in s.connections},{(e.source,e.target) for e in k.connections})
 def test_all_edges_cite_figures(self):
  for a in (strawberry_anatomy(),kiwi_anatomy()):
   self.assertTrue(all(e.source_id and 'Fig' in e.figure and e.dimensions_status=='UNMEASURED' for e in a.connections))
 def test_dangling_relation_rejected(self):
  s=strawberry_anatomy();a=Anatomy(s.taxon,s.fruit_type,s.organs,s.connections+(Connection('unknown','pith','supplies','S02','Darrow Fig 1'),))
  with self.assertRaises(ValueError):a.check()
 def test_missing_kiwi_organ_rejected(self):
  k=kiwi_anatomy();a=Anatomy(k.taxon,k.fruit_type,tuple(o for o in k.organs if o.organ_class!='locule'),tuple(c for c in k.connections if c.source!='locules' and c.target!='locules'))
  with self.assertRaises(ValueError):a.check()
 def test_no_numeric_vascular_diameter_in_graph(self):
  for a in (strawberry_anatomy(),kiwi_anatomy()):
   self.assertTrue(all('diameter' not in vars(c) for c in a.connections))
   self.assertEqual(export_anatomy(a)['source_quality'],'QUALITATIVE_TOPOLOGY')

if __name__=='__main__':unittest.main()