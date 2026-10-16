"""Gambar potongan bagian tengah jig (docs/potongan_bearing.png): letak thrust bearing AXK4060,
washer AS4060, bushing perunggu, Pin center, dan pin index.
Jalankan: python3 tools/render_potongan_bearing.py docs   (butuh cadquery, vtk, pillow)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_visualisasi_tbu import render, label, CAMS, FONT, FONTB
import render_visualisasi_tbu as R
from visualisasi_tbu import *
from PIL import ImageDraw, ImageFont

OUT = sys.argv[1]
P = read_parts()
win = cq.Solid.makeBox(240, 70, 170.3, cq.Vector(CX - 120, 266, CZ - 170))   # potong 0,3 mm di depan sumbu
cut = {}
for n, s in P.items():
    if n.startswith(('Replika', 'Stud', 'Mur', 'Vise', 'Clamp', 'Handle', 'Dudukan')): continue
    c = s.intersect(win)
    if c.Volume() > 1: cut[n] = c
R.BOUNDS = (CX - 120, CX + 120, 266, 330, CZ - 60, CZ)
CAMS['pot'] = ((CX + 180, 520, CZ + 900), (CX, 298, CZ - 20), 12)
W, H = 2600, 1500
img, proj = render(cut, cam='pot', size=(W, H), zoom=1.15); d = ImageDraw.Draw(img)
f = ImageFont.truetype(FONT, 34)
yb, ya = Y_DISC1_TOP - 18 - 3 - 20 - 1, Y_DISC1_TOP - 18 - 2   # dasar set bearing bawah / atas
left = [((CX - 10, 318, CZ), 'Pin center (diam, dibaut ke Base)'),
        ((CX - 85, 316, CZ), 'Piringan utama'),
        ((CX - 70, 288.3, CZ), 'Pin index bawah (kunci piringan bawah)'),
        ((CX - 27, 277.5, CZ), 'Flens Pin center + baut benam M6')]
right = [((CX + 70, 309.3, CZ), 'Pin index (kunci piringan utama)'),
         ((CX + 23, 316.5, CZ), 'Bushing perunggu (bantalan radial)'),
         ((CX + 26, ya + 2, CZ), 'Thrust bearing AXK4060 + 2 washer AS4060 (atas)'),
         ((CX + 23, 295.5, CZ), 'Bushing perunggu bawah'),
         ((CX + 95, 296, CZ), 'Piringan bawah'),
         ((CX + 26, yb + 2, CZ), 'Thrust bearing AXK4060 + 2 washer AS4060 (bawah)'),
         ((CX + 95, 271, CZ), 'Base (diam)')]
for items, x, anc in ((left, 50, 'lm'), (right, W - 50, 'rm')):
    ys = [230 + k * (H - 330) / max(1, len(items) - 1) for k in range(len(items))]
    for (p, t), y in zip(items, ys):
        a = proj(p); bb = d.textbbox((x, y), t, font=f, anchor=anc)
        e = (bb[2] + 12, y) if anc == 'lm' else (bb[0] - 12, y)
        d.line([a, e], fill=(80, 80, 80), width=3); d.ellipse((a[0] - 8, a[1] - 8, a[0] + 8, a[1] + 8), fill=(220, 60, 20))
        label(d, (x, y), t, f, anchor=anc)
d.text((50, 40), 'Potongan tengah: letak bearing', font=ImageFont.truetype(FONTB, 54), fill=(20, 20, 20))
d.text((50, 112), 'Setiap piringan duduk di satu thrust bearing jarum AXK4060 (total tebal 4 mm dengan washer); '
       'bushing perunggu menahan arah radial.', font=ImageFont.truetype(FONT, 28), fill=(90, 90, 90))
img.save(os.path.join(OUT, 'potongan_bearing.png'))
print('ok')
