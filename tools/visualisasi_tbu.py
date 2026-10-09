"""Visualisasi cara pakai jig: TBU (model sederhana) dijepit kedua ragum di atas piringan utama.

Input : Ver4 Jig Assembly ragum putar.step
Output: Ver4 Jig + TBU terjepit.step   (kondisi terjepit, sudut 0°)

Model TBU disederhanakan dari gambar Nabtesco Tread Brake Unit 152-3.5 (tanpa parking brake):
panjang 300 mm (arah jepit ragum), lebar 206 mm, muka mounting (4 x M20, pola 114 x 250) menghadap
ke bawah di atas piringan utama. Bentuk hanya envelope (housing, silinder rem, lever, shoe head,
brake shoe), bukan geometri asli.

Fungsi state(...) dipakai juga oleh script render untuk gambar langkah penggunaan.
Jalankan: python3 tools/visualisasi_tbu.py   (butuh `pip install cadquery`)
"""
import math, os
import cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.Interface import Interface_Static

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'Ver4 Jig Assembly ragum putar.step')
DST = os.path.join(HERE, '..', 'Ver4 Jig + TBU terjepit.step')

CX, CZ = 505.21, -111.927
Y_DISC1_TOP = 317.3205            # muka atas piringan utama = alas TBU
TBU_L, TBU_W = 300.0, 206.0       # Nabtesco 152-3.5: panjang (arah jepit) x lebar
VISE_TILT = math.degrees(math.atan2(0.0143, 0.9999))  # sumbu kedua ragum di Ver3 miring ±0,82° terhadap Z
AX = cq.Vector(math.sin(math.radians(VISE_TILT)), 0, math.cos(math.radians(VISE_TILT)))
CLAMP_TRAVEL = 81.8               # langkah tiap rahang sampai menyentuh TBU (dicek: celah ±0,2 mm)
PIN_PULL = 20.0                   # tarik pin index agar piringan bebas

# Part yang ikut bergerak saat handle ragum diputar (rahang + batang ulir + handle)
MOVING = ('Clamp self made', 'Vise Rod', 'Handle mil', 'Handle pim', 'Handle top')
# Part yang diam saat piringan diputar
FIXED = ('Base', 'Ring UHMW', 'Bantalan UHMW', 'Pin center', 'Replika')


def read_parts(path=SRC):
    doc = TDocStd_Document(TCollection_ExtendedString('XmlOcaf'))
    r = STEPCAFControl_Reader(); r.SetNameMode(True); r.ReadFile(path); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    def name(l):
        a = TDataStd_Name()
        return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else '?'
    out = {}
    def walk(l, loc):
        ref = TDF_Label()
        if st.IsReference_s(l):
            st.GetReferredShape_s(l, ref); loc = loc.Multiplied(st.GetLocation_s(l)); l = ref
        if st.IsAssembly_s(l):
            c = TDF_LabelSequence(); st.GetComponents_s(l, c)
            for i in range(1, c.Length() + 1): walk(c.Value(i), loc)
        else:
            n = name(l)
            while n in out: n += "'"
            out[n] = cq.Shape.cast(st.GetShape_s(l).Moved(loc))
    roots = TDF_LabelSequence(); st.GetFreeShapes(roots); walk(roots.Value(1), TopLoc_Location())
    return out


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def vcyl(r, y0, y1, x=0.0, z=0.0):
    return cq.Solid.makeCylinder(r, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))


