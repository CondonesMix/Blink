import numpy as np, trimesh, shapely
from shapely.geometry import Polygon, Point, LineString, box as sbox
from shapely.ops import unary_union
import shapely.affinity as aff

import os
BASE = trimesh.load(os.environ.get('BLINK_FRONT_32', 'blink_front_CYD32.stl'))
OUT_DIR = os.environ.get('OUT_DIR', '.')
assert BASE.is_watertight
YC = 60.0
M = np.array([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]],float)  # (u=Y,v=Z,h)->(X=h,Y=u,Z=v)

def ext(poly, x0, x1):
    poly = poly.buffer(0)
    parts = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
    ms = []
    for p in parts:
        m = trimesh.creation.extrude_polygon(p, x1 - x0)
        T = M.copy(); T[0,3] = x0
        m.apply_transform(T); ms.append(m)
    return trimesh.boolean.union(ms, engine='manifold') if len(ms) > 1 else ms[0]

def bx(y0,y1,z0,z1,x0,x1):
    b = trimesh.creation.box(extents=[x1-x0,y1-y0,z1-z0])
    b.apply_translation([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]); return b

def soft(p, r):  # round all corners
    return p.buffer(-r).buffer(r) if r > 0 else p

def mirror(p):  # mirror about Y=60
    return aff.scale(p, xfact=-1, yfact=1, origin=(YC, 0))

# Zones decor must never fill (functional geometry of the adapted front)
KEEP_OUT = [
    bx(12.6,107.4, 6.8,63.2, -1,30),     # board cavity, glass recess, window, pins
    bx(-60,180, -60,140, 15.0,40),       # back: slot for the sliding back cover (x>=15.4)
    bx(107,250, 28.0,45.5, 3.5,13.0),    # USB-C plug corridor (right side)
]
def clean(decor):
    return trimesh.boolean.difference([decor]+KEEP_OUT, engine='manifold')

def base_prepared():
    # legs (Z>70) are replaced by each concept's own feet, built from the bed up
    b = trimesh.boolean.difference([BASE, bx(-5,125, 70.6,120, -5,30)], engine='manifold')
    # under-fill the side bumps (x 0..2) so they rest on the bed: no supports
    under = ext(soft(sbox(0.5,22.5,8.5,47.5),1.5),0,2.2).union(ext(soft(sbox(111.5,22.5,119.5,47.5),1.5),0,2.2), engine="manifold")
    return trimesh.boolean.union([b, clean(under)], engine='manifold')

def chevron_us(cy, cz, s=1.0):
    """'>_' prompt glyph (2D), centred at (cy, cz), ~13 x 8 mm * s"""
    g = LineString([(cy-6.5*s, cz-4*s),(cy-1.5*s, cz),(cy-6.5*s, cz+4*s)]).buffer(1.0*s, cap_style=2, join_style=2)
    u = sbox(cy+0.5*s, cz+3.0*s, cy+6.5*s, cz+5.0*s)
    return unary_union([g, u])

# ---------------- Concept A: "Bit" robot ----------------
def concept_A():
    d = []
    # antenna: stem + ball, on top (top = low Z in use)
    stem = sbox(57, -15, 63, 3)
    ball = Point(YC, -21).buffer(6.5, 64)
    d.append(ext(unary_union([stem, ball]), 0, 10))
    # round "headphone" ears on both sides, with the USB notch mirrored on the left
    for cy in (2.0, 118.0):
        ear = Point(cy, 35).buffer(14, 64)
        d.append(ext(ear, 0, 13))
    # two boots (feet), flat soles at Z=87.75 like the original legs
    for y0, y1 in ((15, 50), (70, 105)):
        boot = unary_union([sbox(y0, 66, y1, 87.75)])
        boot = soft(boot, 4).union(sbox(y0+4, 80, y1-4, 87.75))  # rounded but flat sole
        d.append(ext(boot, 0, 15))
    decor = trimesh.boolean.union(d, engine='manifold')
    decor = trimesh.boolean.difference([decor, bx(-250,13,28,45.5,3.5,13)], engine='manifold')  # mirrored notch, left
    out = trimesh.boolean.union([base_prepared(), clean(decor)], engine='manifold')
    # engraved prompt on the left boot (visible face = bed side), 0.8 mm deep
    eng = ext(chevron_us(32.5, 76, 1.0), -1, 0.8)
    return trimesh.boolean.difference([out, eng], engine='manifold')

# ---------------- Concept B: "Llaves" {} with cat ears ----------------
def concept_B():
    d = []
    # a real curly brace: sampled arcs, stroke 4.6 mm
    import math
    def arc(cy, cz, r, a0, a1, n=24):
        return [(cy + r*math.cos(math.radians(a)), cz + r*math.sin(math.radians(a)))
                for a in np.linspace(a0, a1, n)]
    sp, r = 0.5, 6.0                     # spine Y, curl radius (Z grows downward in use)
    path = ([(14, 2.0)] + arc(sp+r, 2.0+r, r, 270, 180) + [(sp, 26.0)]
            + arc(sp-r, 26.0, r, 0, 90) + arc(sp-r, 44.0, r, 270, 360)
            + [(sp, 62.0)] + arc(sp+r, 68.0-r, r, 180, 90) + [(14, 68.0)])
    left = LineString(path).buffer(2.3, 24, cap_style=1, join_style=1)
    for p in (left, mirror(left)):
        d.append(ext(p, 0, 12))
    # ears on top, rounded tips
    ear = soft(Polygon([(16,3),(29,-17),(42,3)]), 2.5)
    for p in (ear, mirror(ear)):
        d.append(ext(p, 0, 12))
    # four feet at the original leg positions, rounded toes, flat soles
    for y0, y1 in ((18.5,30.5),(34.5,46.5),(73.5,85.5),(89.5,101.5)):
        f = soft(sbox(y0, 66, y1, 87.75), 3).union(sbox(y0+3, 80, y1-3, 87.75))
        d.append(ext(f, 0, 15))
    decor = trimesh.boolean.union(d, engine='manifold')
    return trimesh.boolean.union([base_prepared(), clean(decor)], engine='manifold')

