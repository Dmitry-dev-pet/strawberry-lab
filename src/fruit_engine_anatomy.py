"""Taxon-specific organ graphs on one reusable typed anatomical graph API.

Provenance:
  S02: Darrow, The Strawberry (1966) printed figs 19-38, 19-39
  K04: Guo et al., Vascular anatomy of kiwi fruit (2013), figs 1-5

Edges are qualitative, and DO NOT assert measured diameter/flow/branch counts.
The numeric morphometry tables in the data catalog are independent evidence.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable

@dataclass(frozen=True)
class Organ:
    organ_id: str
    organ_class: str
    taxon: str
    source_id: str
    figure: str

@dataclass(frozen=True)
class Connection:
    source: str
    target: str
    relation: str
    source_id: str
    figure: str
    dimensions_status: str = 'UNMEASURED'

@dataclass(frozen=True)
class Anatomy:
    taxon: str
    fruit_type: str
    organs: tuple[Organ,...]
    connections: tuple[Connection,...]

    def check(self) -> None:
        nodes={o.organ_id:o for o in self.organs}
        if len(nodes)!=len(self.organs):raise ValueError('Repeated anatomical organ ID')
        if not self.organs or any(o.taxon!=self.taxon for o in self.organs):
            raise ValueError('Cross-taxon organ graph')
        for c in self.connections:
            if c.source not in nodes or c.target not in nodes:
                raise ValueError('Dangling anatomical relation')
            if not(c.source_id and c.figure and c.relation and c.dimensions_status=='UNMEASURED'):
                raise ValueError('No source provenance or dimensions inferred as measured')
        if self.fruit_type=='expanded_receptacle_with_achenes':
            if 'achene' not in {o.organ_class for o in self.organs}:
                raise ValueError('A strawberry topology requires external achenes')
            if 'locule' in {o.organ_class for o in self.organs}:
                raise ValueError('Strawberry cannot inherit kiwi locules')
        if self.fruit_type=='multicarpellate_ovary_berry':
            classes={o.organ_class for o in self.organs}
            if not {'locule','placenta','internal_seed','pericarp'}<=classes:
                raise ValueError('Kiwi needs placentas, locules, pericarp and internal seeds')
            if 'achene' in classes:raise ValueError('Kiwi cannot inherit strawberry achenes')


def strawberry_anatomy()->Anatomy:
    taxon='Fragaria × ananassa';source='S02';fig='Darrow 1966, Figs 19-38 and 19-39'
    org=[('pedicel','vascular_source'),('receptacle','expanded_receptacle'),
         ('epidermis','epidermis'),('cortex','parenchyma'),('pith','parenchyma'),
         ('central_bundle_ring','vascular_hub'),('achene_traces','vascular_branch'),
         ('surface_achenes','achene'),('enclosed_achene_seeds','enclosed_seed')]
    rel=[('receptacle','epidermis','boundary'),('receptacle','cortex','contains'),
         ('receptacle','pith','contains'),('pedicel','central_bundle_ring','supplies'),
         ('central_bundle_ring','achene_traces','branches_to'),
         ('achene_traces','surface_achenes','supplies'),
         ('receptacle','surface_achenes','supports_external_fruits'),
         ('surface_achenes','enclosed_achene_seeds','each_achene_contains_seed')]
    out=Anatomy(taxon,'expanded_receptacle_with_achenes',
      tuple(Organ(i,k,taxon,source,fig) for i,k in org),
      tuple(Connection(a,b,r,source,fig) for a,b,r in rel))
    out.check();return out


def kiwi_anatomy()->Anatomy:
    taxon='Actinidia deliciosa';source='K04';fig='Guo et al. 2013, Figs 1-5 (particularly Fig 5)'
    org=[('pedicel','vascular_source'),('ovary_pericarp','pericarp'),
         ('outer_pericarp','parenchyma'),('inner_pericarp','parenchyma'),
         ('central_placenta','placenta'),('peripheral_placenta','placenta'),
         ('locules','locule'),('septa','septa'),('central_bundle','vascular_hub'),
         ('outer_pericarp_bundles','vascular_branch'),('ovule_traces','vascular_branch'),
         ('internal_seeds','internal_seed')]
    rel=[('ovary_pericarp','outer_pericarp','contains'),
         ('ovary_pericarp','inner_pericarp','contains'),
         ('ovary_pericarp','locules','contains'),
         ('ovary_pericarp','septa','contains'),
         ('pedicel','central_bundle','supplies'),
         ('central_bundle','central_placenta','supplies'),
         ('central_placenta','ovule_traces','branches_to'),
         ('ovule_traces','internal_seeds','supplies'),
         ('locules','internal_seeds','encloses'),
         ('peripheral_placenta','ovule_traces','supplies'),
         ('pedicel','outer_pericarp_bundles','supplies'),
         ('outer_pericarp_bundles','outer_pericarp','supplies'),
         ('central_placenta','septa','connects_to')]
    out=Anatomy(taxon,'multicarpellate_ovary_berry',
      tuple(Organ(i,k,taxon,source,fig) for i,k in org),
      tuple(Connection(a,b,r,source,fig) for a,b,r in rel))
    out.check();return out


def export_anatomy(a:Anatomy)->dict:
    return {'taxon':a.taxon,'fruit_type':a.fruit_type,'source_quality':'QUALITATIVE_TOPOLOGY',
         'organs':[vars(o) for o in a.organs],
         'connections':[vars(c) for c in a.connections],
         'known_limitation':'Generic vascular branch counts and diameters are UNMEASURED'}