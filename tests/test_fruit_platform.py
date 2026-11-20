"""M2a architecture tests: compositional and evidence-safe fruit instances."""
import dataclasses
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fruit_morphometry import load_catalog
from fruit_platform import (standard_registry, make_context, FruitRegistry,
    StrawberryReceptacleAdapter, KiwiLocularBerryAdapter, FruitContext,
    PlatformError, plans_digest, OrganRecipe)
from fruit_engine import get_specimen

DATA=load_catalog(ROOT/'measurements-v1.json')


class FruitPlatformTests(unittest.TestCase):
    def setUp(self):
        self.registry=standard_registry()
        self.cam=self.registry.plan(make_context(DATA,'Camarosa','cam',seed=3))
        self.sweet=self.registry.plan(make_context(DATA,'Sweet Gold','sweet',seed=9))
        self.jecy=self.registry.plan(make_context(DATA,'Jecy Gold','jecy',seed=9))

    def test_no_nested_mutable_specimen_state(self):
        with self.assertRaises(TypeError):
            self.sweet.context.specimen.radial_region_widths['core'] = None
        with self.assertRaises(TypeError):
            self.sweet.context.specimen.cell_diameters['core'] = None
        self.assertEqual(self.sweet.context.specimen.region_boundaries_mm,(3.6,14.0,21.3))

    def test_two_fruit_taxa_registered(self):
        self.assertEqual(len(self.registry.available_taxa()),2)
        self.assertIn('Fragaria × ananassa',self.registry.available_taxa())

    def test_registry_rejects_duplicate_taxon(self):
        with self.assertRaises(PlatformError):
            FruitRegistry((StrawberryReceptacleAdapter(),StrawberryReceptacleAdapter()))

    def test_immutable_instance_context(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.cam.context.seed=17
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.cam.context.instance_id='bad'

    def test_immutable_organ_recipe_parameter_view(self):
        p=self.cam.organs[0].parameters()
        with self.assertRaises(TypeError):p['height_mm']=200

    def test_strawberry_external_achene_not_kiwi_seed(self):
        self.assertEqual(self.cam.reproductive_topology,'external_individual_achenes')
        self.assertEqual([o.emitter for o in self.cam.renderable_parts],
            ['schematic_receptacle_envelope','schematic_surface_marker_scatter'])
        self.assertIn('R0017',self.cam.organs[1].evidence_rows)
        self.assertEqual(self.cam.organs[1].parameters()['marker_count'],326)

    def test_strawberry_dimensions_exact_primary_table(self):
        self.assertEqual(self.cam.organs[0].parameters()['height_mm'],48)
        self.assertEqual(self.cam.organs[0].parameters()['width_mm'],32.5)
        self.assertEqual(self.cam.organs[0].evidence_rows,('R0015','R0016'))

    def test_kiwi_radii_control_profiles_are_distinct(self):
        a=self.sweet.organs[0].parameters();b=self.jecy.organs[0].parameters()
        self.assertEqual(tuple(a.values()),(3.6,14.0,21.3))
        self.assertEqual(tuple(b.values()),(3.0,11.6,20.7))
        self.assertNotEqual(self.sweet.digest(),self.jecy.digest())

    def test_cell_sizes_from_matching_tissue_and_cultivar(self):
        s=self.sweet.organs[1]
        self.assertAlmostEqual(s.parameters()['core_diameter_mm'],0.0473)
        self.assertAlmostEqual(s.parameters()['outer_pericarp_large_diameter_mm'],0.1646)
        self.assertIn('R0174',s.evidence_rows)

    def test_kiwi_seeds_are_not_fabricated(self):
        for p in (self.sweet,self.jecy):
            self.assertTrue(all('seed' not in (o.emitter or '') for o in p.renderable_parts))
            self.assertEqual(next(o for o in p.organs if o.organ_id=='internal_seeds').emitter,None)
            self.assertTrue(any('UNMEASURED' in o.evidence for o in p.organs))

    def test_strawberry_qualitative_vascular_graph(self):
        v=self.cam.vascular_evidence
        self.assertEqual(v.scope,'SAME_TAXON_QUALITATIVE')
        self.assertEqual(v.source_taxon,'Fragaria × ananassa')
        self.assertGreater(len(v.graph.connections),4)
        self.assertFalse(self.cam.as_dict()['vascular']['calibrated_diameters'])

    def test_no_cross_taxon_kiwi_vascular_inference(self):
        v=self.sweet.vascular_evidence
        self.assertEqual(v.scope,'CROSS_TAXON_REFERENCE_ONLY')
        self.assertEqual(v.source_taxon,'Actinidia deliciosa')
        self.assertIsNone(v.graph)
        self.assertEqual(self.sweet.as_dict()['vascular']['connection_count'],0)

    def test_unsourced_organs_not_rendered(self):
        for p in (self.cam,self.sweet,self.jecy):
            self.assertTrue(all(o.evidence != 'UNMEASURED_ONLY' for o in p.renderable_parts))
            self.assertTrue(all(o.emitter is None for o in p.organs if o.evidence == 'UNMEASURED_ONLY'))

    def test_no_anatomical_cut_module(self):
        for p in (self.cam,self.sweet):
            self.assertTrue(all('cut' not in o.role for o in p.organs))
            self.assertIn('NOT_ANATOMY',p.as_dict()['operations']['cut'])

    def test_changes_to_one_seed_do_not_affect_another(self):
        base=self.cam.digest();other=self.registry.plan(make_context(DATA,'Camarosa','cam',seed=177))
        self.assertNotEqual(other.digest(),base)
        self.assertEqual(base,self.registry.plan(make_context(DATA,'Camarosa','cam',seed=3)).digest())
        self.assertEqual(self.sweet.digest(),self.registry.plan(make_context(DATA,'Sweet Gold','sweet',seed=9)).digest())

    def test_build_order_does_not_change_manifest(self):
        self.assertEqual(plans_digest((self.cam,self.sweet,self.jecy)),
                         plans_digest((self.jecy,self.cam,self.sweet)))

    def test_duplicate_instance_id_rejected(self):
        a=self.cam
        b=self.registry.plan(make_context(DATA,'Sweet Gold','cam',seed=2))
        with self.assertRaises(PlatformError):plans_digest((a,b))

    def test_bad_adapter_origin_rejected(self):
        with self.assertRaises(PlatformError):KiwiLocularBerryAdapter().make_plan(self.cam.context)
        with self.assertRaises(PlatformError):StrawberryReceptacleAdapter().make_plan(self.sweet.context)

    def test_bad_recipe_rejected(self):
        with self.assertRaises(PlatformError):
            OrganRecipe('test','test','any',(('a',1),('a',2)),'MEASURED_EXTENT',('R0',),'bad')

    def test_invalid_seed_and_mode(self):
        with self.assertRaises(PlatformError):make_context(DATA,'Camarosa','p',seed=True)
        with self.assertRaises(PlatformError):make_context(DATA,'Camarosa','p',detail='exact')

    def test_missing_specimen_does_not_fallback(self):
        with self.assertRaises(ValueError):make_context(DATA,'Hayward','kiwi')

    def test_recipe_hash_stable_and_provenance_visible(self):
        self.assertEqual(len(self.cam.digest()),64)
        self.assertIn('R0015',self.cam.as_dict()['organs'][0]['rows'])
        self.assertEqual(self.cam.as_dict()['mm_per_BLENDER_UNIT'],1.)

    def test_unrecognized_adapter_rejected(self):
        with self.assertRaises(PlatformError):FruitRegistry(())


if __name__=='__main__':unittest.main()