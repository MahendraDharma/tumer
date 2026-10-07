"""Tambah piringan bawah (turntable kedua) ke assembly jig agar ragum ikut berputar.

Input : Ver3 Jig Assembly ragum tetap.step
Output: Ver4 Jig Assembly ragum putar.step

Susunan baru (sumbu Y = atas, satuan mm):
  Base (tetap) -> Ring UHMW (tetap) -> Piringan bawah (BARU, Ø880x20, berputar)
  -> Ring UHMW atas (BARU, salinan) -> Piringan utama + kedua dudukan ragum (naik 22 mm)
Pin center diperpanjang 22 mm agar menembus bushing kedua piringan.

Jalankan: python3 tools/tambah_piringan_bawah.py   (butuh `pip install cadquery`)
"""
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

UP = cq.Vector(0, 1, 0)
# Tetap di tempat: Ring UHMW asli kini menopang piringan bawah, Pin center tetap dibaut ke Base
FIXED = {"Base (rev)", "Replika workbench", "Ring UHMW", "Pin center"}


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
    return d.clean()


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

    # Pin center: tetap dibaut di Base, poros Ø40 diperpanjang DY agar tetap masuk bushing piringan utama
    pin_c, _ = by_name["Pin center"]
    pin_world = st.GetShape_s(by_name["Pin center"][1]).Moved(st.GetLocation_s(pin_c))
    pin_new = cq.Shape.cast(pin_world).fuse(cyl(20.0, Y_PIN_TOP - 0.5, Y_PIN_TOP + DY)).clean()
    pin_col = color_of("Pin center")
    st.RemoveComponent(pin_c)
    st.RemoveShape(by_name["Pin center"][1], True)  # jangan tinggalkan Pin center lama sebagai body lepas
    del world["Pin center"]
    add_part("Pin center (panjang)", pin_new.wrapped, pin_col)

    add_part("Ring UHMW atas", world["Ring UHMW"].Moved(TopLoc_Location(shift)), color_of("Ring UHMW"))

    add_part("Piringan bawah", build_lower_disc(world["Base (rev)"]).wrapped, color_of("Piringan (baru)"))
    add_part("Bushing perunggu bawah", build_bushing().wrapped, color_of("Bushing perunggu"))
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
