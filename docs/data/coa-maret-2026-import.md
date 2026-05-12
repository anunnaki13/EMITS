# COA Workbook Import - Update Maret 2026

## Source

- File: `Rekapitulasi CoA Loading, Unloading dan Lab Internal 2026 (Upd. Maret).xlsx`
- Imported sheet utama: `Rekapitulasi CoA`
- Imported sheet umpire: `Data Umpire Batubara`

## Parser Behavior

- `Rekapitulasi CoA` dibaca sebagai workbook gabungan dengan blok `UNLOADING`, `LOADING`, `INTERNAL`, dan `UMPIRE`.
- `Data Umpire Batubara` dipakai sebagai sumber utama data umpire karena memiliki nomor sampel, tanggal pengajuan, lab umpire, tanggal hasil, dan hasil final.
- Kolom periode berformat Indonesia seperti `Mei-23` dinormalisasi menjadi `2023-05-01`.
- Shipment numerik disimpan sebagai string tanpa `.0`; shipment `LOT` dipertahankan sebagai label string.
- Status kualitas tetap mengikuti aturan aplikasi: `critical` bila `Loading GCV - Internal GCV > 150`, `warning` bila `> 100`, selain itu `normal`.

## Dry-Run Result

- Total record rekonsiliasi: `754`
- Rentang `completed_unloading`: `2020-08-03` sampai `2026-04-27`
- Record dengan Loading GCV: `753`
- Record dengan Unloading GCV: `753`
- Record dengan Internal GCV: `445`
- Record umpire selesai: `201`

## Local Import Result

- Koleksi MongoDB: `coa_reconciliation`
- Jumlah sebelum import: `721`
- Jumlah setelah import: `754`
- Status kualitas setelah import: `497 normal`, `232 critical`, `25 warning`
- Status umpire setelah import: `201 completed`, `553 none`
- Record terbaru setelah import: `LOT 483`, supplier `KBB MBE`, `completed_unloading` `2026-04-27`

## Import Command

```bash
./backend/.venv/bin/python backend/scripts/import_coa_workbook.py "Rekapitulasi CoA Loading, Unloading dan Lab Internal 2026 (Upd. Maret).xlsx"
```

Dry-run tanpa menulis database:

```bash
./backend/.venv/bin/python backend/scripts/import_coa_workbook.py "Rekapitulasi CoA Loading, Unloading dan Lab Internal 2026 (Upd. Maret).xlsx" --dry-run
```
