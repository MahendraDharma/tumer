"""Render model TBU saja (docs/model_tbu.png): python3 tools/render_model_tbu.py docs/model_tbu.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_visualisasi_tbu as R
from visualisasi_tbu import *
T = {n: s.translate(cq.Vector(CX, 0, CZ)) for n, s in build_tbu().items()}
R.BOUNDS = (CX - 270, CX + 300, 0, 360, CZ - 110, CZ + 120)
R.CAMS['samping'] = ((CX + 350, 600, CZ + 2000), (CX, 170, CZ), 14)
R.CAMS['iso'] = ((CX + 950, 750, CZ + 650), (CX, 150, CZ), 20)
from PIL import Image, ImageDraw, ImageFont
a, _ = R.render(T, cam='samping', size=(1300, 900), zoom=1.05, bg=(0.86, 0.88, 0.90))
b, _ = R.render(T, cam='iso', size=(1300, 900), zoom=1.05, bg=(0.86, 0.88, 0.90))
out = Image.new('RGB', (2600, 980), 'white'); out.paste(a, (0, 80)); out.paste(b, (1300, 80))
d = ImageDraw.Draw(out); f = ImageFont.truetype(R.FONTB, 40)
d.text((40, 25), 'Tampak samping (depan)', font=f, fill=(20, 20, 20)); d.text((1340, 25), 'Isometri dari ujung shoe head', font=f, fill=(20, 20, 20))
out.save(sys.argv[1])
