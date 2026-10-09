"""Render gambar cara pakai (docs/langkah_penggunaan.png, docs/tbu_terjepit_keterangan.png).
Jalankan: python3 tools/render_visualisasi_tbu.py docs   (butuh cadquery, vtk, pillow)
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visualisasi_tbu import *
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.BRep import BRep_Tool
from OCP.TopoDS import TopoDS
import vtk
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]
P = read_parts()
W, H = 1500, 1100
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def actor(n, s):
    BRepMesh_IncrementalMesh(s.wrapped, 0.5, False, 0.3, True)
    pts = vtk.vtkPoints(); polys = vtk.vtkCellArray()
    e = TopExp_Explorer(s.wrapped, TopAbs_FACE)
    while e.More():
        f = TopoDS.Face_s(e.Current()); loc = TopLoc_Location(); t = BRep_Tool.Triangulation_s(f, loc)
        if t:
            tr = loc.Transformation(); off = pts.GetNumberOfPoints()
            for i in range(1, t.NbNodes() + 1):
                p = t.Node(i).Transformed(tr); pts.InsertNextPoint(p.X(), p.Y(), p.Z())
            rev = f.Orientation() == TopAbs_REVERSED
            for i in range(1, t.NbTriangles() + 1):
                a, b, c = t.Triangle(i).Get()
                if rev: b, c = c, b
                polys.InsertNextCell(3, [off + a - 1, off + b - 1, off + c - 1])
        e.Next()
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(polys)
    nm = vtk.vtkPolyDataNormals(); nm.SetInputData(pd); nm.SetFeatureAngle(35); nm.SplittingOn()
    mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(nm.GetOutputPort())
    ac = vtk.vtkActor(); ac.SetMapper(mp); pr = ac.GetProperty(); pr.SetColor(*color_of(n))
    pr.SetSpecular(0.25); pr.SetSpecularPower(20); pr.SetAmbient(0.25); pr.SetDiffuse(0.75)
    return ac

C = (CX, 400, CZ)
BOUNDS = (CX - 470, CX + 470, 268, 720, CZ - 590, CZ + 590)
ZOOM = 1.75
CAMS = {'iso': ((CX + 1250, 1250, CZ + 1050), C, 17.5)}

def render(shapes, cam='iso', size=(W, H), zoom=None):
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    for n, s in shapes.items():
        if n.startswith('Replika'): continue
        ren.AddActor(actor(n, s))
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren); rw.SetSize(*size)
    pos, fp, ang = CAMS[cam]
    c = ren.GetActiveCamera(); c.SetPosition(*pos); c.SetFocalPoint(*fp); c.SetViewUp(0, 1, 0); c.SetViewAngle(ang)
    ren.ResetCamera(BOUNDS); c.Zoom(zoom or ZOOM); ren.ResetCameraClippingRange(); rw.Render()
    w = vtk.vtkWindowToImageFilter(); w.SetInput(rw); w.Update()
    a = w.GetOutput(); dims = a.GetDimensions()
    from vtk.util.numpy_support import vtk_to_numpy
    arr = vtk_to_numpy(a.GetPointData().GetScalars()).reshape(dims[1], dims[0], -1)[::-1]
    img = Image.fromarray(arr[:, :, :3].copy())
    M = c.GetCompositeProjectionTransformMatrix(size[0] / size[1], -1, 1)
    def proj(p):
        v = [sum(M.GetElement(i, j) * q for j, q in enumerate((*p, 1.0))) for i in range(4)]
        x, y = v[0] / v[3], v[1] / v[3]
        return ((x + 1) / 2 * size[0], (1 - y) / 2 * size[1])
    return img, proj

def arrow(d, p0, p1, col=(220, 60, 20), w=7):
    d.line([p0, p1], fill=col, width=w)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); L = 24
    for s in (-1, 1):
        d.line([p1, (p1[0] - L * math.cos(ang + s * 0.45), p1[1] - L * math.sin(ang + s * 0.45))], fill=col, width=w)

def label(d, xy, text, f, col=(30, 30, 30), anchor='la', box=True):
    if box:
        bb = d.textbbox(xy, text, font=f, anchor=anchor); pad = 6
        d.rectangle((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad), fill=(255, 255, 255), outline=(150, 150, 150))
    d.text(xy, text, font=f, fill=col, anchor=anchor)

def rotp(p, deg):  # putar titik dunia terhadap sumbu jig
    a = math.radians(deg); x, y, z = p[0] - CX, p[1], p[2] - CZ
    return (CX + x * math.cos(a) + z * math.sin(a), y, CZ - x * math.sin(a) + z * math.cos(a))

f_t = ImageFont.truetype(FONTB, 38); f_s = ImageFont.truetype(FONT, 27); f_l = ImageFont.truetype(FONT, 25)
TOP = Y_DISC1_TOP + 372

# ---- 4 langkah ----
steps = [
    (dict(clamp=0, lift=170), '1. Letakkan TBU', 'Rahang terbuka. Turunkan TBU (muka mounting di bawah)\nke tengah piringan utama.'),
    (dict(clamp=1), '2. Jepit TBU', 'Putar handle kedua ragum sampai rahang\nmenekan kedua ujung TBU (±82 mm per sisi).'),
    (dict(clamp=1, angle=45, pins_out=True), '3. Tarik pin, putar', 'Tarik kedua pin index ±20 mm. Putar piringan:\nTBU dan kedua ragum ikut berputar.'),
    (dict(clamp=1, angle=90), '4. Kunci, kerjakan', 'Masukkan kembali kedua pin (kelipatan 45°).\nTBU terkunci, sisi lain bisa dikerjakan.'),
]
panels = []
for kw, title, sub in steps:
    img, proj = render(state(P, **kw)); d = ImageDraw.Draw(img)
    a = kw.get('angle', 0)
    if kw.get('lift'):
        p0 = proj((CX, TOP + 330, CZ)); p1 = proj((CX, TOP + 200, CZ)); arrow(d, p0, p1)
        for sgn, side in ((1, 'atas'), (-1, 'bawah')):
            q = proj((CX, 470, CZ + sgn * 225)); r = proj((CX, 470, CZ + sgn * 340)); arrow(d, q, r, col=(40, 120, 200))
    elif kw.get('clamp') and not a:
        for sgn in (1, -1):
            q = proj((CX, 470, CZ + sgn * 330)); r = proj((CX, 470, CZ + sgn * 200)); arrow(d, q, r)
        label(d, proj((CX + 40, 640, CZ + 450)), 'putar handle', f_l, anchor='mm')
        label(d, proj((CX + 40, 640, CZ - 450)), 'putar handle', f_l, anchor='mm')
    elif kw.get('pins_out'):
        q = proj(rotp((CX + 250, 310, CZ), a)); r = proj(rotp((CX + 330, 310, CZ), a)); arrow(d, q, r)
        label(d, proj(rotp((CX + 330, 420, CZ), a)), 'tarik pin', f_l, anchor='mm')
        pts = [proj(rotp((CX + 420 * math.cos(math.radians(t)), 330, CZ + 420 * math.sin(math.radians(t))), 0)) for t in range(-70, 10, 4)]
        d.line(pts, fill=(220, 60, 20), width=7); arrow(d, pts[-2], pts[-1])
    else:
        for px, side in ((-307, -1),):
            k = proj(rotp((CX + px, 300, CZ), a)); t = (k[0] + 40, k[1] + 120 * side)
            d.line([k, t], fill=(80, 80, 80), width=3); d.ellipse((k[0] - 7, k[1] - 7, k[0] + 7, k[1] + 7), fill=(220, 60, 20))
            label(d, t, 'pin masuk = terkunci', f_l, anchor='lm')
    panels.append((img, title, sub))

PW, PH, TB = 1500, 1100, 150
sheet = Image.new('RGB', (PW * 2, (PH + TB) * 2 + 160), 'white'); d = ImageDraw.Draw(sheet)
d.text((40, 40), 'Cara penggunaan Jig Ragum Putar – TBU Nabtesco 152-3.5', font=ImageFont.truetype(FONTB, 52), fill=(20, 20, 20))
d.text((40, 105), 'Model TBU disederhanakan (envelope 300 × 206 mm dari gambar Nabtesco); warna hanya untuk visualisasi.', font=f_s, fill=(90, 90, 90))
for i, (img, title, sub) in enumerate(panels):
    x, y = (i % 2) * PW, 160 + (i // 2) * (PH + TB)
    sheet.paste(img, (x, y + TB)); d.rectangle((x + 8, y + 8, x + PW - 8, y + TB + PH - 8), outline=(200, 200, 200), width=3)
    d.text((x + 40, y + 30), title, font=f_t, fill=(20, 20, 20))
    d.multiline_text((x + 40, y + 85), sub, font=f_s, fill=(60, 60, 60), spacing=8)
sheet.save(os.path.join(OUT, 'langkah_penggunaan.png'))

# ---- gambar utama dengan keterangan ----
HW, HH = 2600, 1700
img, proj = render(state(P, clamp=1), size=(HW, HH), zoom=1.45); d = ImageDraw.Draw(img)
f_c = ImageFont.truetype(FONT, 36)
left = [((CX + 78, 440, CZ + 190), 'Rahang (clamp) ragum'),
        ((CX + 60, 540, CZ + 449), 'Handle: putar untuk menjepit / melepas'),
        ((CX + 80, 500, CZ + 330), 'Vise holder (dibaut ke piringan bawah)')]
right = [((CX + 75, 430, CZ - 20), 'TBU (dijepit di kedua ujung)'),
         ((CX + 210, 318, CZ - 95), 'Piringan utama (alas TBU)'),
         ((CX + 300, 288, CZ - 250), 'Piringan bawah (dudukan ragum)'),
         ((CX + 237, 308, CZ), 'Pin index: kunci piringan utama'),
         ((CX + 340, 276, CZ), 'Bantalan UHMW (diam)'),
         ((CX + 400, 273.3, CZ + 190), 'Base Ø900 (dibaut ke meja)')]
for items, x, anc in ((left, 50, 'lm'), (right, HW - 50, 'rm')):
    ys = [260 + k * (HH - 380) / max(1, len(items) - 1) for k in range(len(items))]
    for (p, t), y in zip(items, ys):
        a = proj(p); bb = d.textbbox((x, y), t, font=f_c, anchor=anc)
        e = (bb[2] + 12, y) if anc == 'lm' else (bb[0] - 12, y)
        d.line([a, e], fill=(80, 80, 80), width=3); d.ellipse((a[0] - 8, a[1] - 8, a[0] + 8, a[1] + 8), fill=(220, 60, 20))
        label(d, (x, y), t, f_c, anchor=anc)
d.text((50, 40), 'Jig Ragum Putar Ver4 dengan TBU terjepit', font=ImageFont.truetype(FONTB, 56), fill=(20, 20, 20))
d.text((50, 115), 'TBU Nabtesco 152-3.5 (model disederhanakan, 300 × 206 mm). Kedua piringan, kedua ragum, dan TBU berputar bersama.', font=f_s, fill=(90, 90, 90))
img.save(os.path.join(OUT, 'tbu_terjepit_keterangan.png'))
print('ok')
