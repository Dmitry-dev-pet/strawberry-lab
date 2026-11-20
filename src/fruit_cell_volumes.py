"""M2c: independent physical 3-D cell specimens and exact orthogonal sections.

The only source-calibrated geometric dimension is *population mean cell
 diameter* for exact Jeon/Oh/Song (2024) untreated yellow kiwi specimens.
All individual positions, numbers, 3-D spacing, ellipsoid anisotropy,
intercellular void fractions, and the conversion of a histological 2-D
mean diameter to 3-D equivalent volume are EXPLICIT ARTIST HYPOTHESES.
These meshes are not a reconstruction of the histology or 3-D packing.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import ceil, floor, sqrt, sin, cos, pi, prod
from random import Random
from hashlib import sha256
from typing import Iterable
from fruit_platform import FruitPlan
from fruit_biocomponents import measured_cell_populations, MissingBiologicalEvidence

MM_PER_BU=1.0
CELL_REFERENCE='JEON2024, Table 5, control, 180_DAA'
MORPHOLOGY_REFERENCE='White et al. 2018 Acta Hortic. 1218, small isodiametric + large ellipsoidal cells in Actinidia chinensis, abstract'
ARRANGEMENT_STATUS='ARTIST_SPATIAL_PLACEMENT_NOT_OBSERVED_HISTOLOGY'
ASPECT_STATUS='ARTIST_ELLIPSOID_AXIS_RATIOS_NOT_MEASURED'

# Volume-conserving aspect ratios: geometric-mean axis scaling = ~1.
# These factors are illustrative, not observations about the named cultivars.
ASPECTS={
    'core':(1.06,.98,1/(1.06*.98)),
    'inner_pericarp':(1.25,.90,1/(1.25*.90)),
    'outer_pericarp_small':(1.04,.98,1/(1.04*.98)),
    'outer_pericarp_large':(1.25,.90,1/(1.25*.90)),
}
REGIONS=('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large')

@dataclass(frozen=True)
class CellSolid:
    cell_id:int
    instance_id:str
    cultivar:str
    region:str
    center_mm:tuple[float,float,float]
    half_axes_mm:tuple[float,float,float]
    mean_diameter_mm:float
    source_row:str
    size_interpretation:str='3D_VOLUME_EQUIVALENT_FROM_MEASURED_2D_MEAN_DIAMETER__MODELLING_ASSUMPTION'
    shape_status:str=ASPECT_STATUS
    arrangement_status:str=ARRANGEMENT_STATUS

    @property
    def volume_equiv_diameter_mm(self)->float:
        return 2*prod(self.half_axes_mm)**(1/3)

    def inside(self,point:tuple[float,float,float])->float:
        return sum(((point[k]-self.center_mm[k])/self.half_axes_mm[k])**2 for k in range(3))

    def ellipse(self, normal_axis:int, offset_mm:float=0.0):
        """Exact ellipse of the physical 3-D ellipsoid with a coordinate plane.

        Returns (two 3D axis indices, cross-plane center, elliptical radii)
        or None. BOTH perpendicular cuts sample the SAME CellSolid, never a
        re-seeded 2-D texture.
        """
        if normal_axis not in (0,1,2):raise ValueError('bad plane axis')
        q=1-((offset_mm-self.center_mm[normal_axis])/self.half_axes_mm[normal_axis])**2
        if q<=1e-12:return None
        axes=tuple(i for i in range(3) if i!=normal_axis)
        return axes,self.center_mm,tuple(self.half_axes_mm[i]*sqrt(q) for i in axes)

    def section_point(self,normal_axis:int,angle:float,offset_mm:float=0.0):
        e=self.ellipse(normal_axis,offset_mm)
        if e is None:raise ValueError('cell does not intersect this plane')
        a,center,axes=e
        p=list(center);p[normal_axis]=offset_mm
        p[a[0]]+=axes[0]*cos(angle);p[a[1]]+=axes[1]*sin(angle)
        return tuple(p)

@dataclass(frozen=True)
class TissueVolume:
    instance_id:str
    cultivar:str
    taxon:str
    region:str
    side_mm:float
    cells:tuple[CellSolid,...]
    parameters_status:str=ARRANGEMENT_STATUS

    def by_region(self,region):return tuple(c for c in self.cells if c.region==region)


def _hashseed(label:str)->int:
    return int.from_bytes(sha256(label.encode('utf8')).digest()[:8],'little')


def _stable_axes(mean_diameter:float,region:str):
    factors=ASPECTS[region]
    return tuple(.5*mean_diameter * q for q in factors)


def _lattice(axes:tuple[float,float,float],side_mm:float,seed:int,limit:int|None=None):
    """Irregular artist packing from jittered candidates and collision rejection.

    Spatial density, jitter, and gaps are NOT sourced from histology. For
    identical axis-aligned ellipsoids, the normalized separation test
    below ensures 3-D solids do not geometrically overlap.
    """
    rng=Random(seed)
    steps=tuple(2*a*1.16 for a in axes)
    counts0=tuple(max(1,int(floor((side_mm-2*a)/step))+1) for a,step in zip(axes,steps))
    counts=tuple(n-1 if n>1 and n%2==0 else n for n in counts0)
    candidates=[]
    for ix in range(counts[0]):
      for iy in range(counts[1]):
       for iz in range(counts[2]):
        idx=(ix,iy,iz)
        raw=tuple((j-(counts[k]-1)/2)*steps[k] for k,j in enumerate(idx))
        jitter=tuple((rng.random()-.5)*.38*steps[k] for k in range(3))
        pt=tuple(raw[k]+jitter[k] for k in range(3))
        if all(abs(pt[k])+axes[k] <= side_mm/2+1e-9 for k in range(3)):
            candidates.append(pt)
    rng.shuffle(candidates)
    # Neighborhood hash: cells only need neighbors within 2*largest axis.
    binwidth=2*max(axes)
    bins={};accepted=[]
    for pt in candidates:
        q=tuple(floor(p/binwidth) for p in pt)
        fits=True
        for i in (-1,0,1):
         for j in (-1,0,1):
          for k in (-1,0,1):
           for other in bins.get((q[0]+i,q[1]+j,q[2]+k),()):
            norm=sum(((pt[t]-other[t])/(2*axes[t]))**2 for t in range(3))
            if norm < 1.04**2:
                fits=False;break
           if not fits:break
          if not fits:break
         if not fits:break
        if fits:
            bins.setdefault(q,[]).append(pt);accepted.append(pt)
        if limit is not None and len(accepted)>=limit:break
    return tuple(accepted)


def _nonoverlap_with_big(pt,axes,big_cells,clearance_mm):
    # A deliberately conservative sufficient criterion (bounding spheres).
    small_r=max(axes)
    for c in big_cells:
        big_r=max(c.half_axes_mm)
        delta=sum((pt[k]-c.center_mm[k])**2 for k in range(3))
        if delta < (big_r+small_r+clearance_mm)**2:return False
    return True


def build_volume(plan:FruitPlan, *,side_mm:float=.80,single_side_mm:float=.58,seed_offset:int=0)->TissueVolume:
    """One sample per tissue region; outer is mixed with large+small in 3-D."""
    if plan.context.specimen.taxon != 'Actinidia chinensis var. chinensis':
        raise MissingBiologicalEvidence('M2c requires exact untreated yellow A.chinensis diameters')
    specs=measured_cell_populations(plan)
    d={c.region:c.mean_diameter_mm for c in specs}
    provenance={c.region:c.source_row for c in specs}
    if set(d)!=set(REGIONS):raise MissingBiologicalEvidence('Missing exact-region mean diameters')
    blocks=[]
    ident=0
    prefix=plan.context.instance_id+':'+plan.context.specimen.cultivar+':'+str(seed_offset)
    for region in ('core','inner_pericarp'):
        cells=[]
        axes=_stable_axes(d[region],region)
        for p in _lattice(axes,single_side_mm,_hashseed(prefix+region)):
            cells.append(CellSolid(ident,plan.context.instance_id,plan.context.specimen.cultivar,
               region,p,axes,d[region],provenance[region]));ident+=1
        blocks.append(TissueVolume(plan.context.instance_id,plan.context.specimen.cultivar,
                      plan.context.specimen.taxon,region,single_side_mm,tuple(cells)))
    # Big cells spatially mixed with small, matching a qualitative feature
    # of microscopy; their NUMBER and 3-D packing are explicitly not sourced.
    large='outer_pericarp_large';small='outer_pericarp_small'
    l_axes=_stable_axes(d[large],large);s_axes=_stable_axes(d[small],small)
    big=[]
    for j,p in enumerate(_lattice(l_axes,side_mm,_hashseed(prefix+large))):
        if _hashseed(prefix+':large-selection:'+str(j)) % 3 == 0:  # ARTIST subsampling, no source density
            continue
        big.append(CellSolid(ident,plan.context.instance_id,plan.context.specimen.cultivar,
             large,p,l_axes,d[large],provenance[large]));ident+=1
    smalls=[]
    for p in _lattice(s_axes,side_mm,_hashseed(prefix+small)):
        if _nonoverlap_with_big(p,s_axes,big,.007):
            smalls.append(CellSolid(ident,plan.context.instance_id,plan.context.specimen.cultivar,
                    small,p,s_axes,d[small],provenance[small]));ident+=1
    blocks.append(TissueVolume(plan.context.instance_id,plan.context.specimen.cultivar,
                  plan.context.specimen.taxon,'outer_pericarp_MIXED_ARTIST',side_mm,tuple(big+smalls)))
    for block in blocks:
        if not block.cells:raise AssertionError('Generated empty 3D tissue sample')
        for c in block.cells:
            if any(abs(c.center_mm[k])+c.half_axes_mm[k]>block.side_mm/2+1e-8 for k in range(3)):
                raise AssertionError('Outside physical sample box')
            if abs(c.volume_equiv_diameter_mm-c.mean_diameter_mm)>1e-12:
                raise AssertionError('Measured source equivalent diameter not conserved')
    return tuple(blocks)


def section_records(block:TissueVolume,axis:int,offset_mm:float=0)->tuple:
    return tuple((c,c.ellipse(axis,offset_mm)) for c in block.cells if c.ellipse(axis,offset_mm))


def plan_json(blocks):
    result={'schema':'fruitengine.m2c.cells.1','units':'millimetres',
            'histology_status':'SYNTHETIC_3D_CELL_SOLIDS_DIAMETER_CALIBRATED_ONLY',
            'source_numeric':'JEON2024 TABLE5 UNTREATED A_CHINENSIS',
            'appearance_reference':MORPHOLOGY_REFERENCE,
            'warnings':['NO_SOURCE_3D_CELL_PACKING','NO_MEASURED_POROSITY','ELLIPSOID_ASPECT_ARTIST',
                        'DIAMETER_3D_VOLUME_EQUIVALENT_INTERPRETATION_IS_MODELLING_ASSUMPTION'],
            'blocks':[]}
    for block in (b for row in blocks for b in (row if isinstance(row,(tuple,list)) else (row,))):
        obj={'instance':block.instance_id,'cultivar':block.cultivar,'taxon':block.taxon,
            'region':block.region,'cube_side_mm':block.side_mm,'cell_count_artistic':len(block.cells),
            'counts_per_class':{r:sum(c.region==r for c in block.cells) for r in REGIONS},
            'section_ellipse_counts':{str(k):len(section_records(block,k)) for k in (1,2)},
            'cells':[]}
        for c in block.cells:
            obj['cells'].append({'id':c.cell_id,'region':c.region,'center_mm':c.center_mm,
                   'half_axes_mm':c.half_axes_mm,'mean_diameter_mm':c.mean_diameter_mm,
                   'source_row':c.source_row,'placement_status':ARRANGEMENT_STATUS})
        result['blocks'].append(obj)
    return result