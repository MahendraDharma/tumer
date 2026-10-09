"""Tambah piringan bawah (turntable kedua) ke assembly jig agar ragum ikut berputar.

Input : Ver3 Jig Assembly ragum tetap.step
Output: Ver4 Jig Assembly ragum putar.step

Susunan baru (sumbu Y = atas, satuan mm), dirampingkan ke faktor keamanan >= 2:
  Meja kerja -> Base (plat bulat Ø900x5, 8 baut benam M8) -> Ring UHMW 5 mm + 8 bantalan UHMW 5 mm
  di bawah ujung piringan (ragum tidak mengambang) -> Piringan bawah (BARU, plat 19 mm,
  lingkaran Ø880 dipangkas jadi lajur 600 mm, ujung di bawah dudukan 360 mm) -> Ring UHMW atas 3 mm (di
  cekungan 1 mm) -> Piringan utama + kedua dudukan ragum (naik DY = 9 mm terhadap Ver3).
  Alas TBU (muka atas piringan utama) = 49 mm di atas meja kerja (REQ-02: <= 50 mm).

Kunci kedua piringan dari samping: pin masuk dari tepi piringan, lurus ke tengah, dan ujungnya
masuk ke lubang silang di Pin center (diam). Tarik pin agar piringan bisa diputar.
  - Piringan utama: Pin index asli diperpanjang ke dalam (knob tetap di tempatnya).
  - Piringan bawah: Pin index bawah (batang Ø10) + salinan Knob pin index, di sisi -X.
Pin center diperpanjang sampai rata muka atas piringan utama dan diberi 2 lubang silang (sumbu X).

Jalankan: python3 tools/tambah_piringan_bawah.py   (butuh `pip install cadquery`)
"""
import math
import os
import sys

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_ChildIterator, TDF_Label, TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.XCAFDoc import XCAFDoc_ColorGen, XCAFDoc_ColorSurf, XCAFDoc_DocumentTool, XCAFDoc_Location
from OCP.gp import gp_Trsf, gp_Vec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Ver3 Jig Assembly ragum tetap.step")
DST = os.path.join(ROOT, "Ver4 Jig Assembly ragum putar.step")

# Sumbu putar & level Ver3 (eksak dari geometri)
CX, CZ = 505.21, -111.927
V3_BASE_TOP = 288.3205      # muka atas Base Ver3 (dudukan ragum duduk di sini)
V3_DISC1_BOT = 290.3205     # dasar piringan utama Ver3 (= muka atas Ring UHMW di kantong Base)
V3_DISC1_TOP = 308.3205     # muka atas piringan utama Ver3
V3_PIN1 = 299.3205          # sumbu Pin index piringan utama Ver3
V3_PINC_BOT = 278.3205      # dasar flens Pin center Ver3
V3_POCKET_D = 10.0          # kantong Ring UHMW di Base Ver3
R_DISC1 = 230.0

# Susunan baru
Y_TABLE = V3_BASE_TOP - 20.0                 # muka atas meja kerja = dasar Base
T_BASE = 5.0                                 # Base ditopang penuh oleh meja kerja
T_RING, T_RING2, RECESS = 5.0, 3.0, 1.0      # ring UHMW bawah, ring UHMW atas, cekungan ring atas
T_DISC = 19.0                                # piringan bawah (SF >= 2 terhadap momen jepit ragum; 18 mm hanya 1,87)
R_DISC, HALF_W = 440.0, 300.0                # lingkaran Ø880 dipangkas jadi lajur 600 mm (|x| <= 300)
END_Z, END_HALF = 270.0, 180.0               # di bawah dudukan (|z| > 270, lewat baris baut dalam): lebar 360 mm
RING_RI, RING_RO = 150.0, 232.0
Y_BASE_TOP = Y_TABLE + T_BASE
Y_RING_TOP = Y_BASE_TOP + T_RING             # dasar piringan bawah
Y_TOP = Y_RING_TOP + T_DISC                  # muka atas piringan bawah = tempat dudukan ragum
DY = round(Y_TOP - V3_BASE_TOP, 4)           # = 9: kenaikan piringan utama + kedua ragum terhadap Ver3
FLANGE_CB = 2.0                              # cekungan bawah piringan bawah di atas flens Pin center

