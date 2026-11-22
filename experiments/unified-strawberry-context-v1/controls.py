"""Affine integration adapter around the existing immutable M2a FruitContext."""
from dataclasses import dataclass
from math import isfinite
import hashlib,json
from fruit_platform import FruitContext,OrganRecipe,standard_registry

@dataclass(frozen=True)
class SharedDeformation:
    context: FruitContext
    width_factor: float
    height_factor: float

    def __post_init__(self):
        if self.context.seed != 1729:
            raise ValueError('This slice preserves source seed1729; scatter regeneration is not implemented')
        if any(isinstance(v,bool) or not isfinite(v) or not .65<=v<=1.35
               for v in (self.width_factor,self.height_factor)):
            raise ValueError('Artist factors must be finite in0.65..1.35')
        standard_registry().plan(self.context)

    def forward(self,p):
        return (p[0]*self.width_factor,p[1]*self.width_factor,p[2]*self.height_factor)

    def inverse(self,p):
        return (p[0]/self.width_factor,p[1]/self.width_factor,p[2]/self.height_factor)

    def record(self):
        plan=standard_registry().plan(self.context)
        recipe=OrganRecipe('pr34_affine_bundle','integrated_display','pr34_shared_affine',
            (('width_factor',self.width_factor),('height_factor',self.height_factor)),
            'ARTIST_SHARED_MAPPING',(), 'Not a measured cultivar silhouette or solved vascular topology')
        return {'instance_id':self.context.instance_id,'context_class':'fruit_platform.FruitContext',
                'seed':self.context.seed,'detail':self.context.detail,'research_plan_digest':plan.digest(),
                'recipe':{'organ_id':recipe.organ_id,'emitter':recipe.emitter,'evidence':recipe.evidence,
                          'params':dict(recipe.params)},'mapping':'F(x,y,z)=(width*x,width*y,height*z)',
                'vascular_connection_constraint':'UNRESOLVED:539diagnostic endpoints !=264achenes',
                'measured_specimen_reference_mm':{'height':self.context.specimen.fruit_height.mm,
                                                 'width':self.context.specimen.fruit_width.mm},
                'limits':'Affine morph only. Seed count/distribution and tissue synthesis are not regenerated. Reference-mm relief wavelengths/depths stretch with F.'}

    def digest(self):
        return hashlib.sha256(json.dumps(self.record(),sort_keys=True).encode()).hexdigest()
