# Jig Assembly ragum

| File | Isi |
|---|---|
| `Ver3 Jig Assembly ragum tetap.step` | Versi asli: hanya piringan hitam yang berputar, ragum dibaut ke Base |
| `Ver4 Jig Assembly ragum putar.step` | Versi baru: ditambah **Piringan bawah** sehingga kedua ragum ikut berputar |
| `tools/tambah_piringan_bawah.py` | Script yang membuat Ver4 dari Ver3 (`pip install cadquery`, lalu `python3 tools/tambah_piringan_bawah.py`) |

## Perubahan Ver3 → Ver4

![Pratinjau Ver4 (piringan bawah diwarnai merah hanya di gambar ini)](docs/preview_ver4_iso.png)

Susunan dari bawah ke atas (satuan mm):

1. **Base (rev2)** – Base lama + kantong Ø711/Ø609 dalam 10 untuk ring luar (8× tap M6) dan 8× lubang index Ø16,1 tembus pada r 266 tiap 45°.
2. **Ring UHMW** (asli) – tetap di kantong Base, sekarang jadi bantalan luncur piringan bawah.
   **Ring UHMW luar** (baru, Ø710/Ø610 × 12) – penopang kedua agar bagian luar piringan bawah (tempat ragum) tidak menggantung.
3. **Piringan bawah** (baru) – Ø880 × 20, berputar pada Pin center, tinggi 2 mm di atas Base.
   - Lubang Ø50 di tengah untuk **Bushing perunggu bawah** (baru, Ø50/Ø40,1 × 20).
   - Kantong Ø465 dalam 10 di muka atas untuk **Ring UHMW atas** + 4 lubang sekrup ring.
   - 8× lubang tap M12 untuk baut kedua **Dudukan ragum** (pola sama dengan di Base).
   - 2× lubang tap M8 untuk **Blok pin index** (posisi sama dengan di Base).
   - Lubang Ø16,1 + 2× tap M8 di sisi −X untuk **Blok pin index bawah** (baru, 40 × 30 × 70).
     **Pin index bawah** (Ø16) menembus blok dan piringan lalu masuk 15 mm ke salah satu lubang index di Base → piringan bawah terkunci tiap 45°. Knob diangkat 20 mm untuk membebaskan putaran.
   - Diameter 880 dipilih agar seluruh tapak dudukan ragum (sudut terjauh r ≈ 437 dari sumbu) tertopang.
4. **Ring UHMW atas** (baru, salinan ring asli).
5. **Piringan (baru)** (piringan utama), bushing, Pin index + knob, kedua ragum beserta stud, mur, vise holder, clamp, rod dan handle – **semuanya naik 22 mm**, posisi XZ tidak berubah.

**Pin center** diganti **Pin center (panjang)**: flens tetap dibaut ke Base, poros Ø40 diperpanjang 22 mm (ujung atas Y 305,3 → 327,3) agar menembus bushing kedua piringan.

Hasil pengecekan: celah pin–bushing dan pin index–lubang 0,05 mm, tidak ada tumpang tindih antar part baru/berpindah.

## Catatan desain

- Piringan bawah Ø880 lebih lebar dari Base (750 × 810): menjorok ±65 mm di sisi X dan ±35 mm di sisi Z. Jangkauan putar ragum sendiri memang sudah ~r 437, jadi ini tidak bisa dihindari kalau ragum harus berputar penuh.
- Ring UHMW luar dibatasi Ø710 agar tetap di dalam lebar Base (750); bagian piringan di luar r 355 masih menggantung ±85 mm.
- Blok pin index (atas) yang lama ikut di atas piringan bawah, sehingga mengunci piringan utama relatif terhadap ragum; Pin index bawah mengunci ragum relatif terhadap Base.
- Berat piringan bawah baja Ø880 × 20 ≈ 95 kg.