# ---------------- Concept C: "Nube" cloud ghost with prompt ----------------
def concept_C():
    d = []
    top = unary_union([Point(22,3).buffer(10,64), Point(40,-3).buffer(12,64), Point(60,-7).buffer(13,64),
                       Point(80,-3).buffer(12,64), Point(98,3).buffer(10,64)])
    top = top.intersection(sbox(-50,-60,170,9))
    d.append(ext(top, 0, 12))
    side = unary_union([Point(7,19).buffer(8.5,64), Point(3,35).buffer(10,64), Point(7,51).buffer(8.5,64)])
    for p in (side, mirror(side)):
        d.append(ext(p, 0, 13))
    # ghost skirt: five tabs, flat soles at Z=87.75
    tabs = []
    for c in (24.5, 42, 60, 78, 95.5):
        t = soft(sbox(c-8, 66, c+8, 87.75), 4).union(sbox(c-4, 80, c+4, 87.75))
        tabs.append(t)
    d.append(ext(unary_union(tabs + [sbox(16,66,104,74)]), 0, 15))
    decor = trimesh.boolean.union(d, engine='manifold')
    decor = trimesh.boolean.difference([decor, bx(-250,13,28,45.5,3.5,13)], engine='manifold')
    out = trimesh.boolean.union([base_prepared(), clean(decor)], engine='manifold')
    eng = ext(chevron_us(60, -8, 1.0), -1, 0.8)        # '>_' on the forehead puff
    return trimesh.boolean.difference([out, eng], engine='manifold')

if __name__ == '__main__':
    import sys
    for name, f in (('A', concept_A), ('B', concept_B), ('C', concept_C)):
        m = f()
        m.export(os.path.join(OUT_DIR, f'concepto_{name}.stl'))
        print(name, 'watertight', m.is_watertight, 'bounds', np.round(m.bounds,2).tolist(), 'faces', len(m.faces))

# ---------------- Concept D: symmetric robot, screen centred ----------------
YS = 57.2     # window centre: every outside feature is symmetric about this Y
def mirror_s(p):
    return aff.scale(p, xfact=-1, yfact=1, origin=(YS, 0))
def sym(p):
    return unary_union([p, mirror_s(p)])

def concept_D():
    d = []
    # head/body shell: rounded box centred on the window (Y 57.2, Z 35)
    shell = soft(sbox(YS-57.5, -3.5, YS+57.5, 73.5), 14)
    d.append(ext(shell, 0, 15))
    # antenna with ball, centred
    ant = unary_union([sbox(YS-3, -19, YS+3, 0), Point(YS, -25).buffer(6.5, 64)])
    d.append(ext(ant, 0, 10))
    # big round ears centred on Z=35, covering the original side lugs
    ear = Point(YS-56.8, 35).buffer(15.5, 96)
    d.append(ext(sym(ear), 0, 13))
    # two boots, soles on the original plane Z=87.75 (kickstand geometry unchanged)
    boot = soft(sbox(YS-37, 70, YS-11, 87.75), 5).union(sbox(YS-32, 80, YS-16, 87.75))
    d.append(ext(sym(boot), 0, 15))
    decor = trimesh.boolean.union(d, engine='manifold')
    # USB corridor (right) is cut by clean(); the left ear gets the mirrored slot as a cosmetic recess
    usb_l = bx(2*YS-250, 2*YS-107, 28.0, 45.5, 3.5, 13.0)
    decor = trimesh.boolean.difference([decor, usb_l], engine='manifold')
    out = trimesh.boolean.union([base_prepared(), clean(decor)], engine='manifold')
    # shallow engravings on the face (0.6 mm, front face = bed): cheeks, smile, rivets, ear rings
    eng = []
    # all engravings stay outside the functional band (interior box and its mirror: Y 7.0-107.4 x Z 6.8-63.2)
    eng.append(sym(Point(YS-38, 68.5).buffer(3.0, 48)))                          # cheeks, low on the face
    smile = LineString([(YS-9 + 18*t, 66.0 + 3.2*(1-(2*t-1)**2)) for t in np.linspace(0,1,40)]).buffer(0.9, 16)
    eng.append(smile)                                                             # smile under the screen
    for z in (2.5, 70.0):
        eng.append(sym(Point(YS-50, z).buffer(1.5, 32)))                          # rivets
    ring = Point(YS-56.8, 35).buffer(6.4, 96).difference(Point(YS-56.8, 35).buffer(4.8, 96))
    eng.append(sym(ring))                                                         # ear bolts
    e = ext(unary_union(eng), -1, 0.6)
    return trimesh.boolean.difference([out, e], engine='manifold')
