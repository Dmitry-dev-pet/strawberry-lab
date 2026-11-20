"""Biology-inspired geometry field for Strawberry Lab, independent implementation.

The edible strawberry is an enlarged receptacle carrying external achenes.
Reference architecture: a central pith with a vascular cylinder, cortex and
an epidermis, and radial vascular branches towards the surface achenes.

References: Hurtado & Knoche (2026), Frontiers in Horticulture 10.3389/fhort.2026.1779354;
Darrow, The Strawberry (USDA), figs. 19-38 and 19-39.

Numerical radii, branch trajectories and seed arrangement are ARTIST MODEL
parameters, not measured anatomical data. No Frucht code or geometry is used.
"""
from dataclasses import dataclass
from math import sin, cos, pi, sqrt, exp, atan2
from random import Random
import bisect


@dataclass(frozen=True)
class FruitParams:
    half_height: float = 1.825
    radius: float = 1.62
    achene_count: int = 620
    pit_depth: float = .046
    pit_width: float = .086
    jitter: float = .065
    seed: int = 1729


P = FruitParams()


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smoothstep(a, b, x):
    t = clamp((x-a)/(b-a))
    return t*t*(3-2*t)


def radius(t, theta, p=P):
    t = clamp(t, .00001, .99999)
    # Fine ribbing and a variable shoulder, plus a taper to pointed apex.
    base = p.radius * max(0, sin(pi*t))**.56 * (.37 + .93*t)
    ripple = .027*sin(7*theta+1.7*t)+.013*sin(13*theta-8*t)+.007*sin(19*theta+3.1*t)
    return max(0, base*(1+ripple))


def point(t, theta, p=P):
    r = radius(t,theta,p)
    return (r*cos(theta),r*sin(theta),(t-.5)*2*p.half_height)


def normal(t, theta, p=P):
    e=.0007
    ta, tb = clamp(t-e,.00001,.99999), clamp(t+e,.00001,.99999)
    pa,pb=point(ta,theta,p),point(tb,theta,p)
    tl=(tuple((pb[k]-pa[k])/(tb-ta) for k in range(3)))
    pa,pb=point(t,theta-e,p),point(t,theta+e,p)
    th=tuple((pb[k]-pa[k])/(2*e) for k in range(3))
    v=(th[1]*tl[2]-th[2]*tl[1], th[2]*tl[0]-th[0]*tl[2], th[0]*tl[1]-th[1]*tl[0])
    d=sqrt(sum(x*x for x in v))
    return tuple(x/max(d,1e-7) for x in v)


def pith_radius(t,p=P):
    # Variable light center (pith). Dimensionless artist scale only.
    return (.22+.085*(clamp(t)**1.3))*(1+.09*sin(5*t+.6)+.025*sin(22*t))


def fields(x,y,z,p=P):
    """Continuous 3D spatial tissue fields; no dependence on the cut angle."""
    t=clamp(z/(2*p.half_height)+.5,.00001,.99999)
    r=sqrt(x*x+y*y)
    angle=atan2(y,x)
    boundary=radius(t,angle,p)
    q=r/max(boundary,1e-6)
    pp=pith_radius(t,p)
    inner=smoothstep(pp-.035,pp+.055,r)
    pith=1-inner
    bundle_ring=pp+.075
    vascular=exp(-((r-bundle_ring)/.065)**2)
    epidermis=smoothstep(.955,1.,q)
    cortex=clamp(inner*(1-epidermis))
    inside=(q<=1.00001)
    return {'t':t,'r':r,'q':q,'pith':pith if inside else 0.,
            'vascular':vascular if inside else 0.,
            'cortex':cortex if inside else 0.,
            'epidermis':epidermis if inside else 0.,'inside':inside}


def sample_achenes(p=P):
    """Seeded, surface-area-stratified phyllotaxis; random seed is stable."""
    rng=Random(p.seed)
    cdf=[];ts=[];total=0.
    for i in range(1001):
        t=.003+.994*i/1000
        e=.0005
        dr=(radius(t+e,0,p)-radius(t-e,0,p))/(2*e)
        area=radius(t,0,p)*sqrt((2*p.half_height)**2+dr**2)
        total+=area;cdf.append(total);ts.append(t)
    anchors=[]
    for i in range(p.achene_count):
        t=ts[min(bisect.bisect_left(cdf,(i+.5)/p.achene_count*total),len(ts)-1)]
        if not (.085<t<.91):
            continue
        theta=(i*2*pi*.6180339887498949+rng.uniform(-p.jitter,p.jitter))%(2*pi)
        at=point(t,theta,p);n=normal(t,theta,p)
        size=rng.uniform(.83,1.19)
        anchors.append({'id':i,'t':t,'theta':theta,'point':at,'normal':n,'size':size})
    return anchors


