import numpy as np, trimesh, shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
import shapely.affinity as aff
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from verify import holes, vol_in, ZONES, overhang_area, BASE
m = trimesh.load(__import__('sys').argv[1] if len(__import__('sys').argv) > 1 else 'concepto_D_robot.stl')
ok = True
for x in (0.5, 3, 8, 16):
    if holes(BASE, x) != holes(m, x): ok = False; print('x', x, 'DIFF')
for n, z in ZONES.items():
    va, vb = vol_in(BASE, z), vol_in(m, z)
    if abs(va-vb) > 0.5: ok = False; print(n, round(va,1), round(vb,1))
print('interior identical' if ok else 'CHECK', '| watertight', m.is_watertight, '| overhang', overhang_area(m),
      '| size %.1f x %.1f x %.1f' % (m.extents[1], m.extents[2], m.extents[0]), '| vol cm3 %.1f' % (m.volume/1000))
YS = 57.2
def silhouette(mesh, xmax=None):
    tri = mesh.triangles[:, :, 1:3]
    if xmax is not None:
        keep = mesh.triangles[:, :, 0].max(1) <= xmax
        tri = tri[keep]
    polys = [Polygon(t) for t in tri]
    polys = [p for p in polys if p.area > 1e-6]
    return unary_union(polys).buffer(0)
for label, xmax in (('silueta completa (YZ)', None), ('cara frontal (x<=0.6, incl. grabados)', 0.61)):
    s = silhouette(m, xmax)
    mir = aff.scale(s, xfact=-1, yfact=1, origin=(YS, 0))
    diff = s.symmetric_difference(mir)
    def clean2(g):
        g = g.buffer(0.05).buffer(-0.05)
        polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        out = []
        for p in polys:
            if p.area < 1: continue
            out.append(Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area > 1]))
        return unary_union(out)
    s, mir = clean2(s), clean2(mir)
    diff = s.symmetric_difference(mir)
    h = s.boundary.hausdorff_distance(mir.boundary)
    print('   huecos:', [tuple(round(c,1) for c in Polygon(r).bounds) for p in ([s] if s.geom_type=='Polygon' else s.geoms) for r in p.interiors])
    print(f'{label}: area {s.area:.0f} mm2, area asimetrica {diff.area:.2f} mm2, error maximo (Hausdorff) {h:.3f} mm')
