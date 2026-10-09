"""Tambah piringan bawah (turntable kedua) ke assembly jig agar ragum ikut berputar.

Input : Ver3 Jig Assembly ragum tetap.step
Output: Ver4 Jig Assembly ragum putar.step

Susunan baru (sumbu Y = atas, satuan mm):
  Base (plat 920x920x5, dijepit ke meja kerja) -> Ring UHMW (di atas Base) -> Piringan bawah (BARU,
  Ø880x30, berputar) -> Ring UHMW atas (salinan) -> Piringan utama + kedua dudukan ragum.
  Relatif terhadap Ver3: piringan utama & ragum naik DY = 32 mm, lalu semua part di atas Base turun
  BASE_DROP = 5 mm karena Base 20 -> 5 mm dan ring UHMW tidak lagi masuk kantong (10 mm).

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

# Sumbu putar & level, diambil eksak dari geometri Ver3
CX, CZ = 505.21, -111.927
Y_BASE_TOP = 288.3205       # muka atas Base (dulu dudukan ragum duduk di sini)
Y_RING_TOP = 290.3205       # muka atas Ring UHMW di Base (dulu dasar piringan utama)
Y_PIN_TOP = 305.3           # ujung atas poros Pin center di Ver3
Y_DISC1_TOP = 308.3205      # muka atas piringan utama di Ver3
Y_PIN1 = 299.3205           # sumbu Pin index piringan utama di Ver3
R_DISC1 = 230.0
T_DISC = 30.0               # tebal piringan bawah: 20 mm material di bawah kantong ring untuk lubang pin
R_DISC = 440.0              # Ø880: menutup seluruh tapak dudukan ragum (sudut terjauh r≈437)
POCKET_R, POCKET_D = 232.5, 10.0   # kantong Ring UHMW, sama dengan di Base
Y_TOP = Y_RING_TOP + T_DISC
DY = round(Y_TOP - Y_BASE_TOP, 4)  # = 32.0, kenaikan piringan utama + kedua ragum

# Kunci samping: lubang radial Ø10,5 (sama dengan piringan utama), ujung pin masuk ke Pin center
IDX_R, PIN_R, PIN_TIP = 5.25, 5.0, 8.0          # ujung pin di r = 8 mm (12 mm di dalam Pin center)
Y_LOCK = Y_RING_TOP + (T_DISC - POCKET_D) / 2   # sumbu pin bawah: tengah material di bawah kantong
Y_LOCK1 = Y_PIN1 + DY                            # sumbu pin piringan utama setelah dinaikkan

# Base baru: persegi R100 yang menutup penuh piringan bawah + 20 mm
BASE_HALF, BASE_RC = R_DISC + 20.0, 100.0
BASE_OLD = (130.2205, 880.2205, -516.927, 293.073)  # X0, X1, Z0, Z1 Base Ver3 (sudut R100)
T_BASE = 5.0                                  # tebal Base baru (plat ditopang penuh oleh meja kerja)
Y_TABLE = Y_BASE_TOP - 20.0                   # muka atas meja kerja = dasar Base
BASE_DROP = 20.0 - T_BASE - POCKET_D          # = 5: Base 15 mm lebih tipis, ring naik 10 mm keluar kantong
MOUNT_HOLES = [(230.2205, 163.073), (780.2205, 163.073), (230.2205, -386.927), (780.2205, -386.927)]  # Ø40 ke meja

UP = cq.Vector(0, 1, 0)
# Tetap di tempat: Ring UHMW asli kini menopang piringan bawah, Pin center tetap dibaut ke Base
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


def rounded_slab(x0, x1, z0, z1, rc, y0, y1):
    h = y1 - y0
    s = cq.Solid.makeBox(x1 - x0 - 2 * rc, h, z1 - z0, cq.Vector(x0 + rc, y0, z0))
    s = s.fuse(cq.Solid.makeBox(x1 - x0, h, z1 - z0 - 2 * rc, cq.Vector(x0, y0, z0 + rc)))
    for x in (x0 + rc, x1 - rc):
        for z in (z0 + rc, z1 - rc):
            s = s.fuse(cq.Solid.makeCylinder(rc, h, cq.Vector(x, y0, z), UP))
    return s


def base_holes(base):
    """Lubang tap vertikal di muka atas Base: (x, z, r, kedalaman dari muka atasnya)."""
    holes = set()
    for f in cq.Shape.cast(base).Faces():
        if f.geomType() != "CYLINDER":
            continue
        c = BRepAdaptor_Surface(f.wrapped).Cylinder()
        if abs(c.Axis().Direction().Y()) < 0.99 or round(c.Radius(), 2) not in (2.5, 5.1):
            continue
        bb = f.BoundingBox()
        top = Y_BASE_TOP if bb.ymax > Y_BASE_TOP - 0.01 else Y_BASE_TOP - POCKET_D
        holes.add((round(c.Location().X(), 4), round(c.Location().Z(), 4), c.Radius(),
                   round(Y_BASE_TOP - top, 4), round(top - bb.ymin, 4)))
    return sorted(holes)


def build_base(base):
    """Base plat 920x920xT_BASE R100 tanpa kantong: 4 lubang Ø40 ke meja kerja, 4 tap M6 ring UHMW,
    4 tap M6 flens Pin center (posisi sama dengan Base Ver3). Lubang lain Ver3 tidak dipakai lagi."""
    y0, y1 = Y_TABLE, Y_TABLE + T_BASE
    b = rounded_slab(CX - BASE_HALF, CX + BASE_HALF, CZ - BASE_HALF, CZ + BASE_HALF, BASE_RC, y0, y1)
    for x, z in MOUNT_HOLES:
        b = b.cut(cyl(20.0, y0 - 1, y1 + 1, x, z))
    for x, z, r, dtop, depth in base_holes(base):
        if r < 3:                                              # tap M6 (bor Ø5): ring UHMW & flens Pin center
            b = b.cut(cyl(r, y0 - 1, y1 + 1, x, z))
    return b.clean()


def build_lower_disc(base):
    d = cyl(R_DISC, Y_RING_TOP, Y_TOP)
    d = d.cut(cyl(25.0, Y_RING_TOP - 1, Y_TOP + 1))                       # lubang bushing Ø50
    d = d.cut(cyl(POCKET_R, Y_TOP - POCKET_D, Y_TOP + 1))                 # kantong Ring UHMW atas
    # Pola lubang disalin dari Base: 8x M12 dudukan ragum, 4x sekrup Ring UHMW (di dasar kantong).
    for x, z, r, dtop, depth in base_holes(base):
        if (x - CX) ** 2 + (z - CZ) ** 2 < 60 ** 2:                      # lubang flens Pin center
            continue
        y_face = Y_TOP - dtop
        d = d.cut(cyl(r, y_face - depth, y_face + 1, x, z))
    return radial_holes(d, Y_LOCK, 24.0, R_DISC + 1).clean()


def build_bushing():
    b = cyl(25.0, Y_RING_TOP, Y_TOP).cut(cyl(20.05, Y_RING_TOP - 1, Y_TOP + 1))
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
    pin_c = solid("Pin center").fuse(cyl(20.0, Y_PIN_TOP - 0.5, Y_DISC1_TOP + DY))
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

    add_part("Ring UHMW atas", world["Ring UHMW"].Moved(TopLoc_Location(shift)), color_of("Ring UHMW"))
    add_part("Piringan bawah", lower_disc.wrapped, color_of("Piringan (baru)"))
    add_part("Bushing perunggu bawah", build_bushing().wrapped, color_of("Bushing perunggu"))

    # Kunci piringan bawah (sisi -X): batang Ø10 dari Pin center sampai tepi + salinan knob asli
    pin2 = cq.Solid.makeCylinder(PIN_R, R_DISC + 0.1 - PIN_TIP, cq.Vector(CX - PIN_TIP, Y_LOCK, CZ), cq.Vector(-1, 0, 0))
    add_part("Pin index bawah", pin2.wrapped, pin_col)
    knob = solid("Knob pin index").rotate(cq.Vector(CX, 0, CZ), cq.Vector(CX, 1, CZ), 180)
    knob = knob.translate(cq.Vector(-(R_DISC - R_DISC1), Y_LOCK - Y_LOCK1, 0))
    add_part("Knob pin index bawah", bake(knob), color_of("Knob pin index"))

    # Base 920x920x5 menutup penuh piringan bawah; semua part di atasnya turun BASE_DROP
    replace_part("Base (rev)", "Base (rev)", bake(build_base(world["Base (rev)"])))
    down = gp_Trsf()
    down.SetTranslation(gp_Vec(0, -BASE_DROP, 0))
    comps = TDF_LabelSequence()
    st.GetComponents_s(root, comps)
    for i in range(1, comps.Length() + 1):
        c = comps.Value(i)
        ref = TDF_Label()
        st.GetReferredShape_s(c, ref)
        nm = name_of(ref)
        if nm in ("Base (rev)", "Replika workbench"):
            continue
        XCAFDoc_Location.Set_s(c, TopLoc_Location(down).Multiplied(st.GetLocation_s(c)))
    for nm in list(world):
        if nm not in ("Base (rev)", "Replika workbench"):
            world[nm] = world[nm].Moved(TopLoc_Location(down))
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
    print("DY =", DY, "->", DST)


if __name__ == "__main__":
    main()
