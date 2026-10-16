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
DST_TBU = os.path.join(HERE, '..', 'TBU Nabtesco 3.5-1R (model).step')

CX, CZ = 505.21, -111.927
Y_DISC1_TOP = 318.3205            # muka atas piringan utama = alas TBU
TBU_L, TBU_W = 510.0, 206.0       # panjang (melintang) x lebar (arah jepit ragum)
TBU_Y0 = 0.5                      # kedua kaki alas TBU 0,5 mm di atas piringan utama
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


def _prism(pts, z0, z1):
    """Profil XY (x = panjang, y = tinggi) diekstrusi sepanjang z (lebar)."""
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(z1 - z0).val()


def _hex(x, y, z0, z1, d):
    return cq.Workplane("XY", origin=(x, y, z0)).polygon(6, d).extrude(z1 - z0).val()


def build_tbu():
    """TBU Nabtesco 3.5/1R disederhanakan dari foto samping berpenggaris (±0,65 mm/piksel) dan foto isometri.
    Koordinat lokal: x = panjang (+ ke ujung shoe head), y = tinggi dari alas, z = lebar/arah jepit ragum
    (+ = sisi depan dengan tutup bundar & nameplate). Bukan geometri asli."""
    hw = TBU_W / 2
    # Badan cor: kaki kiri dan kaki kanan rata (y = 0) dengan lengkung cekung ±35 mm di antaranya (tempat
    # balok kayu); sisi atas turun miring dari bahu (dudukan pivot tuas di samping silinder) ke ujung kanan,
    # yang berupa muka tegak tempat poros penyetel keluar.
    arch = [(-100 + 200 * k / 12, 35 * math.sin(math.pi * k / 12)) for k in range(13)]
    corner = [(-188 + 12 * math.cos(math.radians(t)), 12 + 12 * math.sin(math.radians(t))) for t in range(180, 271, 30)]
    body = _prism([(-200, 140)] + corner + arch + [(245, 0), (245, 125), (-10, 205), (-38, 245),
                   (-75, 245), (-75, 140)], -hw, hw)
    # sudut depan-bawah ujung kanan dipotong miring (garis miring di foto samping); muka ujung tetap tegak
    body = body.cut(_prism([(135, -1), (246, -1), (246, 112)], 35, hw + 1))
    for x, y, r in ((112, 117, 33),):                                  # dudukan tutup bundar (rata muka)
        body = body.cut(cq.Solid.makeCylinder(r, 3, cq.Vector(x, y, hw - 3), cq.Vector(0, 0, 1)))
    body = body.cut(box(158, 190, 63, 120, hw - 1.5, hw + 1))           # dudukan nameplate (tegak)
    flange = box(-265, -40, 133, 153, -hw, hw)                          # flens silinder (menjorok ke kiri)
    eye = cq.Solid.makeTorus(15, 4, cq.Vector(-224, 100, 0), cq.Vector(0, 0, 1)) \
        .fuse(cq.Solid.makeCylinder(5, 15, cq.Vector(-209, 100, 0), cq.Vector(1, 0, 0)))   # baut mata
    cyl = vcyl(90, 153, 286, -162, 0).fuse(vcyl(85, 286, 292, -162, 0))   # silinder rem + tutup atas
    pipe = vcyl(10, 292, 335, -222, -35).fuse(cq.Solid.makeSphere(14, cq.Vector(-222, 345, -35))) \
        .fuse(cq.Solid.makeCylinder(12, 32, cq.Vector(-222, 345, -35), cq.Vector(-1, 0, 0)))   # pipa siku
    fl_bolts = None
    for x in (-250, -55):
        for z in (-88, 88):
            b = cq.Workplane("XZ", origin=(x, 153, z)).polygon(6, 22).extrude(-10).val()
            fl_bolts = b if fl_bolts is None else fl_bolts.fuse(b)
    # Tuas: dari pivot (mur kuning) di bahu turun ke pin depan
    piv, pin1, pin2 = (-25, 232), (170, 178), (222, 188)
    arm = _prism([(-45, 250), (-5, 214), (182, 158), (160, 198)], -85, 85).cut(vcyl(90, 140, 320, -162, 0))
    pins = cq.Solid.makeCylinder(30, 2 * hw - 4, cq.Vector(piv[0], piv[1], -hw + 2), cq.Vector(0, 0, 1)) \
        .fuse(cq.Solid.makeCylinder(22, 2 * hw - 4, cq.Vector(pin1[0], pin1[1], -hw + 2), cq.Vector(0, 0, 1))) \
        .fuse(cq.Solid.makeCylinder(20, 2 * hw - 4, cq.Vector(pin2[0], pin2[1], -hw + 2), cq.Vector(0, 0, 1))) \
        .fuse(_hex(pin2[0], pin2[1], hw - 2, hw + 10, 30))
    gold = _hex(piv[0], piv[1], hw - 2, hw + 10, 36).fuse(_hex(pin1[0], pin1[1], hw - 2, hw + 8, 30))
    # Shoe head: memanjang di atas badan, menjorok melewati ujung kanan; alur di tengah memisah dua blok rem
    head = _prism([(0, 270), (150, 240), (150, 228), (200, 228), (200, 242), (285, 250), (290, 236),
                   (255, 222), (200, 205), (160, 196), (110, 210), (40, 240), (0, 255)], -80, 80)
    blocks = _prism([(0, 270), (150, 240), (150, 250), (0, 280)], -78, 78) \
        .fuse(_prism([(200, 242), (285, 250), (285, 260), (200, 252)], -78, 78))   # dua pelat blok rem
    slot = box(150, 200, 228, 230, -60, 60)                               # dasar alur (gelap)
    boot = cq.Solid.makeCylinder(32, 30, cq.Vector(120, 200, 0), cq.Vector(1, 0, 0))   # karet pelindung push rod
    cover = cq.Solid.makeCylinder(33, 2.5, cq.Vector(112, 117, hw - 3), cq.Vector(0, 0, 1))
    for a in (90, 210, 330):
        aa = math.radians(a)
        cover = cover.fuse(_hex(112 + 22 * math.cos(aa), 117 + 22 * math.sin(aa), hw - 0.5, hw + 4, 9))
    plate = box(159, 189, 64, 119, hw - 1.5, hw)
    rod = cq.Solid.makeCylinder(7, 50, cq.Vector(240, 40, -20), cq.Vector(1, 0, 0))   # poros penyetel manual
    return {'TBU - badan': body.fuse(flange).fuse(eye).clean(), 'TBU - silinder rem': cyl.fuse(pipe).clean(),
            'TBU - baut': fl_bolts.fuse(pins).clean(), 'TBU - baut kuning': gold.clean(),
            'TBU - lengan tuas': arm.clean(), 'TBU - shoe head': head.clean(), 'TBU - blok rem': blocks.clean(),
            'TBU - alur blok rem': slot, 'TBU - karet pelindung': boot,
            'TBU - tutup samping': cover.clean(), 'TBU - nameplate': plate, 'TBU - poros penyetel': rod}


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
            hub = cq.Vector(CX + sg * 7.66, 438.32, CZ + sg * 533.95)   # sumbu kepala batang ulir
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
            s = s.translate(cq.Vector(CX, Y_DISC1_TOP + TBU_Y0 + lift, CZ))
            out[n] = _rot(s, angle) if angle else s
    return out


