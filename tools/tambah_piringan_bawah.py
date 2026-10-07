"""Tambah piringan bawah (turntable kedua) ke assembly jig agar ragum ikut berputar.

Input : Ver3 Jig Assembly ragum tetap.step
Output: Ver4 Jig Assembly ragum putar.step

Susunan baru (sumbu Y = atas, satuan mm):
  Base (tetap) -> Ring UHMW (tetap) -> Piringan bawah (BARU, Ø880x20, berputar)
  -> Ring UHMW atas (BARU, salinan) -> Piringan utama + kedua dudukan ragum (naik 22 mm)
Pin center diperpanjang 22 mm agar menembus bushing kedua piringan.
Base (rev2): ditambah kantong Ring UHMW luar (penopang bagian luar piringan bawah) dan
8 lubang index Ø16 tiap 45° untuk Pin index bawah (pengunci piringan bawah ke Base).

Jalankan: python3 tools/tambah_piringan_bawah.py   (butuh `pip install cadquery`)
"""
import math
import os
import sys

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
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
Y_PIN_TOP = 305.3           # ujung atas poros Pin center
T_DISC = 20.0               # tebal piringan bawah (sama dengan Base)
R_DISC = 440.0              # Ø880: menutup seluruh tapak dudukan ragum (sudut terjauh r≈437)
POCKET_R, POCKET_D = 232.5, 10.0   # kantong Ring UHMW, sama dengan di Base
Y_TOP = Y_RING_TOP + T_DISC
DY = round(Y_TOP - Y_BASE_TOP, 4)  # = 22.0, kenaikan piringan utama + kedua ragum

# Penopang luar: ring UHMW kedua di Base, di dalam lebar Base (setengah lebar 375)
R_OUT_IN, R_OUT_OUT = 305.0, 355.0
R_OUT_SCREW = 330.0
# Pengunci piringan bawah: pin vertikal Ø16 di sisi -X, masuk 15 mm ke Base
R_IDX = 266.0               # di antara Ring UHMW dalam (r 232) dan ring luar (r 305)
PIN_R, HOLE_R = 8.0, 8.05
Y_BASE_BOT = 268.3205
BLOCK_H, BLOCK_X, BLOCK_Z, BLOCK_BOLT_DZ = 30.0, 40.0, 70.0, 25.0

UP = cq.Vector(0, 1, 0)
# Tetap di tempat: Ring UHMW asli kini menopang piringan bawah, Pin center tetap dibaut ke Base
FIXED = {"Base (rev)", "Replika workbench", "Ring UHMW", "Pin center", "Base (rev2)", "Ring UHMW luar"}


def cyl(r, y0, y1, x=CX, z=CZ):
    return cq.Solid.makeCylinder(r, y1 - y0, cq.Vector(x, y0, z), UP)


def base_holes(base):
    """Lubang tap vertikal di muka atas Base: (x, z, r, kedalaman dari muka atasnya)."""
    holes = set()
    for f in cq.Shape.cast(base).Faces():
        if f.geomType() != "CYLINDER":
            continue
        ad = BRepAdaptor_Surface(f.wrapped)
        c = ad.Cylinder()
        if abs(c.Axis().Direction().Y()) < 0.99 or round(c.Radius(), 2) not in (2.5, 3.4, 5.1):
            continue
        bb = f.BoundingBox()
        top = Y_BASE_TOP if bb.ymax > Y_BASE_TOP - 0.01 else Y_BASE_TOP - POCKET_D
        holes.add((round(c.Location().X(), 4), round(c.Location().Z(), 4), c.Radius(),
                   round(Y_BASE_TOP - top, 4), round(top - bb.ymin, 4)))
    return sorted(holes)


def build_lower_disc(base):
    d = cyl(R_DISC, Y_RING_TOP, Y_TOP)
    d = d.cut(cyl(25.0, Y_RING_TOP - 1, Y_TOP + 1))                       # lubang bushing Ø50
    d = d.cut(cyl(POCKET_R, Y_TOP - POCKET_D, Y_TOP + 1))                 # kantong Ring UHMW atas
    # Pola lubang disalin dari Base: 8x M12 dudukan ragum, 2x M8 Blok pin index,
    # 4x sekrup Ring UHMW (di dasar kantong). Lubang M6 flens Pin center tidak perlu.
    for x, z, r, dtop, depth in base_holes(base):
        if (x - CX) ** 2 + (z - CZ) ** 2 < 60 ** 2:
            continue
        y_face = Y_TOP - dtop
        d = d.cut(cyl(r, y_face - depth, y_face + 1, x, z))
    # lubang Pin index bawah (tembus) + 2x tap M8 untuk Blok pin index bawah
    x, z = polar(R_IDX, 180)
    d = d.cut(cyl(HOLE_R, Y_RING_TOP - 1, Y_TOP + 1, x, z))
    for dz in (-BLOCK_BOLT_DZ, BLOCK_BOLT_DZ):
        d = d.cut(cyl(3.4, Y_TOP - 15, Y_TOP + 1, x, z + dz))
    return d.clean()


