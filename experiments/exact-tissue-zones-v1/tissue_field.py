"""Continuous ARTIST relief components in the original fruit rest space."""

from math import cos, hypot, sin

from mathutils import Vector
from mathutils.noise import noise

CONTROLS = (
    ("strawberry_tissue_cortex_mm", "Cortex relief (mm)", 0.135, 0.28),
    ("strawberry_tissue_pith_mm", "Pith relief (mm)", 0.052, 0.16),
    ("strawberry_tissue_vascular_mm", "Vascular relief (mm)", 0.045, 0.14),
)
VASCULAR_REACH_MM = 1.0


def tissue_masks(rest, atlas):
    x, y, z = rest
    radius = hypot(x - .017*sin(6*z), y - .014*cos(4*z))
    axial_radius = .090 + .142*min(1.0, max(0.0, (z+1.14)/2.16))
    relative_radius = radius / axial_radius
    # Keep the amber axial tissue in the core and suppress isolated pale peripheral strands.
    axial = 1 - smoothstep((relative_radius - .72) / 1.18)
    green = smoothstep((atlas.sample_green(rest) - .095) / .225)
    core = 1 - smoothstep((relative_radius - .46) / .46)
    pith = axial * (green + (1 - green)*core)
    return 1 - pith, pith


def tissue_components(rest, mm, atlas, strands):
    """Return three nonnegative unit responses before the geometric seam fade."""
    cortex, pith = tissue_masks(rest, atlas)
    x, y, z = rest * mm
    fine = noise(Vector((x/.68 + 17.4, y/.68 + 9.2, z/1.18 - 5.1)), noise_basis="PERLIN_NEW")
    meso = noise(Vector((x/1.55 - 4.6, y/1.55 + 3.7, z/2.7 + 8.6)), noise_basis="PERLIN_NEW")
    pulp = noise(Vector((x/3.3 + 1.7, y/3.3 - 11.2, z/4.6 + 7.4)), noise_basis="PERLIN_NEW")
    cortex_signal = min(1.0, max(0.0, .43 + .54*fine + .23*meso))
    pith_signal = min(1.0, max(0.0, .42 + .43*pulp))
    vascular = 0.0
    if strands is not None:
        reach = VASCULAR_REACH_MM / mm
        halo = 1 - smoothstep(strands.distance(rest, reach) / reach)
        vascular = halo * min(1.0, max(0.0, .58 + .37*meso + .18*fine))
    return cortex*cortex_signal, pith*pith_signal, vascular
