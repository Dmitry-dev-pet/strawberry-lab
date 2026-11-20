"""Fruit Engine M2a: immutable fruit contexts and composable organ recipes.

The same explicit runtime can assemble strawberry or kiwi profiles without
switching process-global module variables. These are evidence-scoped recipes,
NOT complete histological reconstructions or a clone of Frucht's node tree.

The morphology and measurement sources are owned by fruit_engine.py and
fruit_engine_anatomy.py; Blender is deliberately not imported here.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol
from types import MappingProxyType
import hashlib
import json

from fruit_engine import Specimen, get_specimen, provenance_dict, MM_PER_BLENDER_UNIT
from fruit_engine_anatomy import Anatomy, strawberry_anatomy, kiwi_anatomy
from fruit_morphometry import EvidenceError


class PlatformError(ValueError):
    """Invalid fruit context, missing adapter or unsafe biological inference."""


@dataclass(frozen=True)
class FruitContext:
    """One independently owned fruit instance. No mutable globals or fallback."""
    instance_id: str
    specimen: Specimen
    seed: int = 1729
    detail: str = 'preview'

    def __post_init__(self):
        if not self.instance_id or self.instance_id.strip() != self.instance_id:
            raise PlatformError('Fruit instance needs a clean nonempty ID')
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise PlatformError('Fruit seed must be an integer')
        if self.detail not in ('preview', 'measured'):
            raise PlatformError('Unsupported detail mode; no implicit Exact fallback')
        # Specimen is frozen, but M1f returned plain dicts inside it. Freeze
        # them here so one caller cannot mutate another active fruit context.
        object.__setattr__(self, 'specimen', replace(self.specimen,
            radial_region_widths=MappingProxyType(dict(self.specimen.radial_region_widths)),
            cell_diameters=MappingProxyType(dict(self.specimen.cell_diameters))))


@dataclass(frozen=True)
class OrganRecipe:
    """A typed anatomical/rendering task; measured size != measured shape.

    Parameter values are immutable pairs to keep contexts isolated. Geometry
    emitters are stateless: all params, seed and source live in the recipe.
    """
    organ_id: str
    role: str
    emitter: str | None
    params: tuple[tuple[str, int | float], ...]
    evidence: str
    evidence_rows: tuple[str, ...]
    caveat: str

    def __post_init__(self):
        if not self.organ_id or not self.role or not self.evidence:
            raise PlatformError('Incomplete organ recipe')
        names = [key for key, _ in self.params]
        if len(names) != len(set(names)):
            raise PlatformError('Duplicate organ parameter name')
        if self.evidence == 'MEASURED_EXTENT' and not self.evidence_rows:
            raise PlatformError('Measured organ needs a source row')

    def parameters(self) -> MappingProxyType:
        return MappingProxyType(dict(self.params))


@dataclass(frozen=True)
class VascularEvidence:
    source_taxon: str
    scope: str
    source_id: str
    graph: Anatomy | None = None

    def __post_init__(self):
        if self.scope == 'SAME_TAXON_QUALITATIVE' and self.graph is None:
            raise PlatformError('Same-taxon anatomy must have actual graph')
        if self.graph is not None and self.graph.taxon != self.source_taxon:
            raise PlatformError('Vascular graph source taxon mismatch')


@dataclass(frozen=True)
class FruitPlan:
    context: FruitContext
    adapter_id: str
    anatomy_origin: str
    reproductive_topology: str
    tissue_domains: tuple[str, ...]
    organs: tuple[OrganRecipe, ...]
    vascular_evidence: VascularEvidence
    physical_scale_mm_per_BU: float = MM_PER_BLENDER_UNIT

    def __post_init__(self):
        if not self.organs or any(r.emitter is not None and r.evidence == 'UNMEASURED_ONLY' for r in self.organs):
            raise PlatformError('Cannot silently render an unmeasured-only organ')
        ids = [o.organ_id for o in self.organs]
        if len(ids) != len(set(ids)):
            raise PlatformError('Duplicate organ IDs in fruit plan')
        if self.anatomy_origin != self.context.specimen.developmental_origin:
            raise PlatformError('Origin does not match measured specimen')
        if self.reproductive_topology != self.context.specimen.reproductive_plan:
            raise PlatformError('Wrong reproduction plan for specimen')
        if self.physical_scale_mm_per_BU != 1.0:
            raise PlatformError('M2a uses explicit 1 BU = 1 mm; rescaling needs an explicit adapter')
        v = self.vascular_evidence
        if v.scope == 'SAME_TAXON_QUALITATIVE' and v.source_taxon != self.context.specimen.taxon:
            raise PlatformError('Incompatible species vascular reference')

    @property
    def renderable_parts(self) -> tuple[OrganRecipe, ...]:
        return tuple(o for o in self.organs if o.emitter is not None)

    def as_dict(self) -> dict:
        v = self.vascular_evidence
        return {
            'instance_id': self.context.instance_id,
            'adapter': self.adapter_id,
            'seed': self.context.seed,
            'detail': self.context.detail,
            'specimen': provenance_dict(self.context.specimen),
            'developmental_origin': self.anatomy_origin,
            'reproductive_topology': self.reproductive_topology,
            'tissue_domains': list(self.tissue_domains),
            'organs': [{
                'id': o.organ_id, 'role': o.role, 'emitter': o.emitter,
                'params': dict(o.params), 'evidence': o.evidence,
                'rows': list(o.evidence_rows), 'caveat': o.caveat,
            } for o in self.organs],
            'vascular': {
                'source_taxon': v.source_taxon, 'scope': v.scope,
                'source_id': v.source_id,
                'visible_geometry_generated': False,
                'organ_graph_names': [n.organ_id for n in v.graph.organs] if v.graph else [],
                'connection_count': len(v.graph.connections) if v.graph else 0,
                'calibrated_diameters': False,
            },
            'operations': {'cut': 'NOT_ANATOMY; NOT_IMPLEMENTED_IN_M2A',
                           'export': 'BLENDER_SCENE_ONLY'},
            'mm_per_BLENDER_UNIT': self.physical_scale_mm_per_BU,
        }

    def digest(self) -> str:
        payload = json.dumps(self.as_dict(), ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()


class FruitAdapter(Protocol):
    adapter_id: str
    taxon: str
    developmental_origin: str

    def make_plan(self, context: FruitContext) -> FruitPlan:
        ...


def _measured_params(**kwargs: float | int) -> tuple[tuple[str, int | float], ...]:
    return tuple(sorted(kwargs.items()))


class StrawberryReceptacleAdapter:
    """Own topology: external true fruits attached to floral receptacle."""
    adapter_id = 'fragaria_receptacle_v1'
    taxon = 'Fragaria × ananassa'
    developmental_origin = 'expanded_floral_receptacle'

    def make_plan(self, context: FruitContext) -> FruitPlan:
        s = context.specimen
        if s.taxon != self.taxon or s.developmental_origin != self.developmental_origin:
            raise PlatformError('Fragaria adapter cannot build a different organ origin')
        if not s.fruit_height or not s.fruit_width or s.achene_mean is None:
            raise PlatformError('Strawberry silhouette and achene mean require actual source')
        if s.display_achene_count is None or s.display_achene_count <= 0:
            raise PlatformError('Invalid source-based achene count')
        organs = (
            OrganRecipe('receptacle', 'fruit_flesh', 'schematic_receptacle_envelope',
                        _measured_params(height_mm=s.fruit_height.mm,
                                         width_mm=s.fruit_width.mm),
                        'MEASURED_EXTENT',
                        (s.fruit_height.observation_id, s.fruit_width.observation_id),
                        'Silhouette from reusable algorithm, not measured surface points.'),
            OrganRecipe('surface_achenes', 'surface_true_fruits',
                        'schematic_surface_marker_scatter',
                        _measured_params(marker_count=s.display_achene_count),
                        'MEASURED_COUNT_MEAN', (s.achene_mean_id,),
                        'Count is rounded study mean. Seed size and phyllotaxis are ARTIST.'),
            OrganRecipe('cortex_pith', 'interior_tissue', None, (),
                        'QUALITATIVE_ONLY', ('S02',),
                        'No ripe-cortex numeric cell model measured for Camarosa.'),
            OrganRecipe('achene_vascular_traces', 'vascular_branches', None, (),
                        'QUALITATIVE_ONLY', ('S02',),
                        'No quantitative connection paths/diameters; NOT generated.'),
            OrganRecipe('calyx', 'floral_attachment', None, (),
                        'UNMEASURED_ONLY', (), 'No matched Camarosa dimensions; NOT generated.'),
        )
        graph = strawberry_anatomy()
        return FruitPlan(context, self.adapter_id, s.developmental_origin,
                         s.reproductive_plan,
                         ('epidermis', 'cortex', 'vascular_zone', 'pith'),
                         organs, VascularEvidence(self.taxon,'SAME_TAXON_QUALITATIVE','S02',graph))


class KiwiLocularBerryAdapter:
    """Own topology: ovary pericarp, locules, placental internal seeds.

    Widths/cell size measurements are from yellow A. chinensis. Guo 2013
    vascular anatomy is GREEN A. deliciosa, therefore REFERENCE_ONLY.
    """
    adapter_id = 'actinidia_ovary_v1'
    taxon = 'Actinidia chinensis var. chinensis'
    developmental_origin = 'multicarpellate_ovary_pericarp'

    def make_plan(self, context: FruitContext) -> FruitPlan:
        s = context.specimen
        if s.taxon != self.taxon or s.developmental_origin != self.developmental_origin:
            raise PlatformError('Kiwi adapter cannot build a different organ origin')
        boundaries = s.region_boundaries_mm
        if len(boundaries) != 3:
            raise PlatformError('Kiwi must have 3 source-measured radial extents')
        region_rows = tuple(s.radial_region_widths[k].observation_id
                            for k in ('core','inner_pericarp','outer_pericarp'))
        cell_rows = tuple(s.cell_diameters[k].observation_id for k in
                         ('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large'))
        organs = (
            OrganRecipe('pericarp_tissue_zones','tissue_domains',
                        'schematic_radial_pericarp_section',
                        _measured_params(core_boundary_mm=boundaries[0],
                                         inner_boundary_mm=boundaries[1],
                                         outer_boundary_mm=boundaries[2]),
                        'MEASURED_EXTENT', region_rows,
                        'Measured radial transect only: 2D schematic circular regions, not whole fruit.'),
            OrganRecipe('cell_size_gauges', 'measurement_visualization',
                        'measured_cell_diameter_gauges',
                        _measured_params(**{k+'_diameter_mm': s.cell_diameters[k].mm
                                           for k in ('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large')}),
                        'MEASURED_DIAMETER_ONLY', cell_rows,
                        'These are scale calibration circles, not real cell membranes or packing.'),
            OrganRecipe('locules_placenta', 'seed_bearing_ovary', None, (),
                        'QUALITATIVE_ONLY', ('K04',),
                        'Locule count, positions and vascular architecture for this cultivar UNMEASURED.'),
            OrganRecipe('internal_seeds', 'internal_reproductive_structures', None, (),
                        'UNMEASURED_ONLY', (),
                        'Kiwi seed count/position are NOT given in Jeon Table 3–5.'),
            OrganRecipe('calyx_hairs', 'surface_attachment', None, (),
                        'UNMEASURED_ONLY', (), 'Hair density and calyx sizes not measured.'),
        )
        # Guo et al. studied A. deliciosa, NOT these A. chinensis cultivars.
        ref = kiwi_anatomy()
        vascular = VascularEvidence(ref.taxon, 'CROSS_TAXON_REFERENCE_ONLY',
                                    'K04', graph=None)
        return FruitPlan(context, self.adapter_id, s.developmental_origin,
                         s.reproductive_plan, ('core','inner_pericarp','outer_pericarp'),
                         organs, vascular)


class FruitRegistry:
    """Registration is constructor-only. Builders never mutate global state."""
    def __init__(self, adapters: tuple[FruitAdapter, ...]):
        lookup: dict[str,FruitAdapter] = {}
        for adapter in adapters:
            if adapter.taxon in lookup:
                raise PlatformError('Duplicate registry taxon')
            lookup[adapter.taxon] = adapter
        if not lookup:
            raise PlatformError('Empty fruit registry')
        self._by_taxon = MappingProxyType(lookup)

    def available_taxa(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_taxon))

    def plan(self, context: FruitContext) -> FruitPlan:
        taxon = context.specimen.taxon
        try:
            adapter = self._by_taxon[taxon]
        except KeyError as exc:
            raise PlatformError(f'No topology adapter for taxon {taxon}') from exc
        plan = adapter.make_plan(context)
        if plan.context is not context or plan.adapter_id != adapter.adapter_id:
            raise PlatformError('Adapter returned mismatched context')
        return plan


def standard_registry() -> FruitRegistry:
    return FruitRegistry((StrawberryReceptacleAdapter(), KiwiLocularBerryAdapter()))


def make_context(catalog: dict, cultivar: str, instance_id: str,
                 *, seed: int=1729, detail: str='preview') -> FruitContext:
    """Only the exact-context M1f measurement selector can construct a context."""
    specimen = get_specimen(catalog, cultivar)
    return FruitContext(instance_id, specimen, seed=seed, detail=detail)


def plans_digest(plans: tuple[FruitPlan, ...]) -> str:
    ids = [p.context.instance_id for p in plans]
    if len(ids) != len(set(ids)):
        raise PlatformError('Instance IDs must be unique in a Blender scene')
    return hashlib.sha256(json.dumps({p.context.instance_id:p.digest()
                                      for p in sorted(plans,key=lambda p:p.context.instance_id)},
                                     sort_keys=True).encode()).hexdigest()