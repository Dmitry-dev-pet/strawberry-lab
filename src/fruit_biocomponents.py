"""Evidence-aware contracts for shared Fruit Engine anatomical components (M2b).

This is intentionally Blender-independent. It does NOT infer natural cell packing,
vascular diameters or unmeasured ripe strawberry cortex cell sizes.

Sources: exact primary numeric tables in measurements-v1.json (ARIZA2011,
JEON2024) and qualitative organ graph S02 (Darrow 1966).
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from fruit_platform import FruitPlan, PlatformError


class MissingBiologicalEvidence(PlatformError):
    """A requested physical trait is absent in the matching original source."""


@dataclass(frozen=True)
class TissueFieldContract:
    instance_id: str
    taxon: str
    cultivar: str
    status: str  # MEASURED_RADIAL_WIDTHS | QUALITATIVE_ONLY
    boundaries_mm: tuple[float, ...]
    source_rows: tuple[str, ...]
    tissue_labels: tuple[str, ...]


@dataclass(frozen=True)
class CellPopulationContract:
    instance_id: str
    region: str
    mean_diameter_mm: float
    source_row: str
    sample_count_xyz: tuple[int, int, int]
    artist_spacing_factor: float
    sample_cube_side_mm: float
    arrangement_status: str = 'ILLUSTRATIVE_3D_LATTICE_NOT_HISTOLOGY'

    @property
    def points_count(self) -> int:
        x, y, z = self.sample_count_xyz
        return x * y * z

    @property
    def occupied_span_mm(self) -> float:
        n = max(self.sample_count_xyz)
        return (n - 1) * self.mean_diameter_mm * self.artist_spacing_factor + self.mean_diameter_mm


@dataclass(frozen=True)
class VesselTopologyContract:
    instance_id: str
    taxon: str
    source_taxon: str
    source_id: str
    evidence_status: str
    typed_edges: tuple[tuple[str, str, str], ...]
    diameter_mm: None = None
    placement_status: str = 'UNMEASURED_GEOMETRY'


def tissue_contract(plan: FruitPlan) -> TissueFieldContract:
    s = plan.context.specimen
    if s.taxon.startswith('Actinidia'):
        b = tuple(s.region_boundaries_mm)
        if len(b) != 3 or not (0 < b[0] < b[1] < b[2]):
            raise MissingBiologicalEvidence('Kiwi requires 3 measured radial limits')
        r = tuple(s.radial_region_widths[k].observation_id for k in
                  ('core', 'inner_pericarp', 'outer_pericarp'))
        if any(not q for q in r):
            raise MissingBiologicalEvidence('Missing tissue provenance')
        return TissueFieldContract(plan.context.instance_id, s.taxon, s.cultivar,
                                   'MEASURED_RADIAL_WIDTHS', b, r,
                                   ('core','inner_pericarp','outer_pericarp'))
    if s.taxon.startswith('Fragaria'):
        return TissueFieldContract(plan.context.instance_id, s.taxon, s.cultivar,
                                   'QUALITATIVE_ONLY', (), ('S02',),
                                   ('receptacle_unknown_subregion',))
    raise MissingBiologicalEvidence('No evidence for tissue field')


def measured_cell_populations(plan: FruitPlan, *, sample_cube_side_mm: float=0.63,
                              artist_spacing_factor: float=1.10) -> tuple[CellPopulationContract,...]:
    """Build measured-diameter samples, never invent an unknown population.

    Geometry is a purely illustrative 3D lattice of round proxy cells.
    Only the individual mean DIAMETER is measured. A cell count for the actual
    organ or physical 3-D density is NOT inferred from the lattice.
    """
    s = plan.context.specimen
    if not s.cell_diameters:
        return ()   # e.g. ripe Camarosa, published numeric data insufficient
    if not (0.25 <= sample_cube_side_mm <= 2.0):
        raise ValueError('Diagnostic sample should be small, 0.25–2 mm')
    if not (1.0 <= artist_spacing_factor <= 1.3):
        raise ValueError('Artist spacing must be explicit in [1,1.3]')
    regions=('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large')
    if set(s.cell_diameters)!=set(regions):
        raise MissingBiologicalEvidence('Not all four original tissue cell means exist')
    out=[]
    for region in regions:
        m = s.cell_diameters[region]
        d = m.mm
        if not (math.isfinite(d) and 0 < d < sample_cube_side_mm):
            raise MissingBiologicalEvidence(f'Invalid measured cell diameter for {region}')
        # Fit source-scale sphere proxies into the stated diagnostic cube.
        # Lattice spacing is ARTIST convention and not a measured density.
        n = max(1, 1+int((sample_cube_side_mm-d)/(d*artist_spacing_factor)))
        if n**3 > 16000:
            raise ValueError('Too many diagnostic proxy cells')
        c=CellPopulationContract(plan.context.instance_id,region,d,m.observation_id,
                                 (n,n,n),artist_spacing_factor,sample_cube_side_mm)
        if c.occupied_span_mm > sample_cube_side_mm+1e-10:
            raise AssertionError('Cell sample overshoots physical cube')
        out.append(c)
    return tuple(out)


def vascular_contract(plan:FruitPlan) -> VesselTopologyContract:
    ve=plan.vascular_evidence
    if ve.scope == 'SAME_TAXON_QUALITATIVE':
        if ve.graph is None or ve.source_taxon != plan.context.specimen.taxon:
            raise MissingBiologicalEvidence('Same-taxon vascular graph mismatch')
        ve.graph.check()
        edges=tuple((e.source,e.target,e.relation) for e in ve.graph.connections
                   if e.relation in ('supplies','branches_to'))
        if not edges:
            raise MissingBiologicalEvidence('No source-backed graph edges')
        return VesselTopologyContract(plan.context.instance_id,
                     plan.context.specimen.taxon,ve.source_taxon,
                     ve.source_id,'QUALITATIVE_TOPOLOGY_ONLY',edges)
    if ve.scope == 'CROSS_TAXON_REFERENCE_ONLY':
        # A. deliciosa example cannot be rendered as A. chinensis measured vessels.
        return VesselTopologyContract(plan.context.instance_id,
                         plan.context.specimen.taxon,ve.source_taxon,
                         ve.source_id,'CROSS_TAXON_REF_DO_NOT_GENERATE',())
    raise MissingBiologicalEvidence('Unsupported or missing vascular evidence status')


def require_measured_vessel_diameter(contract:VesselTopologyContract)->float:
    if contract.diameter_mm is None:
        raise MissingBiologicalEvidence('No matching primary vessel diameter in dataset')
    return contract.diameter_mm


def anatomical_components(plan:FruitPlan)->dict:
    t=tissue_contract(plan)
    cells=measured_cell_populations(plan)
    vein=vascular_contract(plan)
    return {'instance':plan.context.instance_id,
            'tissue':vars(t),
            'cells':[vars(c)|{'points_count':c.points_count,'occupied_span_mm':c.occupied_span_mm}
                     for c in cells],
            'vessels':vars(vein),
            'warnings':['CELL_PACKING_IS_ARTIST_DIAGNOSTIC',
                        'VESSEL_DIAMETER_UNMEASURED_NOT_GENERATED_AS_PHYSICAL_VESSEL',
                        'CUT_REMAINS_SEPARATE_OPERATION']}