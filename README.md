# Jig Assembly ragum

| File | Isi |
|---|---|
| `Ver3 Jig Assembly ragum tetap.step` | Versi asli: hanya piringan hitam yang berputar, ragum dibaut ke Base |
| `Ver4 Jig Assembly ragum putar.step` | Versi baru: ditambah **Piringan bawah** sehingga kedua ragum ikut berputar |
| `tools/tambah_piringan_bawah.py` | Script yang membuat Ver4 dari Ver3 (`pip install cadquery`, lalu `python3 tools/tambah_piringan_bawah.py`) |

## Perubahan Ver3 → Ver4

![Pratinjau Ver4 (piringan bawah diwarnai merah hanya di gambar ini)](docs/preview_ver4_iso.png)

Susunan dari bawah ke atas (satuan mm):

1. **Base (rev)** – tidak berubah.
2. **Ring UHMW** (asli) – tetap di kantong Base, sekarang jadi bantalan luncur piringan bawah.
3. **Piringan bawah** (baru) – Ø880 × 20, berputar pada Pin center, tinggi 2 mm di atas Base.
   - Lubang Ø50 di tengah untuk **Bushing perunggu bawah** (baru, Ø50/Ø40,1 × 20).
   - Kantong Ø465 dalam 10 di muka atas untuk **Ring UHMW atas** + 4 lubang sekrup ring.
   - 8× lubang tap M12 untuk baut kedua **Dudukan ragum** (pola sama dengan di Base).
   - 2× lubang tap M8 untuk **Blok pin index** (posisi sama dengan di Base).
   - Diameter 880 dipilih agar seluruh tapak dudukan ragum (sudut terjauh r ≈ 437 dari sumbu) tertopang.
4. **Ring UHMW atas** (baru, salinan ring asli).
5. **Piringan (baru)** (piringan utama), bushing, Pin index + knob, kedua ragum beserta stud, mur, vise holder, clamp, rod dan handle – **semuanya naik 22 mm**, posisi XZ tidak berubah.

**Pin center** diganti **Pin center (panjang)**: flens tetap dibaut ke Base, poros Ø40 diperpanjang 22 mm (ujung atas Y 305,3 → 327,3) agar menembus bushing kedua piringan.

Hasil pengecekan: celah pin–bushing 0,05 mm di kedua piringan, tidak ada tumpang tindih antar part baru/berpindah.

## Catatan desain

- Piringan bawah Ø880 lebih lebar dari Base (750 × 810): menjorok ±65 mm di sisi X dan ±35 mm di sisi Z. Jangkauan putar ragum sendiri memang sudah ~r 437, jadi ini tidak bisa dihindari kalau ragum harus berputar penuh.
- Piringan bawah hanya ditopang Ring UHMW Ø464; bagian luar tempat ragum menggantung (cantilever). Kalau perlu lebih kaku, pertimbangkan ring UHMW/bantalan kedua berdiameter lebih besar di Base.
- Belum ada pengunci untuk piringan bawah terhadap Base, jadi ragum bisa berputar bebas saat dipakai. Blok pin index yang ada sekarang ikut di atas piringan bawah (mengunci piringan utama relatif terhadap ragum).
- Berat piringan bawah baja Ø880 × 20 ≈ 95 kg.