COLORS = {'TBU - alur blok rem': (0.12, 0.12, 0.12), 'TBU - poros penyetel': (0.10, 0.10, 0.10),
          'TBU - blok rem': (0.32, 0.27, 0.23), 'TBU - karet pelindung': (0.08, 0.08, 0.08),
          'TBU - baut kuning': (0.85, 0.68, 0.25), 'TBU - baut': (0.86, 0.86, 0.84),
          'TBU - nameplate': (0.55, 0.62, 0.70), 'TBU - shoe head': (0.74, 0.75, 0.74),
          'TBU - lengan tuas': (0.76, 0.77, 0.76), 'TBU - tutup samping': (0.80, 0.81, 0.80)}
def color_of(n):
    if n in COLORS: return COLORS[n]
    if n.startswith('TBU'): return (0.84, 0.85, 0.84)
    if n.startswith('Thrust bearing'): return (0.93, 0.62, 0.10)
    if n.startswith('Washer'): return (0.50, 0.55, 0.66)
    if n.startswith('Piringan bawah'): return (0.78, 0.18, 0.15)
    if n.startswith('Piringan'): return (0.10, 0.10, 0.11)
    if n.startswith('Base'): return (0.62, 0.66, 0.70)
    if 'UHMW' in n: return (0.96, 0.96, 0.92)
    if 'Bushing' in n: return (0.80, 0.55, 0.22)
    if 'index' in n: return (0.20, 0.45, 0.80)
    if n.startswith('Replika'): return (0.80, 0.72, 0.58)
    return (0.68, 0.68, 0.66)


def write_step(shapes, path, root_name='JigTBU_rev2 + TBU'):
    doc = TDocStd_Document(TCollection_ExtendedString('XmlOcaf'))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    root = st.NewShape(); TDataStd_Name.Set_s(root, TCollection_ExtendedString(root_name))
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
    write_step(build_tbu(), DST_TBU, root_name='TBU Nabtesco 3.5-1R (model)')   # TBU saja, alas di y = 0
    print('TBU saja ->', os.path.abspath(DST_TBU))