# Kunci samping: lubang radial Ø10,5 (sama dengan piringan utama), ujung pin masuk ke Pin center
IDX_R, PIN_R, PIN_TIP = 5.25, 5.0, 8.0       # ujung pin di r = 8 mm (12 mm di dalam Pin center)
Y_LOCK = Y_RING_TOP + T_DISC / 2             # sumbu pin bawah: tengah tebal piringan bawah
Y_LOCK1 = V3_PIN1 + DY                       # sumbu pin piringan utama setelah dinaikkan

# Base: plat bulat Ø900 menutup seluruh area putar; diikat ke meja dengan 8 baut benam M8 (rata permukaan,
# tidak tertabrak piringan bawah yang lewat 5 mm di atasnya)
R_BASE = 450.0
MOUNT_R, MOUNT_ANG = 420.0, [22.5 + 45 * k for k in range(8)]
# 8 bantalan UHMW di bawah ujung piringan bawah (tempat ragum), tebal sama dengan ring dalam
PAD_R0, PAD_R1, PAD_W, PAD_ANG = 295.0, 365.0, 60.0, [45 * k for k in range(8)]

UP = cq.Vector(0, 1, 0)
# Tidak ikut dinaikkan DY (Base, ring bawah, dan Pin center dibuat ulang di posisi barunya)
FIXED = {"Base (rev)", "Replika workbench", "Ring UHMW", "Pin center"}


def cyl(r, y0, y1, x=CX, z=CZ):
    return cq.Solid.makeCylinder(r, y1 - y0, cq.Vector(x, y0, z), UP)


def radial_holes(shape, y, r0, r1, n=8):
    """n lubang radial Ø10,5 (tiap 360/n derajat) dari r0 sampai r1 pada ketinggian y."""
    for k in range(n):
        a = math.radians(360 / n * k)
        u = cq.Vector(math.cos(a), 0, math.sin(a))
        shape = shape.cut(cq.Solid.makeCylinder(IDX_R, r1 - r0, cq.Vector(CX, y, CZ) + u * r0, u))
    return shape


def base_holes(base):
    """Lubang tap vertikal Base Ver3: (x, z, r, jarak muka dari atas Base, kedalaman)."""
    holes = set()
    for f in cq.Shape.cast(base).Faces():
        if f.geomType() != "CYLINDER":
            continue
        c = BRepAdaptor_Surface(f.wrapped).Cylinder()
        if abs(c.Axis().Direction().Y()) < 0.99 or round(c.Radius(), 2) not in (2.5, 5.1):
            continue
        bb = f.BoundingBox()
        top = V3_BASE_TOP if bb.ymax > V3_BASE_TOP - 0.01 else V3_BASE_TOP - V3_POCKET_D
        holes.add((round(c.Location().X(), 4), round(c.Location().Z(), 4), c.Radius(),
                   round(V3_BASE_TOP - top, 4), round(top - bb.ymin, 4)))
    return sorted(holes)


def polar(r, deg):
    a = math.radians(deg)
    return CX + r * math.cos(a), CZ + r * math.sin(a)


def csk(shape, x, z, y_top, r_hole, r_head):
    """Lubang tembus + benaman 90° dari muka atas (untuk baut kepala benam)."""
    shape = shape.cut(cyl(r_hole, y_top - 30, y_top + 1, x, z))
    return shape.cut(cq.Solid.makeCone(r_head, r_hole, r_head - r_hole, cq.Vector(x, y_top, z), cq.Vector(0, -1, 0)))


