"""Scientific evidence gates for M2b shared GN modules."""
import json
import unittest
from pathlib import Path
from fruit_morphometry import load_catalog
from fruit_platform import make_context, standard_registry
from fruit_biocomponents import (tissue_contract, measured_cell_populations,
   vascular_contract, require_measured_vessel_diameter, MissingBiologicalEvidence,
   anatomical_components)

CAT=load_catalog(str(Path(__file__).resolve().parents[1]/'data'/'morphometry'/'measurements-v1.json'))
R=standard_registry()

def p(c,seed=12):return R.plan(make_context(CAT,c,c.lower().replace(' ','_'),seed=seed))

class BioComponentsTests(unittest.TestCase):
    def test_tissues_kiwi_measured_both(self):
        self.assertEqual(tissue_contract(p('Sweet Gold')).boundaries_mm,(3.6,14.,21.3))
        self.assertEqual(tissue_contract(p('Jecy Gold')).boundaries_mm,(3.,11.6,20.7))
    def test_strawberry_never_invents_pith_width(self):
        t=tissue_contract(p('Camarosa'))
        self.assertEqual(t.boundaries_mm,())
        self.assertEqual(t.status,'QUALITATIVE_ONLY')
    def test_cell_means_sweet(self):
        c=measured_cell_populations(p('Sweet Gold'))
        self.assertEqual([round(x.mean_diameter_mm,4) for x in c],[.0473,.0959,.0514,.1646])
        self.assertTrue(all(x.source_row.startswith('R') for x in c))
    def test_cell_means_jecy(self):
        c=measured_cell_populations(p('Jecy Gold'))
        self.assertEqual([round(x.mean_diameter_mm,4) for x in c],[.0474,.0855,.0653,.1815])
    def test_zero_camarosa_cells(self):
        self.assertEqual(measured_cell_populations(p('Camarosa')),())
    def test_samples_fit_volume(self):
        for cultivar in ('Sweet Gold','Jecy Gold'):
            for c in measured_cell_populations(p(cultivar)):
                self.assertLessEqual(c.occupied_span_mm,c.sample_cube_side_mm+1e-9)
                self.assertEqual(c.sample_count_xyz[0]**3,c.points_count)
    def test_schematic_spacing_not_scientific(self):
        for c in measured_cell_populations(p('Sweet Gold')):
            self.assertTrue(c.arrangement_status.startswith('ILLUSTRATIVE'))
            self.assertGreater(c.artist_spacing_factor,1)
    def test_invalid_art_space_rejected(self):
        with self.assertRaises(ValueError):measured_cell_populations(p('Sweet Gold'),artist_spacing_factor=.8)
    def test_unknown_vascular_diameter_never_filled(self):
        with self.assertRaises(MissingBiologicalEvidence):
            require_measured_vessel_diameter(vascular_contract(p('Camarosa')))
    def test_strawberry_vessel_topology_no_mm(self):
        v=vascular_contract(p('Camarosa'))
        self.assertEqual(v.evidence_status,'QUALITATIVE_TOPOLOGY_ONLY')
        self.assertTrue(any(r=='branches_to' for a,b,r in v.typed_edges))
        self.assertIsNone(v.diameter_mm)
    def test_kiwi_cross_taxon_vascular_nonrenderable(self):
        for c in ('Sweet Gold','Jecy Gold'):
            v=vascular_contract(p(c))
            self.assertEqual(v.evidence_status,'CROSS_TAXON_REF_DO_NOT_GENERATE')
            self.assertEqual(v.typed_edges,())
            self.assertNotEqual(v.taxon,v.source_taxon)
    def test_two_instances_no_contamination(self):
        a=p('Camarosa',seed=1);b=p('Camarosa',seed=2)
        self.assertEqual(tissue_contract(a).status,tissue_contract(b).status)
        self.assertNotEqual(a.digest(),b.digest())
    def test_component_serialization(self):
        for cultivar in ('Camarosa','Sweet Gold','Jecy Gold'):
            z=anatomical_components(p(cultivar))
            self.assertTrue(json.loads(json.dumps(z))['warnings'])

if __name__=='__main__':unittest.main()