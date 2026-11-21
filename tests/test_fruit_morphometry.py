"""Source accuracy and non-pooling guards for the first measurement registry."""
import json, sys, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE/'src'))
from fruit_morphometry import load_catalog,select_observations,convert_length,evidence_profile,EvidenceError

class TestMorphometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load_catalog(HERE/'data'/'morphometry'/'measurements-v1.json')

    def test_205_rows_and_provenance(self):
        self.assertEqual(len(self.c['observations']),205)
        self.assertEqual({s: sum(r['source_id']==s for r in self.c['observations']) for s in self.c['sources']},
                         {'JAMES1974':13,'ARIZA2011':36,'CURRIE1997':60,'JEON2024':96})
        self.assertTrue(all(r['source_locator'] and r['value']>=0 for r in self.c['observations']))

    def test_james_exact_stage_b(self):
        r=select_observations(self.c,source_id='JAMES1974',taxon='Fragaria × ananassa',cultivar='Cambridge Vigour',stage='B',treatment='none',metric='cell_maximum_length')
        self.assertEqual(len(r),1)
        self.assertEqual((r[0]['value'],r[0]['uncertainty_value']), (59.9,5.3))

    def test_james_no_fake_ripe_cells(self):
        r=select_observations(self.c,source_id='JAMES1974',taxon='Fragaria × ananassa',cultivar='Cambridge Vigour',stage='E',treatment='none',metric='cell_maximum_length')
        self.assertEqual(r,[])

    def test_no_cross_species_fallback(self):
        with self.assertRaises(EvidenceError):
            evidence_profile(self.c,source_id='JEON2024',taxon='Actinidia deliciosa',cultivar='Sweet Gold',stage='harvest_180_DAA',treatment='BenefitsPZ_sprays=0')

    def test_no_treatment_fallback(self):
        with self.assertRaises(EvidenceError):
            evidence_profile(self.c,source_id='JEON2024',taxon='Actinidia chinensis var. chinensis',cultivar='Sweet Gold',stage='harvest_180_DAA',treatment='BenefitsPZ_sprays=999')

    def test_unverified_cultivar_not_preset(self):
        with self.assertRaises(EvidenceError):
            evidence_profile(self.c,source_id='CURRIE1997',taxon='Actinidia deliciosa',cultivar='cultivar_unverified_ch3',stage='150_DAFB',treatment='girdled_day=7;leaf_fruit_ratio=1')

    def test_control_sweet_gold_has_12_measurements(self):
        p=evidence_profile(self.c,source_id='JEON2024',taxon='Actinidia chinensis var. chinensis',cultivar='Sweet Gold',stage='harvest_180_DAA',treatment='BenefitsPZ_sprays=0')
        self.assertEqual(len(p['measurements']),12)
        inner=next(r for r in p['measurements'] if r['tissue']=='inner_pericarp' and r['metric']=='cell_mean_diameter')
        self.assertEqual((inner['value'],inner['uncertainty_value']), (95.9,0.8))

    def test_ariza_achenes_control_counts(self):
        p=evidence_profile(self.c,source_id='ARIZA2011',taxon='Fragaria × ananassa',cultivar='Camarosa',stage='field_harvest',treatment='fruit_shape=well_formed')
        self.assertEqual(len(p['measurements']),6)
        count=next(r for r in p['measurements'] if r['metric']=='achene_total_per_fruit')
        self.assertEqual(count['value'],325.6)

    def test_unit_conversion_only_for_length(self):
        self.assertAlmostEqual(convert_length(1.5, 'cm','mm'),15)
        self.assertAlmostEqual(convert_length(200,'µm','mm'),0.2)
        with self.assertRaises(EvidenceError):convert_length(4,'count','mm')

    def test_source_typo_is_not_guessed(self):
        rr=[r for r in self.c['observations'] if r['uncertainty_kind']=='SEM_unreadable_typo_in_source']
        self.assertEqual(len(rr),1)
        self.assertIsNone(rr[0]['uncertainty_value'])

if __name__=='__main__':unittest.main()