def build_base(base):
    """Base plat bulat Ø900xT_BASE: 8 lubang benam M8 ke meja kerja, 4 tap M6 Ring UHMW dan 4 tap M6 flens
    Pin center (posisi sama dengan Base Ver3), 8 tap M6 bantalan UHMW."""
    y0, y1 = Y_TABLE, Y_TABLE + T_BASE
    b = cyl(R_BASE, y0, y1)
    for a in MOUNT_ANG:
        b = csk(b, *polar(MOUNT_R, a), y1, 4.5, 8.25)
    for a in PAD_ANG:
        b = b.cut(cyl(2.5, y0 - 1, y1 + 1, *polar((PAD_R0 + PAD_R1) / 2, a)))
    for x, z, r, dtop, depth in base_holes(base):
        if r < 3:                                              # tap M6 (bor Ø5): ring UHMW & flens Pin center
            b = b.cut(cyl(r, y0 - 1, y1 + 1, x, z))
    return b.clean()


def ring(y0, t, screws=()):
    r = cyl(RING_RO, y0, y0 + t).cut(cyl(RING_RI, y0 - 1, y0 + t + 1))
    for x, z in screws:                                        # baut L M6, kepala tenggelam
        r = r.cut(cyl(3.3, y0 - 1, y0 + t + 1, x, z)).cut(cyl(5.5, y0 + t - 3.5, y0 + t + 1, x, z))
    return r.clean()


def build_pad(deg):
    rm = (PAD_R0 + PAD_R1) / 2
    p = cq.Solid.makeBox(PAD_R1 - PAD_R0, T_RING, PAD_W, cq.Vector(CX + PAD_R0, Y_BASE_TOP, CZ - PAD_W / 2))
    p = csk(p, CX + rm, CZ, Y_BASE_TOP + T_RING, 3.3, 6.2)
    return p.rotate(cq.Vector(CX, 0, CZ), cq.Vector(CX, 1, CZ), -deg).clean()


def build_lower_disc(base):
    d = cyl(R_DISC, Y_RING_TOP, Y_TOP)
    d = d.intersect(cq.Solid.makeBox(2 * HALF_W, T_DISC + 2, 2 * R_DISC + 2,
                                     cq.Vector(CX - HALF_W, Y_RING_TOP - 1, CZ - R_DISC - 1)))  # lajur 600 mm
    for sz in (1, -1):                                                    # ujung di bawah dudukan: lebar 360 mm
        for sx in (1, -1):
            x0 = CX + sx * END_HALF if sx > 0 else CX - HALF_W - 1
            z0 = CZ + END_Z if sz > 0 else CZ - R_DISC - 1
            d = d.cut(cq.Solid.makeBox(HALF_W - END_HALF + 1, T_DISC + 2, R_DISC - END_Z + 1,
                                       cq.Vector(x0, Y_RING_TOP - 1, z0)))
    d = d.cut(cyl(25.0, Y_RING_TOP - 1, Y_TOP + 1))                       # lubang bushing Ø50
    d = d.cut(cyl(43.0, Y_RING_TOP - 1, Y_RING_TOP + FLANGE_CB))          # bebas flens Pin center
    d = d.cut(cyl(RING_RO + 0.5, Y_TOP - RECESS, Y_TOP + 1))              # cekungan ring UHMW atas
    for x, z, r, dtop, depth in base_holes(base):                         # 8x tap M12 dudukan ragum
        if r > 5:
            d = d.cut(cyl(r, Y_TOP - depth, Y_TOP + 1, x, z))
    return radial_holes(d, Y_LOCK, 24.0, R_DISC + 1).clean()


def build_bushing():
    y0 = Y_RING_TOP + FLANGE_CB
    b = cyl(25.0, y0, Y_TOP).cut(cyl(20.05, y0 - 1, Y_TOP + 1))
    return radial_holes(b, Y_LOCK, 19.0, 26.0).clean()


