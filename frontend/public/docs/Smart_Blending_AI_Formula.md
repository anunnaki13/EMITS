# DOKUMENTASI FORMULA SMART BLENDING AI
## Sistem Manajemen Bahan Bakar Digital - PLTU Tenayan

**Versi:** 1.0  
**Tanggal:** 30 Januari 2026  
**Dibuat oleh:** Tim Pengembang Tenayan Fuel Intelligence

---

## DAFTAR ISI

1. [Pendahuluan](#1-pendahuluan)
2. [Formula Utama Blending](#2-formula-utama-blending)
3. [Parameter Input (Constraints)](#3-parameter-input-constraints)
4. [Klasifikasi Batubara](#4-klasifikasi-batubara)
5. [Basis Pengukuran](#5-basis-pengukuran)
6. [Sumber Data untuk Optimasi](#6-sumber-data-untuk-optimasi)
7. [Kriteria Optimasi](#7-kriteria-optimasi)
8. [Contoh Perhitungan Manual](#8-contoh-perhitungan-manual)
9. [Output AI](#9-output-ai)
10. [Referensi Teknis](#10-referensi-teknis)

---

## 1. PENDAHULUAN

Smart Blending AI adalah fitur berbasis kecerdasan buatan yang mengoptimasi pencampuran batubara untuk mencapai spesifikasi kualitas yang diinginkan. Sistem ini menggunakan model AI (Google Gemini) untuk menganalisis inventori batubara yang tersedia dan memberikan rekomendasi blending yang optimal.

### Tujuan Utama:
- Mencapai target GCV (Gross Calorific Value) yang diinginkan
- Menjaga semua parameter kualitas dalam batas yang ditentukan
- Mengoptimalkan biaya dengan memilih kombinasi batubara yang efisien
- Memastikan ketersediaan stok mencukupi untuk kuantitas yang dibutuhkan

---

## 2. FORMULA UTAMA BLENDING

### 2.1 Prinsip Linear Interpolation

Formula dasar blending menggunakan prinsip **rata-rata tertimbang (weighted average)**:

```
Hasil_Parameter = Σ (Parameter_i × Persentase_i)
```

Dimana:
- `Parameter_i` = Nilai parameter dari batubara ke-i
- `Persentase_i` = Persentase (dalam desimal) batubara ke-i dalam campuran
- `Σ Persentase_i = 1.0` (total harus 100%)

### 2.2 Aplikasi untuk Setiap Parameter

| Parameter | Formula |
|-----------|---------|
| **GCV Campuran** | GCV₁×%₁ + GCV₂×%₂ + ... + GCVₙ×%ₙ |
| **Abu Campuran** | Ash₁×%₁ + Ash₂×%₂ + ... + Ashₙ×%ₙ |
| **Sulphur Campuran** | TS₁×%₁ + TS₂×%₂ + ... + TSₙ×%ₙ |
| **Total Moisture** | TM₁×%₁ + TM₂×%₂ + ... + TMₙ×%ₙ |
| **Inherent Moisture** | IM₁×%₁ + IM₂×%₂ + ... + IMₙ×%ₙ |
| **Volatile Matter** | VM₁×%₁ + VM₂×%₂ + ... + VMₙ×%ₙ |
| **Fixed Carbon** | FC₁×%₁ + FC₂×%₂ + ... + FCₙ×%ₙ |

### 2.3 Formula untuk Tonase

```
Tonase_i = Total_Kuantitas × Persentase_i
```

---

## 3. PARAMETER INPUT (CONSTRAINTS)

### 3.1 Tabel Parameter

| Parameter | Satuan | Range Tipikal | Default | Keterangan |
|-----------|--------|---------------|---------|------------|
| **Target GCV** | kcal/kg | 3700 - 4700 | - | Nilai kalor yang ingin dicapai |
| **Max Ash** | % (ARB) | 3.3 - 6.0 | - | Batas maksimal kandungan abu |
| **Max Sulphur** | % (ARB) | 0.13 - 2.2 | - | Batas maksimal kandungan belerang |
| **Max Total Moisture** | % (ARB) | 25 - 40 | 35.0 | Kelembaban total maksimal |
| **Max Inherent Moisture** | % (ADB) | 13.8 - 25 | 18.0 | Kelembaban inheren maksimal |
| **Min Volatile Matter** | % (ARB) | 27.9 - 40 | 35.0 | Zat terbang minimal |
| **Min Fixed Carbon** | % (ARB) | 23 - 41 | 25.0 | Karbon tetap minimal |
| **Target Quantity** | MT | - | - | Total tonase yang dibutuhkan |

### 3.2 Penjelasan Parameter

#### GCV (Gross Calorific Value)
- **Definisi:** Jumlah energi panas yang dihasilkan per kilogram batubara saat pembakaran sempurna
- **Satuan:** kCal/kg atau MJ/kg
- **Konversi:** 1 MJ/kg = 238.85 kCal/kg
- **Dampak:** Semakin tinggi GCV, semakin banyak energi yang dihasilkan

#### Ash Content (Kandungan Abu)
- **Definisi:** Residu mineral yang tersisa setelah pembakaran sempurna
- **Dampak tinggi:** Meningkatkan keausan, fouling, dan biaya pembuangan
- **Target:** Semakin rendah semakin baik

#### Total Sulphur
- **Definisi:** Kandungan belerang total dalam batubara
- **Dampak tinggi:** Emisi SO₂, korosi, dan polusi lingkungan
- **Target:** Semakin rendah semakin baik

#### Total Moisture (TM)
- **Definisi:** Kandungan air total dalam batubara (surface + inherent)
- **Dampak tinggi:** Menurunkan nilai kalor efektif, meningkatkan biaya transportasi
- **Target:** Semakin rendah semakin baik

#### Inherent Moisture (IM)
- **Definisi:** Kandungan air yang terikat secara fisik dalam struktur batubara
- **Berbeda dengan:** Surface moisture yang bisa hilang saat pengeringan

#### Volatile Matter (VM)
- **Definisi:** Komponen batubara yang menguap saat dipanaskan tanpa udara
- **Dampak:** Mempengaruhi kemudahan penyalaan dan kestabilan nyala

#### Fixed Carbon (FC)
- **Definisi:** Karbon yang tersisa setelah volatile matter hilang
- **Dampak:** Indikator utama kandungan energi batubara

---

## 4. KLASIFIKASI BATUBARA

### 4.1 Berdasarkan Rank (Peringkat)

| Tipe | GCV Range (ARB) | Karakteristik | Harga |
|------|-----------------|---------------|-------|
| **LRC (Low Rank Coal)** | 3000 - 4500 kcal/kg | Moisture tinggi (>30%), volatile matter tinggi | Lebih murah |
| **MRC (Medium Rank Coal)** | 4500 - 6000 kcal/kg | Moisture sedang, keseimbangan antara VM dan FC | Sedang |
| **HRC (High Rank Coal)** | >6000 kcal/kg | Moisture rendah, fixed carbon tinggi | Lebih mahal |

### 4.2 Pertimbangan Blending

- **LRC + MRC:** Kombinasi umum untuk mencapai target GCV dengan biaya optimal
- **Rasio tipikal:** 60-70% LRC + 30-40% MRC untuk target GCV 4000-4200 kcal/kg
- **Jumlah batubara ideal:** 2-4 jenis untuk kemudahan operasional

---

## 5. BASIS PENGUKURAN

### 5.1 Jenis Basis

| Kode | Nama Lengkap | Deskripsi | Penggunaan |
|------|--------------|-----------|------------|
| **AR/ARB** | As Received Basis | Kondisi batubara saat diterima, termasuk semua moisture | Perhitungan nilai kalor aktual |
| **ADB** | Air Dried Basis | Setelah dikeringkan di udara terbuka, surface moisture hilang | Standar laboratorium |
| **DB** | Dry Basis | Kondisi kering total, tanpa moisture | Perbandingan kualitas antar batubara |
| **DAF/DAFB** | Dry Ash Free Basis | Tanpa moisture dan abu | Analisis kandungan organik murni |

### 5.2 Konversi Antar Basis

```
GCV (ADB) = GCV (ARB) × [100 / (100 - Surface Moisture)]
GCV (DB) = GCV (ADB) × [100 / (100 - Inherent Moisture)]
```

---

## 6. SUMBER DATA UNTUK OPTIMASI

### 6.1 Inventori Batubara

Data dikumpulkan dari 3 sumber utama dalam 6 bulan terakhir:

| Sumber | Max Records | Data yang Diambil |
|--------|-------------|-------------------|
| **Vessel** | 50 | Pengiriman via kapal besar |
| **Barge** | 50 | Pengiriman via tongkang |
| **Trucking** | 50 | Pengiriman via truk |

### 6.2 Parameter yang Dikumpulkan

Untuk setiap record batubara:
- `supplier` - Nama pemasok
- `gcv_arb` - GCV (As Received)
- `ash_arb` - Abu (As Received)
- `ts_arb` - Total Sulphur (As Received)
- `tm_arb` - Total Moisture (As Received)
- `im_adb` - Inherent Moisture (Air Dried)
- `vm_arb` - Volatile Matter (As Received)
- `fc_arb` - Fixed Carbon (As Received)
- `bl_mt` / `quantity` - Tonase tersedia
- `date` - Tanggal penerimaan

### 6.3 Data Pendukung

- **Smart Stock:** Data stok aktual di stockpile
- **Merit Order:** Data harga per kCal dari setiap supplier

---

## 7. KRITERIA OPTIMASI

### 7.1 Urutan Prioritas

| Prioritas | Kriteria | Keterangan |
|-----------|----------|------------|
| **1** | Capai Target GCV | Hasil blend harus memenuhi target GCV |
| **2** | Parameter dalam batas | Semua constraint (ash, sulphur, dll) terpenuhi |
| **3** | Optimasi biaya | Gunakan batubara lebih murah jika memungkinkan |
| **4** | Minimalkan supplier | Idealnya 2-4 jenis batubara |

### 7.2 Constraint Validation

Setiap rekomendasi harus memenuhi:
```
GCV_hasil ≥ Target_GCV
Ash_hasil ≤ Max_Ash
Sulphur_hasil ≤ Max_Sulphur
TM_hasil ≤ Max_Total_Moisture
IM_hasil ≤ Max_Inherent_Moisture
VM_hasil ≥ Min_Volatile_Matter
FC_hasil ≥ Min_Fixed_Carbon
```

---

## 8. CONTOH PERHITUNGAN MANUAL

### 8.1 Skenario

**Target:**
- GCV = 4000 kcal/kg
- Max Ash = 5%
- Kuantitas = 10,000 MT

**Batubara Tersedia:**

| Supplier | GCV (ARB) | Ash (ARB) | Tipe |
|----------|-----------|-----------|------|
| PT. Supplier A | 4800 | 3.5% | MRC |
| PT. Supplier B | 3500 | 5.5% | LRC |

### 8.2 Langkah Perhitungan

**Step 1: Mencari persentase untuk mencapai target GCV**

Menggunakan persamaan linear:
```
Target_GCV = (GCV_A × X) + (GCV_B × (1-X))

4000 = (4800 × X) + (3500 × (1-X))
4000 = 4800X + 3500 - 3500X
4000 - 3500 = 1300X
500 = 1300X
X = 0.385 (38.5%)
```

Hasil:
- Supplier A: 38.5%
- Supplier B: 61.5%

**Step 2: Verifikasi Ash Content**
```
Ash_campuran = (Ash_A × %_A) + (Ash_B × %_B)
Ash_campuran = (3.5 × 0.385) + (5.5 × 0.615)
Ash_campuran = 1.35 + 3.38
Ash_campuran = 4.73%
```

✅ Ash 4.73% < 5% (MEMENUHI SYARAT)

**Step 3: Hitung Tonase**
```
Tonase_A = 10,000 × 0.385 = 3,850 MT
Tonase_B = 10,000 × 0.615 = 6,150 MT
```

### 8.3 Hasil Akhir

| Supplier | Persentase | Tonase | GCV | Ash |
|----------|------------|--------|-----|-----|
| PT. Supplier A | 38.5% | 3,850 MT | 4800 | 3.5% |
| PT. Supplier B | 61.5% | 6,150 MT | 3500 | 5.5% |
| **CAMPURAN** | **100%** | **10,000 MT** | **4000** | **4.73%** |

---

## 9. OUTPUT AI

### 9.1 Struktur Response

AI memberikan output dalam format JSON:

```json
{
  "recommendation": [
    {
      "supplier": "PT BUKIT ASAM",
      "source": "Vessel",
      "type": "LRC",
      "percentage": 60.0,
      "tonnage": 6000.0,
      "gcv": 4277,
      "ash": 4.4,
      "sulphur": 0.21,
      "total_moisture": 34.0,
      "inherent_moisture": 15.3,
      "volatile_matter": 31.9,
      "fixed_carbon": 29.7
    },
    {
      "supplier": "PT PLN BATUBARA",
      "source": "Barge",
      "type": "MRC",
      "percentage": 40.0,
      "tonnage": 4000.0,
      "gcv": 4650,
      "ash": 3.8,
      "sulphur": 0.18,
      "total_moisture": 28.0,
      "inherent_moisture": 14.0,
      "volatile_matter": 35.2,
      "fixed_carbon": 33.0
    }
  ],
  "predicted_quality": {
    "gcv": 4426,
    "ash": 4.16,
    "sulphur": 0.198,
    "total_moisture": 31.6,
    "inherent_moisture": 14.78,
    "volatile_matter": 33.22,
    "fixed_carbon": 31.02
  },
  "meets_target": true,
  "reasoning": "Kombinasi ini menggunakan 60% batubara LRC dari PT BUKIT ASAM dan 40% MRC dari PT PLN BATUBARA untuk mencapai target GCV 4000 kcal/kg dengan margin aman.",
  "cost_warning": "Penggunaan batubara MRC sebesar 40% mungkin meningkatkan biaya dibanding blend yang lebih banyak LRC."
}
```

### 9.2 Penjelasan Field

| Field | Deskripsi |
|-------|-----------|
| `recommendation` | Array batubara yang direkomendasikan |
| `predicted_quality` | Hasil perhitungan kualitas campuran |
| `meets_target` | Boolean apakah semua target tercapai |
| `reasoning` | Penjelasan mengapa blend ini optimal |
| `cost_warning` | Peringatan terkait biaya jika relevan |

---

## 10. REFERENSI TEKNIS

### 10.1 Standar yang Digunakan

- **ASTM D388** - Classification of Coals by Rank
- **ISO 1928** - Determination of Gross Calorific Value
- **ISO 11722** - Determination of Moisture Content
- **ISO 1171** - Determination of Ash Content

### 10.2 Asumsi dan Batasan

1. Formula blending mengasumsikan pencampuran homogen
2. Data kualitas dari COA (Certificate of Analysis) dianggap akurat
3. Tidak memperhitungkan segregasi selama penyimpanan
4. Nilai prediksi memiliki toleransi ±5% dari hasil aktual

### 10.3 Rekomendasi Operasional

1. Lakukan verifikasi kualitas campuran secara berkala
2. Perhatikan urutan pencampuran untuk homogenitas
3. Simpan record blending untuk traceability
4. Bandingkan prediksi dengan hasil aktual untuk kalibrasi model

---

## LAMPIRAN

### A. Glossary

| Istilah | Definisi |
|---------|----------|
| ARB | As Received Basis |
| ADB | Air Dried Basis |
| GCV | Gross Calorific Value |
| TM | Total Moisture |
| IM | Inherent Moisture |
| VM | Volatile Matter |
| FC | Fixed Carbon |
| TS | Total Sulphur |
| LRC | Low Rank Coal |
| MRC | Medium Rank Coal |
| COA | Certificate of Analysis |
| MT | Metric Ton |

### B. Formula Quick Reference

```
GCV_blend = Σ(GCV_i × %_i)
Ash_blend = Σ(Ash_i × %_i)
Sulphur_blend = Σ(TS_i × %_i)
Moisture_blend = Σ(TM_i × %_i)

Tonase_i = Total_Kuantitas × Persentase_i

Σ Persentase_i = 100%
```

---

**Dokumen ini dibuat untuk keperluan internal PLTU Tenayan**  
**© 2026 Sistem Manajemen Bahan Bakar Digital**

---

**Phase-3 verification (2026-05-10):** This formula is verified against
`.planning/intel/constraints.md` → CONS-blending-formula, CONS-blending-input-ranges,
CONS-blending-constraint-validation, CONS-blending-ai-output, CONS-blending-tolerance.
No drift detected. See `docs/audit/SMART_BLENDING_FORMULA_AUDIT.md` for the full audit log.

**Operational status:** Smart Blending AI is operationally degraded — the formula and code
path are correct, but the Universal LLM Key budget is exhausted (BudgetExceededError).
Live recommendations are blocked until budget is restored (Phase 6, OPS-01).
See `documentation.md#known-issues` for the active Known Issues entry.

Verified against CONS-blending-formula (linear weighted-average, all 7 parameters),
CONS-blending-input-ranges (parameter ranges and defaults), CONS-blending-constraint-validation
(GCV ≥ target, Ash/Sulphur/TM/IM ≤ max, VM/FC ≥ min), CONS-blending-ai-output (JSON shape),
and CONS-blending-tolerance (±5% prediction tolerance).
