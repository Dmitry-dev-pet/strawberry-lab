from dataclasses import dataclass
from math import isfinite
@dataclass(frozen=True)
class Recipe:
    seed: int
    achene_count: int
    a: float
    b: float
    h: float
    def __post_init__(self):
        if type(self.seed) is not int or not 0<=self.seed<2**31:raise ValueError('seed must be a nonnegative 31-bit integer')
        if type(self.achene_count) is not int or self.achene_count!=264:raise ValueError('Generator v1 currently supports exactly264 achenes')
        for value,low,high in [(self.a,-.25,.3),(self.b,-.25,.3),(self.h,.85,1.2)]:
            if isinstance(value,bool) or not isfinite(value) or not low<=value<=high:raise ValueError('Invalid artist profile coefficient')