def polar(r, deg):
    a = math.radians(deg)
    return CX + r * math.cos(a), CZ + r * math.sin(a)


def build_base(base):
    b = cq.Shape.cast(base)
    # kantong ring UHMW luar, sama dalamnya dengan kantong ring dalam
    b = b.cut(cyl(R_OUT_OUT + 0.5, Y_BASE_TOP - POCKET_D, Y_BASE_TOP + 1)
              .cut(cyl(R_OUT_IN - 0.5, Y_BASE_TOP - POCKET_D - 1, Y_BASE_TOP + 2)))
    for k in range(8):
        x, z = polar(R_OUT_SCREW, 22.5 + 45 * k)      # 8x tap M6 sekrup ring luar
        b = b.cut(cyl(2.5, Y_BASE_TOP - POCKET_D - 8, Y_BASE_TOP, x, z))
        x, z = polar(R_IDX, 45 * k)                   # 8x lubang index Ø16 tembus
        b = b.cut(cyl(HOLE_R, Y_BASE_BOT - 1, Y_BASE_TOP + 1, x, z))
    return b.clean()


def build_outer_ring():
    r = cyl(R_OUT_OUT, Y_BASE_TOP - POCKET_D, Y_RING_TOP).cut(cyl(R_OUT_IN, Y_BASE_TOP - 20, Y_RING_TOP + 1))
    for k in range(8):
        x, z = polar(R_OUT_SCREW, 22.5 + 45 * k)
        r = r.cut(cyl(3.3, Y_BASE_TOP - 20, Y_RING_TOP + 1, x, z))
    return r.clean()


def build_index_block():
    x, z = polar(R_IDX, 180)
    blk = cq.Solid.makeBox(BLOCK_X, BLOCK_H, BLOCK_Z,
                           cq.Vector(x - BLOCK_X / 2, Y_TOP, z - BLOCK_Z / 2))
    blk = blk.cut(cyl(HOLE_R, Y_TOP - 1, Y_TOP + BLOCK_H + 1, x, z))
    for dz in (-BLOCK_BOLT_DZ, BLOCK_BOLT_DZ):        # 2x baut M8
        blk = blk.cut(cyl(4.5, Y_TOP - 1, Y_TOP + BLOCK_H + 1, x, z + dz))
        blk = blk.cut(cyl(7.5, Y_TOP + BLOCK_H - 9, Y_TOP + BLOCK_H + 1, x, z + dz))
    return blk.clean()


def build_index_pin():
    x, z = polar(R_IDX, 180)
    y_top = Y_TOP + BLOCK_H + 20  # ruang angkat 20 > 15 mm masuk ke Base
    pin = cyl(PIN_R, Y_BASE_TOP - 15, y_top, x, z)
    knob = cyl(15.0, y_top, y_top + 15, x, z)
    return pin, knob


def build_bushing():
    return cyl(25.0, Y_RING_TOP, Y_TOP).cut(cyl(20.05, Y_RING_TOP - 1, Y_TOP + 1))


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

    TDataStd_Name.Set_s(root, TCollection_ExtendedString("Ver4 Jig Assembly ragum putar"))
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

    def remove_part(nm):
        comp, ref = by_name[nm]
        st.RemoveComponent(comp)
        st.RemoveShape(ref, True)  # jangan tinggalkan part lama sebagai body lepas
        del world[nm]

    # Pin center: tetap dibaut di Base, poros Ø40 diperpanjang DY agar tetap masuk bushing piringan utama
    pin_c, _ = by_name["Pin center"]
    pin_world = st.GetShape_s(by_name["Pin center"][1]).Moved(st.GetLocation_s(pin_c))
    pin_new = cq.Shape.cast(pin_world).fuse(cyl(20.0, Y_PIN_TOP - 0.5, Y_PIN_TOP + DY)).clean()
    pin_col = color_of("Pin center")
    remove_part("Pin center")
    add_part("Pin center (panjang)", pin_new.wrapped, pin_col)

    add_part("Ring UHMW atas", world["Ring UHMW"].Moved(TopLoc_Location(shift)), color_of("Ring UHMW"))

    add_part("Piringan bawah", build_lower_disc(world["Base (rev)"]).wrapped, color_of("Piringan (baru)"))
    add_part("Bushing perunggu bawah", build_bushing().wrapped, color_of("Bushing perunggu"))

    # Base diganti Base (rev2): + kantong ring luar + 8 lubang index (dibuat setelah pola lubang disalin)
    base_new, base_col = build_base(world["Base (rev)"]), color_of("Base (rev)")
    remove_part("Base (rev)")
    add_part("Base (rev2)", base_new.wrapped, base_col)
    add_part("Ring UHMW luar", build_outer_ring().wrapped, color_of("Ring UHMW"))
    pin, knob = build_index_pin()
    add_part("Blok pin index bawah", build_index_block().wrapped, color_of("Dudukan ragum atas"))
    add_part("Pin index bawah", pin.wrapped, color_of("Pin index"))
    add_part("Knob pin index bawah", knob.wrapped, color_of("Knob pin index"))
    st.UpdateAssemblies()

    # Cek tabrakan antar part baru/berpindah
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