def name_of(lab):
    a = TDataStd_Name()
    return a.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), a) else ""


def volume(shape):
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, p)
    return p.Mass()


def main():
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    rd = STEPCAFControl_Reader()
    rd.SetNameMode(True)
    rd.SetColorMode(True)
    if rd.ReadFile(SRC) != IFSelect_RetDone or not rd.Transfer(doc):
        sys.exit("gagal membaca " + SRC)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    roots = TDF_LabelSequence()
    st.GetFreeShapes(roots)
    root = roots.Value(1)
    comps = TDF_LabelSequence()
    st.GetComponents_s(root, comps)

    TDataStd_Name.Set_s(root, TCollection_ExtendedString("JigTBU_rev2"))  # nama asli di Ver3
    shift = gp_Trsf()
    shift.SetTranslation(gp_Vec(0, DY, 0))
    by_name, world = {}, {}
    for i in range(1, comps.Length() + 1):
        c = comps.Value(i)
        ref = TDF_Label()
        st.GetReferredShape_s(c, ref)
        nm = name_of(ref)
        by_name[nm] = (c, ref)
        loc = st.GetLocation_s(c)
        if nm not in FIXED:
            loc = TopLoc_Location(shift).Multiplied(loc)
            XCAFDoc_Location.Set_s(c, loc)
        world[nm] = st.GetShape_s(ref).Moved(loc)

    def color_of(nm):
        # Warna dari Fusion biasanya menempel di label part atau di sub-shape (body/face)
        col = Quantity_Color()
        comp, ref = by_name[nm]
        labs = [ref, comp]
        it = TDF_ChildIterator(ref, True)
        while it.More():
            labs.append(it.Value())
            it.Next()
        for lab in labs:
            if ct.GetColor_s(lab, XCAFDoc_ColorSurf, col) or ct.GetColor_s(lab, XCAFDoc_ColorGen, col):
                return col
        return None

    def add_part(nm, shape, col):
        lab = st.AddShape(shape, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(nm))
        if col is not None:
            ct.SetColor(lab, col, XCAFDoc_ColorSurf)
        comp = st.AddComponent(root, lab, TopLoc_Location())
        TDataStd_Name.Set_s(comp, TCollection_ExtendedString(nm + ":1"))
        world[nm] = shape

    def replace_part(old, new_name, shape):
        col = color_of(old)
        comp, ref = by_name[old]
        st.RemoveComponent(comp)
        st.RemoveShape(ref, True)  # jangan tinggalkan part lama sebagai body lepas
        del world[old]
        add_part(new_name, shape, col)

    def baked(shape):  # geometri baru tanpa TopLoc_Location, agar tiap part jadi satu produk bernama di STEP
        return BRepBuilderAPI_Transform(shape.Located(TopLoc_Location()), shape.Location().Transformation(), True).Shape()

    def solid(nm):
        return cq.Shape.cast(baked(world[nm]))

    def bake(s):
        return baked(s.wrapped)

    lower_disc = build_lower_disc(world["Base (rev)"])

    # Pin center: tetap dibaut di Base; poros Ø40 diperpanjang sampai rata muka atas piringan utama,
    # + 2 lubang silang (sumbu X) penerima ujung pin kedua piringan
    pin_c = solid("Pin center").translate(cq.Vector(0, Y_BASE_TOP - V3_PINC_BOT, 0))   # flens di atas Base
    pin_c = pin_c.fuse(cyl(20.0, Y_BASE_TOP + 20, V3_DISC1_TOP + DY))
    for y in (Y_LOCK, Y_LOCK1):
        pin_c = pin_c.cut(cq.Solid.makeCylinder(IDX_R, 60, cq.Vector(CX - 30, y, CZ), cq.Vector(1, 0, 0)))
    replace_part("Pin center", "Pin center (panjang)", bake(pin_c.clean()))

    # Piringan utama + bushing-nya: 8 lubang radial diteruskan sampai lubang tengah
    replace_part("Piringan (baru)", "Piringan (baru)",
                 bake(radial_holes(solid("Piringan (baru)"), Y_LOCK1, 24.0, R_DISC1 + 1).clean()))
    replace_part("Bushing perunggu", "Bushing perunggu",
                 bake(radial_holes(solid("Bushing perunggu"), Y_LOCK1, 19.0, 26.0).clean()))

    # Pin index asli diperpanjang ke dalam sampai ujungnya masuk ke Pin center (knob tetap)
    pin1, pin_col = solid("Pin index"), color_of("Pin index")
    ext = cq.Solid.makeCylinder(PIN_R, pin1.BoundingBox().xmin - CX - PIN_TIP + 0.5,
                                cq.Vector(CX + PIN_TIP, Y_LOCK1, CZ), cq.Vector(1, 0, 0))
    replace_part("Pin index", "Pin index (panjang)", bake(pin1.fuse(ext).clean()))

    screws = [(x, z) for x, z, r, dt, dp in base_holes(world["Base (rev)"]) if r < 3 and (x - CX) ** 2 + (z - CZ) ** 2 > 60 ** 2]
    replace_part("Ring UHMW", "Ring UHMW", bake(ring(Y_BASE_TOP, T_RING, screws)))
    add_part("Ring UHMW atas", ring(Y_TOP - RECESS, T_RING2).wrapped, color_of("Ring UHMW"))
    add_part("Piringan bawah", lower_disc.wrapped, color_of("Piringan (baru)"))
    add_part("Bushing perunggu bawah", build_bushing().wrapped, color_of("Bushing perunggu"))

    # Kunci piringan bawah (sisi -X): batang Ø10 dari Pin center sampai tepi + salinan knob asli
    pin2 = cq.Solid.makeCylinder(PIN_R, HALF_W + 0.1 - PIN_TIP, cq.Vector(CX - PIN_TIP, Y_LOCK, CZ), cq.Vector(-1, 0, 0))
    add_part("Pin index bawah", pin2.wrapped, pin_col)
    knob = solid("Knob pin index").rotate(cq.Vector(CX, 0, CZ), cq.Vector(CX, 1, CZ), 180)
    knob = knob.translate(cq.Vector(-(HALF_W - R_DISC1), Y_LOCK - Y_LOCK1, 0))
    add_part("Knob pin index bawah", bake(knob), color_of("Knob pin index"))

    # Base Ø900x5 di bawah seluruh area putar + 8 bantalan UHMW di bawah ujung piringan
    replace_part("Base (rev)", "Base (rev)", bake(build_base(world["Base (rev)"])))
    for k, a in enumerate(PAD_ANG, 1):
        add_part(f"Bantalan UHMW {k}", bake(build_pad(a)), color_of("Ring UHMW"))
    st.UpdateAssemblies()

    # Cek tabrakan antar part
    clash = []
    names = list(world)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} <= FIXED or (a.startswith(("Stud", "Mur")) and b.startswith(("Stud", "Mur"))):
                continue  # ulir stud-mur memang dimodelkan saling tumpang (sudah begitu di Ver3)
            v = volume(BRepAlgoAPI_Common(world[a], world[b]).Shape())
            if v > 50.0:  # abaikan sentuhan muka datar
                clash.append((a, b, v))
    for a, b, v in clash:
        print(f"  overlap {a} x {b}: {v:.0f} mm3")

    wr = STEPCAFControl_Writer()
    wr.SetNameMode(True)
    wr.SetColorMode(True)
    wr.Transfer(doc, STEPControl_AsIs)
    if wr.Write(DST) != IFSelect_RetDone:
        sys.exit("gagal menulis " + DST)
    print("DY =", DY, "| alas TBU di atas meja =", round(V3_DISC1_TOP + DY - Y_TABLE, 2), "mm ->", DST)


if __name__ == "__main__":
    main()
