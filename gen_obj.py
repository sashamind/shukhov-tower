import math

# ---- параметры (реальные данные) ----
RINGS  = [20.15, 16.15, 12.7, 9.7, 7.05, 4.2, 1.6]   # радиусы колец, м
LEVELS = [0, 25, 50, 75, 100, 125, 148]
BEAMS  = [24, 24, 24, 24, 12, 12]                     # стержней в семействе
TWISTS = [26, 33, 44, 55, 65, 70]                     # градусы на секцию
H, MAST_H = 148, 12
ROD_R, RING_R = 0.16, 0.13                            # радиусы профилей, м
NS = 8                                                # граней в сечении трубки

verts, faces, objects = [], [], []
def start_object(name):
    objects.append((name, len(faces)))

def add_tube(p0, p1, r, ns=NS):
    """цилиндр между двумя точками"""
    ax = [p1[i]-p0[i] for i in range(3)]
    L = math.sqrt(sum(a*a for a in ax))
    if L < 1e-9: return
    ax = [a/L for a in ax]
    ref = (0,1,0) if abs(ax[1]) < 0.9 else (1,0,0)
    u = [ax[1]*ref[2]-ax[2]*ref[1], ax[2]*ref[0]-ax[0]*ref[2], ax[0]*ref[1]-ax[1]*ref[0]]
    lu = math.sqrt(sum(a*a for a in u)); u = [a/lu for a in u]
    v = [ax[1]*u[2]-ax[2]*u[1], ax[2]*u[0]-ax[0]*u[2], ax[0]*u[1]-ax[1]*u[0]]
    base = len(verts)
    for p in (p0, p1):
        for k in range(ns):
            a = 2*math.pi*k/ns
            verts.append(tuple(p[i] + r*(math.cos(a)*u[i] + math.sin(a)*v[i]) for i in range(3)))
    for k in range(ns):
        k2 = (k+1) % ns
        a, b, c, d = base+k, base+k2, base+ns+k2, base+ns+k
        faces.append((a, b, c, d))

def add_ring(rc, y, r, nseg=72, ns=NS):
    """тор: осевая окружность радиуса rc на высоте y, трубка радиуса r"""
    base = len(verts)
    for i in range(nseg):
        t = 2*math.pi*i/nseg
        cx, cz = rc*math.cos(t), rc*math.sin(t)
        # локальный базис сечения: радиальное направление + вертикаль
        ux, uz = math.cos(t), math.sin(t)
        for k in range(ns):
            a = 2*math.pi*k/ns
            verts.append((cx + r*math.cos(a)*ux, y + r*math.sin(a), cz + r*math.cos(a)*uz))
    for i in range(nseg):
        i2 = (i+1) % nseg
        for k in range(ns):
            k2 = (k+1) % ns
            faces.append((base+i*ns+k, base+i2*ns+k, base+i2*ns+k2, base+i*ns+k2))

# ---- секции: прямые стержни двух семейств ----
rod_count = 0
for s in range(6):
    start_object(f"section_{s+1}_rods")
    r1, r2 = RINGS[s], RINGS[s+1]
    y1, y2 = LEVELS[s], LEVELS[s+1]
    n = BEAMS[s]
    tw = math.radians(TWISTS[s])
    for d in (1, -1):
        for i in range(n):
            a0 = 2*math.pi*i/n
            a1 = a0 + d*tw
            p0 = (r1*math.cos(a0), y1, r1*math.sin(a0))
            p1 = (r2*math.cos(a1), y2, r2*math.sin(a1))
            add_tube(p0, p1, ROD_R)
            rod_count += 1

# ---- межсекционные кольца (двойные) ----
start_object("junction_rings")
for j in range(7):
    rr = RINGS[j]*1.02
    yy = max(LEVELS[j], 0.6)
    add_ring(rr, yy-0.55, RING_R)
    add_ring(rr, yy+0.55, RING_R)

# ---- юбка фундамента ----
start_object("base_skirt")
rA, rB, yB = 21.6, RINGS[0], 3.4
sk = math.radians(10)
for d in (1, -1):
    for i in range(40):
        a0 = 2*math.pi*i/40
        a1 = a0 + d*sk
        add_tube((rA*math.cos(a0), 0, rA*math.sin(a0)),
                 (rB*math.cos(a1), yB, rB*math.sin(a1)), ROD_R*0.8)
add_ring(rA, 0, RING_R)

# ---- траверсы и флагшток ----
start_object("mast")
rm, nm, top = 1.1, 8, H+8.5
for i in range(nm):
    a = 2*math.pi*i/nm
    p_lo = (rm*math.cos(a), H+1.2, rm*math.sin(a))
    add_tube(p_lo, (rm*math.cos(a), top, rm*math.sin(a)), 0.08)
    for d in (1, -1):
        a2 = a + d*2*math.pi/nm*2
        add_tube(p_lo, (rm*math.cos(a2), top, rm*math.sin(a2)), 0.06)
    add_tube((RINGS[6]*math.cos(a), H, RINGS[6]*math.sin(a)), p_lo, 0.08)
yy = H+1.2
while yy <= top:
    add_ring(rm, yy, 0.07, nseg=36)
    yy += 2.4
add_tube((0, top, 0), (0, H+MAST_H, 0), 0.09)

# ---- запись OBJ ----
import os
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shukhov-tower.obj")
with open(path, "w") as f:
    f.write("# Shukhov Tower (Shabolovka, 1922) - parametric reconstruction\n")
    f.write("# units: meters, Y-up (Blender OBJ importer converts to Z-up by default)\n")
    f.write(f"# rods: {rod_count} (4 lower sections x48, 2 upper x24), rings d40.3->3.2 m\n")
    for v in verts:
        f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
    bounds = objects + [("_end", len(faces))]
    for (name, f0), (_, f1) in zip(bounds, bounds[1:]):
        f.write(f"o {name}\ns 1\n")
        for q in faces[f0:f1]:
            f.write(f"f {q[0]+1} {q[1]+1} {q[2]+1} {q[3]+1}\n")

print(f"verts: {len(verts)}, quads: {len(faces)}, rods: {rod_count}, objects: {len(objects)}")
print(f"size: {os.path.getsize(path)/1e6:.1f} MB -> {path}")
