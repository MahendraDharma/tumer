# Jig Assembly ragum

| File | Isi |
|---|---|
| `Ver3 Jig Assembly ragum tetap.step` | Versi asli: hanya piringan hitam yang berputar, ragum dibaut ke Base |
| `Ver4 Jig Assembly ragum putar.step` | Versi baru: ditambah **Piringan bawah** sehingga kedua ragum ikut berputar |
| `tools/tambah_piringan_bawah.py` | Script yang membuat Ver4 dari Ver3 (`pip install cadquery`, lalu `python3 tools/tambah_piringan_bawah.py`) |

## Perubahan Ver3 → Ver4

![Pratinjau Ver4 (piringan bawah merah, pin biru; warna hanya di gambar ini)](docs/preview_ver4_iso.png)

Bagian baru dirampingkan ke faktor keamanan ±2,5 (spesifikasi kelompok). Susunan dari bawah ke atas (satuan mm):

1. **Base (rev)** – plat SS400 660 × 660 × 5 (sudut R60), ditopang penuh oleh meja kerja dan dijepit lewat 4 lubang Ø40. Hanya ada 4 tap M6 untuk ring UHMW dan 4 tap M6 untuk flens Pin center.
2. **Ring UHMW** – Ø464 / Ø300 × 5, di atas Base, 4 baut L M6 kepala tenggelam.
3. **Piringan bawah** (baru) – plat SS400 20 mm, lingkaran Ø880 dipangkas menjadi lajur 600 mm sepanjang sumbu ragum; di bawah dudukan (lebih dari 270 mm dari sumbu) lebarnya 360 mm (±65 kg).
   - Lubang Ø50 di tengah untuk **Bushing perunggu bawah** (Ø50/Ø40,1 × 18) dan cekungan bawah Ø86 × 2 di atas flens Pin center.
   - Cekungan Ø465 × 1 di muka atas untuk **Ring UHMW atas** (Ø464 / Ø300 × 3).
   - 8× tap M12 untuk baut kedua **Dudukan ragum** (pola sama dengan Base Ver3).
   - 8× lubang radial Ø10,5 (tiap 45°) dari tepi sampai lubang tengah, untuk Pin index bawah.
4. **Piringan (baru)** (piringan utama), bushing, Pin index + knob, kedua ragum beserta stud, mur, vise holder, clamp, rod dan handle – **naik 10 mm** terhadap Ver3, posisi XZ tidak berubah. Jarak rahang ragum ke piringan utama sama seperti Ver3.
5. Alas TBU (muka atas piringan utama) berada **50 mm** di atas meja kerja, sesuai REQ-02.

### Kunci samping (kedua piringan)

Pin masuk dari tepi piringan, lurus ke tengah, dan ujungnya masuk ±12 mm ke lubang silang di **Pin center** yang diam. Tarik pin ±20 mm agar piringan bisa diputar; kunci di kelipatan 45°.

- **Piringan utama**: **Pin index (panjang)** = Pin index asli yang diperpanjang ke dalam; knob tetap di tempatnya.
- **Piringan bawah**: **Pin index bawah** (batang Ø10) + **Knob pin index bawah** (salinan knob asli) di sisi −X.
- **Pin center (panjang)**: flens dibaut ke Base; poros Ø40 sampai rata muka atas piringan utama, 2 lubang silang Ø10,5.

### Faktor keamanan (target ±2,5)

| Bagian | Beban penentu | n |
|---|---|---|
| Piringan bawah, potongan tengah (melewati lubang pin dan Ø50) | Momen jepit ragum F<sub>c</sub>·h = 10 829 N × 210 mm | 2,6 |
| Piringan bawah, awal bagian 360 mm (z = 275) | Momen turun linear ke tepi dudukan (±2 140 N·m) | ±2,6 |
| Piringan bawah, potongan lain | Sama | > 3 |
| Ulir M12 dudukan di piringan bawah (panjang ulir 18) | Tarik baut dari momen guling + preload | 3,9 |
| Baut M12 dudukan | Sama; momen kencang dibatasi 37 N·m | ±3 |
| Baut flens Pin center M6 (geser) | Torsi kerja 210 N·m saat terkunci | 3,4 |
| Base 5 mm, ring UHMW 5/3 mm, bushing 18 mm | Berat; ditopang meja | > 4 |

Berat total jig (tanpa TBU dan meja): ±179 kg.

Hasil pengecekan CAD: celah pin–lubang 0,25 mm, pin center–bushing 0,05 mm, flens Pin center–piringan bawah 2 mm; tidak ada tumpang tindih antar part.

## Catatan

- Piringan bawah lebih lebar dari Base dan menjorok di atas meja kerja; ia hanya bertumpu di Ring UHMW Ø464.
- Piringan utama (18 mm), dudukan ragum, vise holder, dan clamp adalah part Ver3 dan tidak diubah.
