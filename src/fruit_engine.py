"""Evidence-bound minimal shared organ/tissue engine for Strawberry Lab.

This file deliberately separates measurements from shape/topology assumptions.
One Blender unit is explicitly one millimetre (scene.scale_length = .001).
No unmeasured vascular dimensions, fruit height for kiwi, or ripe strawberry
cell sizes are silently invented. Independent code, no Frucht node trees.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from math import isclose
from fruit_morphometry import select_observations, convert_length, EvidenceError

MM_PER_BLENDER_UNIT = 1.0
SOURCE_CONTEXT = {
    "Camarosa": ("ARIZA2011", "Fragaria × ananassa", "field_harvest", "fruit_shape=well_formed"),
    "Sweet Gold": ("JEON2024", "Actinidia chinensis var. chinensis", "harvest_180_DAA", "BenefitsPZ_sprays=0"),
    "Jecy Gold": ("JEON2024", "Actinidia chinensis var. chinensis", "harvest_180_DAA", "BenefitsPZ_sprays=0"),
}

@dataclass(frozen=True)
class Measured:
    mm: float
    observation_id: str
    unit_original: str
    value_original: float
    uncertainty_original: float | None
    source_locator: str

@dataclass(frozen=True)
class Specimen:
    cultivar: str
    taxon: str
    source_id: str
    stage: str
    treatment: str
    developmental_origin: str
    reproductive_plan: str
    fruit_height: Measured | None
    fruit_width: Measured | None
    achene_mean: float | None
    achene_mean_id: str | None
    radial_region_widths: Mapping[str, Measured]
    cell_diameters: Mapping[str, Measured]
    classification: str = "measured_values_plus_schematic_topology"

    @property
    def physical_radius(self) -> float | None:
        if self.fruit_width is not None:
            return self.fruit_width.mm / 2
        if self.radial_region_widths:
            return sum(q.mm for q in self.radial_region_widths.values())
        return None

    @property
    def display_achene_count(self) -> int | None:
        """Rounded mean for deterministic DRAWING, not actual observed fruit count."""
        return round(self.achene_mean) if self.achene_mean is not None else None

    @property
    def region_boundaries_mm(self) -> tuple[float, ...]:
        if not self.radial_region_widths:
            return ()
        if set(self.radial_region_widths) != {'core', 'inner_pericarp', 'outer_pericarp'}:
            raise EvidenceError('Kiwi radial tissue regions must be complete')
        core = self.radial_region_widths['core'].mm
        inner = self.radial_region_widths['inner_pericarp'].mm
        outer = self.radial_region_widths['outer_pericarp'].mm
        return (core, core + inner, core + inner + outer)


def get_specimen(catalog: dict, cultivar: str) -> Specimen:
    if cultivar not in SOURCE_CONTEXT:
        raise EvidenceError(f'No exact-context calibrated profile for {cultivar!r}')
    source_id, taxon, stage, treatment = SOURCE_CONTEXT[cultivar]
    rows = select_observations(catalog, source_id=source_id,taxon=taxon,cultivar=cultivar,
                               stage=stage,treatment=treatment)
    if not rows:
        raise EvidenceError('Requested exact scientific study has no matching rows')

    def take(tissue: str, metric: str, unit: str | None=None) -> tuple[dict,Measured]:
        matches=[r for r in rows if r['tissue']==tissue and r['metric']==metric]
        if len(matches)!=1:
            raise EvidenceError(f'Expected exactly one original value for {tissue}/{metric}, got {len(matches)}')
        row=matches[0]
        if unit is not None and row['unit'] != unit:
            raise EvidenceError(f'Unexpected source unit for {row["id"]}: {row["unit"]}')
        length=convert_length(row['value'],row['unit'],'mm')
        return row, Measured(mm=length,observation_id=row['id'], unit_original=row['unit'],
           value_original=row['value'],uncertainty_original=row['uncertainty_value'],
           source_locator=row['source_locator'])

    if cultivar=='Camarosa':
        h=take('whole','fruit_length','cm')[1]
        w=take('whole','fruit_width','cm')[1]
        achenes=[r for r in rows if r['tissue']=='surface' and r['metric']=='achene_total_per_fruit']
        if len(achenes)!=1 or achenes[0]['unit']!='count':
            raise EvidenceError('Achene count is missing or ambiguous')
        return Specimen(cultivar,taxon,source_id,stage,treatment,'expanded_floral_receptacle',
            'external_individual_achenes',h,w,achenes[0]['value'],achenes[0]['id'],{}, {})
    regions={k:take(k,'radial_tissue_width','mm')[1]
             for k in ('core','inner_pericarp','outer_pericarp')}
    total=take('half_radial_total','radial_tissue_width','mm')[1]
    if not isclose(sum(v.mm for v in regions.values()),total.mm,abs_tol=1e-8):
        raise EvidenceError('Incorrect physical region thickness totals in source')
    cell_diameters={k:take(k,'cell_mean_diameter','µm')[1]
        for k in ('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large')}
    return Specimen(cultivar,taxon,source_id,stage,treatment,'multicarpellate_ovary_pericarp',
         'internal_locular_seeds',None,None,None,None,regions,cell_diameters)


def provenance_dict(s: Specimen) -> dict:
    def quantity(v: Measured | None):
        return None if v is None else {"mm":v.mm,"row":v.observation_id,"source_value":v.value_original,
                                        "source_unit":v.unit_original,"SE_source":v.uncertainty_original}
    return {"cultivar":s.cultivar,"taxon":s.taxon,"source_id":s.source_id,
        "stage":s.stage,"treatment":s.treatment,"origin":s.developmental_origin,
        "reproduction":s.reproductive_plan,"height":quantity(s.fruit_height),
        "width":quantity(s.fruit_width),"achene_mean":s.achene_mean,
        "achene_display_rounding":s.display_achene_count,"achene_row":s.achene_mean_id,
        "region_widths":{k:quantity(v) for k,v in s.radial_region_widths.items()},
        "region_boundaries_mm":s.region_boundaries_mm,
        "cell_diameters":{k:quantity(v) for k,v in s.cell_diameters.items()},
        "bu_per_mm":1.0/MM_PER_BLENDER_UNIT,"unmeasured":["vascular_diameter","intercellular_porosity",
                 "achene_pit_depth","epidermis_thickness","kiwi_ovule_locations",
                 "ripe_strawberry_cortex_cell_size"]}