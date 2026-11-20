"""Evidence-first access to measured fruit anatomy, with cultivar and treatment guards.

Only factual observations from cited literature. This module does not assert
that source table means are universal defaults, or generate Geometry Nodes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EvidenceError(ValueError):
    """Requested a measurement that is not supported by one exact experiment."""


def load_catalog(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    catalog = json.loads(p.read_text(encoding='utf-8'))
    if catalog.get('schema_version') != 'fruit_morphometry.1':
        raise EvidenceError('Unsupported morphometry catalog schema')
    ids = [row['id'] for row in catalog['observations']]
    if len(ids) != len(set(ids)):
        raise EvidenceError('Repeated measurement identifiers')
    for row in catalog['observations']:
        if row['source_id'] not in catalog['sources']:
            raise EvidenceError(f"Unregistered source: {row['source_id']}")
    return catalog


def select_observations(catalog: dict, *, source_id: str, taxon: str,
                        cultivar: str, stage: str, treatment: str,
                        tissue: str | None = None, metric: str | None = None) -> list[dict]:
    """Require an exact experiment identity to prevent cross-taxon pooling.

    No default or fallback for unspecified cultivar, stage or treatment.
    This deliberately does not deduplicate or aggregate different studies.
    """
    required = (source_id, taxon, cultivar, stage, treatment)
    if not all(isinstance(s, str) and s for s in required):
        raise EvidenceError('source, taxon, cultivar, stage and treatment are all required')
    if source_id not in catalog['sources']:
        raise EvidenceError(f'Unknown source {source_id!r}')
    if catalog['sources'][source_id]['taxon'] != taxon:
        raise EvidenceError('Study taxon differs from requested taxon')
    rows = [r for r in catalog['observations'] if all((r[k] == v for k, v in (
      ('source_id', source_id), ('taxon', taxon), ('cultivar', cultivar),
      ('stage', stage), ('treatment', treatment))))]
    if tissue is not None:
        rows = [r for r in rows if r['tissue'] == tissue]
    if metric is not None:
        rows = [r for r in rows if r['metric'] == metric]
    return rows


def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """Transform length units only, never mass, counts or a source statistic."""
    scale_mm = {'mm': 1.0, 'cm': 10.0, 'µm': 0.001}
    if from_unit not in scale_mm or to_unit not in scale_mm:
        raise EvidenceError('Only genuine length units are supported')
    return float(value) * scale_mm[from_unit] / scale_mm[to_unit]


def evidence_profile(catalog: dict, *, source_id: str, taxon: str,
                     cultivar: str, stage: str, treatment: str) -> dict:
    """Snapshot exact experimental observations; NOT an automatic material preset."""
    rows = select_observations(catalog, source_id=source_id, taxon=taxon,
                               cultivar=cultivar, stage=stage, treatment=treatment)
    if not rows:
        raise EvidenceError('No matching table observations; refusing nearest-cultivar fallback')
    if cultivar.startswith('cultivar_unverified'):
        raise EvidenceError('Unverified cultivar cannot be promoted to a named empirical preset')
    return {
      'source_id': source_id, 'source_url': catalog['sources'][source_id]['url'],
      'taxon': taxon, 'cultivar': cultivar, 'stage': stage, 'treatment': treatment,
      'type': 'experimental_evidence_not_ready_to_render',
      'measurements': [{k: r[k] for k in ('id','tissue','metric','axis','value','unit','uncertainty_value','uncertainty_kind','statistic','source_locator')} for r in rows],
      'warnings': ['Experimental observations only: not a universal botanical preset.',
         'Do not mix organs/regions or infer unmeasured seed/vessel/calxy dimensions.',
         'Model world scale needs an explicit physical mm mapping before any Blender use.']
    }