def build_tbu():
    """TBU sederhana di koordinat lokal (x = lebar, y = atas dari alas, z = panjang/arah jepit)."""
    hw, hl = TBU_W / 2, TBU_L / 2
    flange = box(-hw, hw, 0, 20, -hl, hl)
    for sx in (-57, 57):
        for sz in (-125, 125):
            flange = flange.cut(vcyl(11, -1, 21, sx, sz))           # 4 lubang mounting M20
    housing = box(-75, 75, 20, 180, -hl, hl)
    housing = housing.fillet(8, [e for e in housing.Edges() if abs(e.Center().y - 100) < 1])
    cyl = vcyl(95, 20, 215, 0, 55).fuse(vcyl(75, 215, 230, 0, 55))  # silinder rem Ø152 + cover
    cyl = cyl.cut(housing)
    lever = box(-55, 55, 180, 250, -hl, -10).cut(cyl)
    rod = vcyl(18, 250, 262, 0, -40)
    head = box(-65, 65, 262, 300, -110, 110)
    shoe = box(-60, 60, 300, 372, -145, 145).cut(
        cq.Solid.makeCylinder(430, 200, cq.Vector(-100, 775, 0), cq.Vector(1, 0, 0)))
    return {'TBU - flens mounting': flange, 'TBU - housing': housing,
            'TBU - silinder rem': cyl, 'TBU - housing lever': lever.fuse(rod),
            'TBU - shoe head': head, 'TBU - brake shoe': shoe}


def _rot(s, deg):
    return s.rotate(cq.Vector(CX, 0, CZ), cq.Vector(CX, 1, CZ), deg)


def state(parts, clamp=1.0, lift=0.0, angle=0.0, pins_out=False, with_tbu=True):
    """Kembalikan {nama: shape} untuk satu kondisi.
    clamp: 0 = rahang terbuka, 1 = rahang menjepit TBU; lift: TBU diangkat (mm);
    angle: sudut putar kedua piringan (derajat); pins_out: pin index ditarik."""
    d = CLAMP_TRAVEL * clamp
    out = {}
    for n, s in parts.items():
        if n.startswith(MOVING):
            s = s.translate(AX * (-d if 'atas' in n else d))
        if pins_out and n.startswith(('Pin index', 'Knob pin index')):
            s = s.translate(cq.Vector(-PIN_PULL if 'bawah' in n else PIN_PULL, 0, 0))
        if angle and not n.startswith(FIXED):
            s = _rot(s, angle)
        out[n] = s
    if with_tbu:
        for n, s in build_tbu().items():
            s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), VISE_TILT)  # sejajar sumbu ragum
            s = s.translate(cq.Vector(CX, Y_DISC1_TOP + lift, CZ))
            out[n] = _rot(s, angle) if angle else s
    return out


COLORS = {'TBU - brake shoe': (0.30, 0.22, 0.16), 'TBU - shoe head': (0.45, 0.47, 0.50)}
def color_of(n):
    if n in COLORS: return COLORS[n]
    if n.startswith('TBU'): return (0.22, 0.40, 0.62)
    if n.startswith('Piringan bawah'): return (0.78, 0.18, 0.15)
    if n.startswith('Piringan'): return (0.10, 0.10, 0.11)
    if n.startswith('Base'): return (0.62, 0.66, 0.70)
    if 'UHMW' in n: return (0.96, 0.96, 0.92)
    if 'Bushing' in n: return (0.80, 0.55, 0.22)
    if 'index' in n: return (0.20, 0.45, 0.80)
    if n.startswith('Replika'): return (0.80, 0.72, 0.58)
    return (0.68, 0.68, 0.66)


def write_step(shapes, path):
    doc = TDocStd_Document(TCollection_ExtendedString('XmlOcaf'))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    root = st.NewShape(); TDataStd_Name.Set_s(root, TCollection_ExtendedString('JigTBU_rev2 + TBU'))
    for n, s in shapes.items():
        lab = st.AddShape(s.wrapped, False); TDataStd_Name.Set_s(lab, TCollection_ExtendedString(n.rstrip("'")))
        ct.SetColor(lab, Quantity_Color(*color_of(n), Quantity_TOC_RGB), XCAFDoc_ColorSurf)
        comp = st.AddComponent(root, lab, TopLoc_Location())
        TDataStd_Name.Set_s(comp, TCollection_ExtendedString(n.rstrip("'")))
    st.UpdateAssemblies()
    Interface_Static.SetCVal_s('write.step.schema', 'AP214')
    w = STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True)
    w.Transfer(doc, STEPControl_AsIs); w.Write(path)


if __name__ == '__main__':
    parts = read_parts()
    shapes = state(parts, clamp=1.0)
    write_step(shapes, DST)
    print('langkah rahang = %.1f mm per sisi ->' % CLAMP_TRAVEL, os.path.abspath(DST))