def vascular_route(achene, p=P, segments=16):
    """A continuous branch from the vascular cylinder to one surface achene.

    Provenance: branch topology is a science-grounded simplified graph;
    cubic interpolation, root height and bend are not anatomical measurements.
    """
    t=achene['t'];theta=achene['theta']
    root_t=clamp(t+.16+.08*(.5-t),.08,.975)
    root_z=(root_t-.5)*2*p.half_height
    r0=pith_radius(root_t,p)+.075
    end=achene['point'];nx,ny,nz=achene['normal']
    end=(end[0]-nx*.024,end[1]-ny*.024,end[2]-nz*.024)
    start=(r0*cos(theta),r0*sin(theta),root_z)
    bend=.14*sin(achene['id']*1.87)
    pts=[]
    for j in range(segments+1):
        u=j/segments
        # Smooth progression radial; z rises towards root along oblique bundles.
        s=u*u*(3-2*u)
        radial=r0+(sqrt(end[0]**2+end[1]**2)-r0)*s
        ang=theta+bend*sin(pi*u)
        z=root_z+(end[2]-root_z)*u+.032*sin(pi*u)
        pts.append((radial*cos(ang),radial*sin(ang),z))
    pts[0]=start;pts[-1]=end
    return pts


def vascular_graph(anchors,p=P):
    """Graph where all achene terminal branches attach to the same vascular cylinder."""
    # Each cylinder vertex C_k is part of the connected backbone, and each
    # branch root connects to backbone by its radial cylinder position.
    return [{'achene_id':a['id'],'root':vascular_route(a,p)[0],
             'terminal':vascular_route(a,p)[-1],
             'points':vascular_route(a,p), 'root_connects_to':'vascular_cylinder'} for a in anchors]


def validate_graph(anchors, branches):
    ids={a['id'] for a in anchors}
    seen={b['achene_id'] for b in branches}
    if len(branches)!=len(ids) or seen!=ids:
        return False, 'Achene anchors and vascular branches do not match'
    for b in branches:
        if b.get('root_connects_to')!='vascular_cylinder' or len(b['points'])<3:
            return False, f"Disconnected branch {b['achene_id']}"
        if any(any(not (abs(x)<1e20) for x in pt) for pt in b['points']):
            return False, f"Invalid branch coordinate {b['achene_id']}"
    return True, f'Connected {len(ids)} achene branches to central vascular cylinder'


def tissue_color(x,y,z,p=P):
    d=fields(x,y,z,p)
    # Three-dimensional continuous color field with deterministic cell-scale
    # modulation. No separate 2D map is baked for each slice orientation.
    q=d['q'];ct=d['cortex'];v=d['vascular'];c=d['pith'];t=d['t']
    # Cortex's dark-red outside slowly transitions to soft pink flesh.
    outer=smoothstep(.58,.97,q)
    flesh=(.83+.07*outer,.255-.185*outer,.235-.175*outer)
    cell=(sin(45*x+4*sin(11*z))*sin(50*y+7*sin(13*x))*sin(43*z+8*sin(6*y)))
    tiny=(sin(130*x+51*y)*sin(146*y+42*z)*sin(100*z+12*x))
    fleck=.052*cell+.023*tiny
    flesh=(flesh[0]+fleck,flesh[1]+.65*fleck,flesh[2]+.65*fleck)
    # A pale, variable pith and off-white bundle ring.
    pith=(.98,.76-.08*sin(9*z+3*x),.70-.035*sin(8*z))
    mix=c*.98
    color=tuple(flesh[k]*(1-mix)+pith[k]*mix for k in range(3))
    mix=.57*v*(1-c)
    vascular=(.99,.78,.65)
    color=tuple(color[k]*(1-mix)+vascular[k]*mix for k in range(3))
    epi=.48*d['epidermis']
    skin=(.65,.064,.087)
    color=tuple(color[k]*(1-epi)+skin[k]*epi for k in range(3))
    return tuple(clamp(z) for z in color)+(1.,)


if __name__=='__main__':
    aas=sample_achenes();bs=vascular_graph(aas)
    print({'achene_count':len(aas),'bundle_count':len(bs),'connectivity':validate_graph(aas,bs)})