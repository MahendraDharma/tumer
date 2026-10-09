"""Visualisasi cara pakai jig: TBU (model sederhana) dijepit kedua ragum di atas piringan utama.

Input : Ver4 Jig Assembly ragum putar.step
Output: Ver4 Jig + TBU terjepit.step   (kondisi terjepit, sudut 0°)

Model TBU disederhanakan (envelope, bukan geometri asli): panjang ±500 mm, lebar ±206 mm
(Nabtesco 152-3.5, lebar dari gambar Section A-A). Ragum menjepit sisi LEBAR TBU; panjangnya
melintang di atas piringan utama. Muka mounting (4 x M20, pola 114 x 250) menghadap ke bawah.

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
TBU_L, TBU_W = 500.0, 206.0       # panjang (melintang) x lebar (arah jepit ragum)
VISE_TILT = math.degrees(math.atan2(0.0143, 0.9999))  # sumbu kedua ragum di Ver3 miring ±0,82° terhadap Z
AX = cq.Vector(math.sin(math.radians(VISE_TILT)), 0, math.cos(math.radians(VISE_TILT)))
JAW_FACE = 232.0                  # jarak muka rahang (terbuka) ke sumbu jig, sepanjang sumbu ragum
CLAMP_TRAVEL = JAW_FACE - TBU_W / 2 - 0.2  # langkah tiap rahang sampai menyentuh TBU (±129 mm)
HANDLE_ROT = 90.0                 # T-handle diputar mendatar; menghadap bawah ia menabrak dudukan ragum
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
    """TBU sederhana di koordinat lokal (x = panjang, y = atas dari alas, z = lebar/arah jepit)."""
    hl, hw = TBU_L / 2, TBU_W / 2
    body = box(-150, 150, 0, 180, -hw, hw)                     # flens mounting + housing utama
    for sx in (-125, 125):
        for sz in (-57, 57):
            body = body.cut(vcyl(11, -1, 25, sx, sz))           # 4 lubang mounting M20 (114 x 250)
    cyl = cq.Solid.makeCylinder(95, hl - 150, cq.Vector(-150, 100, 0), cq.Vector(-1, 0, 0))  # silinder rem
    cover = cq.Solid.makeCylinder(70, 12, cq.Vector(-hl + 12, 100, 0), cq.Vector(-1, 0, 0))
    lever = box(150, hl, 20, 200, -60, 60)
    rod = vcyl(18, 180, 262, 40, 0)
    head = box(-110, 110, 262, 300, -65, 65)
    shoe = box(-145, 145, 300, 372, -60, 60).cut(
        cq.Solid.makeCylinder(430, 200, cq.Vector(0, 775, -100), cq.Vector(0, 0, 1)))
    return {'TBU - housing': body, 'TBU - silinder rem': cyl.fuse(cover).cut(body),
            'TBU - housing lever': lever.fuse(rod).cut(body),
            'TBU - shoe head': head, 'TBU - brake shoe': shoe}


def _rot(s, deg):
    return s.rotate(cq.Vector(CX, 0, CZ), cq.Vector(CX, 1, CZ), deg)


def state(parts, clamp=1.0, lift=0.0, angle=0.0, pins_out=False, with_tbu=True):
    """Kembalikan {nama: shape} untuk satu kondisi.
    clamp: 0 = rahang terbuka, 1 = rahang menjepit TBU; lift: TBU diangkat (mm);
    angle: sudut putar kedua piringan (derajat, kelipatan 45° bila pin terkunci); pins_out: pin index ditarik."""
    d = CLAMP_TRAVEL * clamp
    out = {}
    for n, s in parts.items():
        if n.startswith(('Handle', 'Vise Rod')) and HANDLE_ROT:   # batang ulir + T-handle berputar bersama
            sg = 1 if 'atas' in n else -1
            hub = cq.Vector(CX + sg * 7.66, 437.32, CZ + sg * 533.95)   # sumbu kepala batang ulir
            s = s.rotate(hub, hub + AX, HANDLE_ROT)
        if n.startswith(MOVING):
            s = s.translate(AX * (-d if 'atas' in n else d))
        if pins_out and n.startswith(('Pin index', 'Knob pin index')):
            s = s.translate(cq.Vector(-PIN_PULL if 'bawah' in n else PIN_PULL, 0, 0))
        # pin terkunci selalu di lubang silang Pin center (sumbu X); pin hanya ikut berputar saat ditarik
        pin = n.startswith(('Pin index', 'Knob pin index'))
        if angle and not n.startswith(FIXED) and (pins_out or not pin):
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
