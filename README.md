# Jig Assembly ragum

| File | Isi |
|---|---|
| `Ver3 Jig Assembly ragum tetap.step` | Versi asli: hanya piringan hitam yang berputar, ragum dibaut ke Base |
| `Ver4 Jig Assembly ragum putar.step` | Versi baru: ditambah **Piringan bawah** sehingga kedua ragum ikut berputar |
| `tools/tambah_piringan_bawah.py` | Script yang membuat Ver4 dari Ver3 (`pip install cadquery`, lalu `python3 tools/tambah_piringan_bawah.py`) |

## Perubahan Ver3 → Ver4

![Pratinjau Ver4 (piringan bawah merah, pin biru; warna hanya di gambar ini)](docs/preview_ver4_iso.png)

Susunan dari bawah ke atas (satuan mm):

1. **Base (rev)** – diperlebar menjadi persegi 920 × 920 (sudut R100) agar seluruh piringan bawah tertumpu. Semua lubang dan kantong Base Ver3 tetap di posisinya.
2. **Ring UHMW** (asli) – tetap di kantong Base, sekarang jadi bantalan luncur piringan bawah.
3. **Piringan bawah** (baru) – Ø880 × 30, berputar pada Pin center, 2 mm di atas Base.
   - Lubang Ø50 di tengah untuk **Bushing perunggu bawah** (Ø50/Ø40,1 × 30).
   - Kantong Ø465 dalam 10 untuk **Ring UHMW atas** + 4 lubang sekrup ring.
   - 8× lubang tap M12 untuk baut kedua **Dudukan ragum** (pola sama dengan di Base).
   - 8× lubang radial Ø10,5 (tiap 45°) dari tepi sampai lubang tengah, untuk Pin index bawah.
   - Tebal 30 agar di bawah kantong ring masih ada 20 mm material untuk lubang pin.
4. **Ring UHMW atas** (salinan ring asli).
5. **Piringan (baru)** (piringan utama), bushing, Pin index + knob, kedua ragum beserta stud, mur, vise holder, clamp, rod dan handle – **semuanya naik 32 mm**, posisi XZ tidak berubah.

### Kunci samping (kedua piringan)

Pin masuk dari tepi piringan, lurus ke tengah, dan ujungnya masuk ±12 mm ke lubang silang di **Pin center** yang diam. Tarik pin ±20 mm (sampai keluar dari bushing) agar piringan bisa diputar; kunci di kelipatan 45° saat salah satu lubang radial piringan segaris dengan lubang Pin center (sumbu X).

- **Piringan utama**: **Pin index (panjang)** = Pin index asli yang diperpanjang ke dalam; knob tetap di tempatnya. 8 lubang radial piringan dan **Bushing perunggu** diteruskan sampai lubang tengah.
- **Piringan bawah**: **Pin index bawah** (batang Ø10) + **Knob pin index bawah** (salinan knob asli) di sisi −X.
- **Pin center (panjang)**: flens tetap dibaut ke Base; poros Ø40 diperpanjang sampai rata muka atas piringan utama dan diberi 2 lubang silang Ø10,5 (satu per piringan).

Hasil pengecekan: celah pin–lubang 0,25 mm, pin center–bushing 0,05 mm, piringan bawah–Base 2 mm; tidak ada tumpang tindih antar part.

## Catatan

- Base 920 × 920 sedikit keluar dari tepi meja kerja: ±31 mm di sisi +X dan ±51 mm di sisi +Z.
- Berat piringan bawah baja Ø880 × 30 ≈ 120 kg.
