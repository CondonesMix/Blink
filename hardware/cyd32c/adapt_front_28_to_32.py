"""Adapta blink_front.stl (CYD 2.8" ESP32-2432S028) a la CYD 3.2" ESP32-2432S032C.

Ejes del STL: X = profundidad (0 = cara frontal), Y = horizontal (Y alto = lado USB/flex),
Z = vertical (Z alto = orejas superiores).
Uso: python3 mod32.py <entrada.stl> <salida.stl> [grosor_cristal_mm]
"""
import sys
import numpy as np
import trimesh
from trimesh.creation import box, cylinder

src, dst = sys.argv[1], sys.argv[2]
T_STACK = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0  # cristal+tactil+cinta: frente cristal -> cara PCB

LIP = 1.0                  # grosor del marco frontal (igual que el original)
X_SH = LIP + T_STACK       # cara frontal del PCB / apoyo
X_CAV_END = 15.6           # el hueco original llega a ~15,4 y enlaza con la ranura de la tapa
X_PIN_END = 11.0           # punta de los pines (igual que el original)

YC, ZC = 60.0, 35.0        # centro de la placa dentro de la caja
BOARD = (93.7, 55.0)
CLR = 0.35                 # holgura por lado placa-hueco
HOLE_DX, HOLE_DZ = 86.7, 48.0
PIN_D = 3.0                # agujeros de la placa: Ø3,2

# Pantalla (lado flex = Y alto). Medido sobre el plano del fabricante.
GLASS = (77.7, 55.04)
GLASS_YC = YC - 0.2
ACTIVE = (64.8, 48.6)
ACTIVE_YC = YC - 2.8
WIN_MARGIN = (0.7, 0.9)    # mismo margen que el original sobre el área activa
FLEX_EXTRA = 1.5           # holgura extra para la curva del flex


def abox(y0, y1, z0, z1, x0, x1):
    b = box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b


m = trimesh.load(src)
assert m.is_watertight

# 1) Rellenar ventana, rebaje de pantalla, ranuras y el inicio del hueco antiguo
fill = abox(12.9, 107.1, 7.4, 62.6, 0.0, X_SH + 0.02)
m = trimesh.boolean.union([m, fill], engine="manifold")

cuts = []
# 2) Hueco nuevo de la placa (elimina también los pines antiguos)
by, bz = BOARD[0] / 2 + CLR, BOARD[1] / 2 + CLR
cuts.append(abox(YC - by, YC + by, ZC - bz, ZC + bz, X_SH, X_CAV_END))

# 3) Rebaje para el cristal
gy0 = GLASS_YC - GLASS[0] / 2 - 0.6
gy1 = GLASS_YC + GLASS[0] / 2 + 0.6 + FLEX_EXTRA
gz = GLASS[1] / 2 + 0.5
cuts.append(abox(gy0, gy1, ZC - gz, ZC + gz, LIP, X_SH + 0.01))

# 4) Ventana visible
wy = ACTIVE[0] / 2 + WIN_MARGIN[0]
wz = ACTIVE[1] / 2 + WIN_MARGIN[1]
cuts.append(abox(ACTIVE_YC - wy, ACTIVE_YC + wy, ZC - wz, ZC + wz, -1.0, LIP + 0.01))

# 5) Alivio para LED RGB y LDR (cara frontal del PCB, lado opuesto al flex)
cuts.append(abox(YC - by, gy0 + 0.01, ZC - 19.0, ZC + 19.0, LIP + 0.5, X_SH + 0.01))

m = trimesh.boolean.difference([m] + cuts, engine="manifold")

# 6) Pines nuevos
pins = []
for dy in (-HOLE_DX / 2, HOLE_DX / 2):
    for dz in (-HOLE_DZ / 2, HOLE_DZ / 2):
        L = X_PIN_END - X_SH + 0.02
        c = cylinder(radius=PIN_D / 2, height=L, sections=48)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        c.apply_translation([X_SH - 0.02 + L / 2, YC + dy, ZC + dz])
        pins.append(c)
m = trimesh.boolean.union([m] + pins, engine="manifold")

m.export(dst)
print(f"OK  T_STACK={T_STACK}  apoyo PCB x={X_SH}  watertight={m.is_watertight}  bounds={np.round(m.bounds,2).tolist()}")
print(f"ventana Y {ACTIVE_YC-wy:.2f}-{ACTIVE_YC+wy:.2f}  Z {ZC-wz:.2f}-{ZC+wz:.2f}")
print(f"rebaje  Y {gy0:.2f}-{gy1:.2f}  Z {ZC-gz:.2f}-{ZC+gz:.2f}")
print(f"hueco   Y {YC-by:.2f}-{YC+by:.2f}  Z {ZC-bz:.2f}-{ZC+bz:.2f}")
print("pines   Y", YC - HOLE_DX/2, YC + HOLE_DX/2, " Z", ZC - HOLE_DZ/2, ZC + HOLE_DZ/2)
