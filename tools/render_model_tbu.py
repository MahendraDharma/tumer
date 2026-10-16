"""Render model TBU saja (docs/model_tbu.png): python3 tools/render_model_tbu.py docs/model_tbu.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_visualisasi_tbu as R
from visualisasi_tbu import *
T = {n: s.translate(cq.Vector(CX, 0, CZ)) for n, s in build_tbu().items()}
R.BOUNDS = (CX - 270, CX + 270, -75, 330, CZ - 110, CZ + 120)
R.CAMS['foto'] = ((CX + 300, 480, CZ + 1000), (CX, 120, CZ), 20)
img, _ = R.render(T, cam='foto', size=(1400, 1000), zoom=1.1)
img.save(sys.argv[1])
