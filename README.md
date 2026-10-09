# Jig Assembly ragum

| File | Isi |
|---|---|
| `Ver3 Jig Assembly ragum tetap.step` | Versi asli: hanya piringan hitam yang berputar, ragum dibaut ke Base |
| `Ver4 Jig Assembly ragum putar.step` | Versi baru: ditambah **Piringan bawah** sehingga kedua ragum ikut berputar |
| `Ver4 Jig + TBU terjepit.step` | Ver4 dengan TBU (model sederhana) dalam kondisi terjepit kedua ragum |
| `tools/tambah_piringan_bawah.py` | Script yang membuat Ver4 dari Ver3 (`pip install cadquery`, lalu `python3 tools/tambah_piringan_bawah.py`) |

## Perubahan Ver3 → Ver4

![Pratinjau Ver4 (piringan bawah merah, pin biru; warna hanya di gambar ini)](docs/preview_ver4_iso.png)

Bagian baru dirampingkan ke faktor keamanan ≥ 2 (spesifikasi kelompok). Susunan dari bawah ke atas (satuan mm):

1. **Base (rev)** – plat bulat SS400 Ø900 × 5 yang menutup seluruh area putar, ditopang penuh oleh meja kerja dan diikat dengan **8 baut kepala benam M8** (rata permukaan, mur di bawah meja). Ada 4 tap M6 untuk ring UHMW, 4 tap M6 untuk flens Pin center, dan 8 tap M6 untuk bantalan UHMW.
2. **Ring UHMW** – Ø464 / Ø300 × 5, di atas Base, 4 baut L M6 kepala tenggelam.
   **8 Bantalan UHMW** – 70 × 60 × 5 di r ≈ 330 (tiap 45°), di bawah ujung piringan bawah tempat ragum, jadi ragum tidak mengambang. Setiap bantalan diikat 1 baut benam M6.
3. **Piringan bawah** (baru) – plat SS400 19 mm, lingkaran Ø880 dipangkas menjadi lajur 600 mm sepanjang sumbu ragum; di bawah dudukan (lebih dari 270 mm dari sumbu) lebarnya 360 mm (±62 kg).
   - Lubang Ø50 di tengah untuk **Bushing perunggu bawah** (Ø50/Ø40,1 × 17) dan cekungan bawah Ø86 × 2 di atas flens Pin center.
   - Cekungan Ø465 × 1 di muka atas untuk **Ring UHMW atas** (Ø464 / Ø300 × 3).
   - 8× tap M12 untuk baut kedua **Dudukan ragum** (pola sama dengan Base Ver3).
   - 8× lubang radial Ø10,5 (tiap 45°) dari tepi sampai lubang tengah, untuk Pin index bawah.
4. **Piringan (baru)** (piringan utama), bushing, Pin index + knob, kedua ragum beserta stud, mur, vise holder, clamp, rod dan handle – **naik 9 mm** terhadap Ver3, posisi XZ tidak berubah. Jarak rahang ragum ke piringan utama sama seperti Ver3.
5. Alas TBU (muka atas piringan utama) berada **49 mm** di atas meja kerja, sesuai REQ-02 (≤ 50 mm).

### Kunci samping (kedua piringan)

Pin masuk dari tepi piringan, lurus ke tengah, dan ujungnya masuk ±12 mm ke lubang silang di **Pin center** yang diam. Tarik pin ±20 mm agar piringan bisa diputar; kunci di kelipatan 45°.

- **Piringan utama**: **Pin index (panjang)** = Pin index asli yang diperpanjang ke dalam; knob tetap di tempatnya.
- **Piringan bawah**: **Pin index bawah** (batang Ø10) + **Knob pin index bawah** (salinan knob asli) di sisi −X.
- **Pin center (panjang)**: flens dibaut ke Base; poros Ø40 sampai rata muka atas piringan utama, 2 lubang silang Ø10,5.

### Faktor keamanan (target ≥ 2)

| Bagian | Beban penentu | n |
|---|---|---|
| Piringan bawah, potongan tengah (melewati lubang pin dan Ø50) | Momen jepit ragum F<sub>c</sub>·h = 10 829 N × 210 mm (momen penuh, konservatif) | 2,2 |
| Piringan bawah, awal bagian 360 mm (z = 275) | Momen jepit penuh (konservatif) | 2,2 |
| Piringan bawah, potongan lain | Sama | > 2,9 |
| Ulir M12 dudukan di piringan bawah (plat 19, ulir terpakai 18) | Tarik baut dari momen guling + preload | 3,9 |
| Baut M12 dudukan | Sama; momen kencang dibatasi 37 N·m | ±3 |
| Baut flens Pin center M6 (geser) | Torsi kerja 210 N·m saat terkunci | 3,4 |
| Base 5 mm, ring dan bantalan UHMW 5/3 mm, bushing 17 mm | Berat; ditopang meja | > 4 |

Berat total jig (tanpa TBU dan meja): ±184 kg.

Hasil pengecekan CAD: celah pin–lubang 0,25 mm, pin center–bushing 0,05 mm, flens Pin center–piringan bawah 2 mm, knob pin bawah–bantalan 3,1 mm; tidak ada tumpang tindih antar part.

## Catatan

- Base Ø900 menjorok ±41 mm keluar dari tepi meja kerja di sisi +Z.
- Baut Base ke meja diubah dari 4 × M20 (REQ-05) menjadi 8 × M8 kepala benam, karena kepala M20 akan tertabrak piringan bawah.
- Piringan utama (18 mm), dudukan ragum, vise holder, dan clamp adalah part Ver3 dan tidak diubah.

## Cara penggunaan (visualisasi dengan TBU)

![Jig dengan TBU terjepit](docs/tbu_terjepit_keterangan.png)

![Langkah penggunaan](docs/langkah_penggunaan.png)

1. Buka kedua rahang. Letakkan TBU dengan muka mounting (4 × M20) di bawah, di tengah piringan utama.
2. Putar handle kedua ragum sampai rahang menekan kedua ujung TBU. Untuk TBU 152-3.5 (panjang 300 mm), setiap rahang maju ±82 mm.
3. Tarik kedua pin index ±20 mm, lalu putar piringan. TBU, kedua ragum, dan kedua piringan berputar bersama.
4. Masukkan kembali kedua pin di kelipatan 45°. TBU terkunci dan sisi lain bisa dikerjakan.

Model TBU disederhanakan dari gambar Nabtesco Tread Brake Unit 152-3.5 (panjang 300 mm, lebar 206 mm, pola mounting 114 × 250). Bentuknya hanya envelope, bukan geometri asli. Kedua ragum di Ver3 terpasang miring ±0,82° terhadap sumbu jig, jadi TBU di model diputar dengan sudut yang sama. Dibuat dengan `tools/visualisasi_tbu.py` (STEP) dan `tools/render_visualisasi_tbu.py` (gambar).
