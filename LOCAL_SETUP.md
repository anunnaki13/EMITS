# LOCAL_SETUP.md

Dokumen ini menjelaskan cara menjalankan hasil backup aplikasi PLTU Tenayan Fuel Management System di mesin lokal Anda.

## 1. Isi Backup

Backup full ini dirancang untuk memuat:
- source code frontend dan backend
- `backend/.env` asli dari environment saat backup dibuat
- `frontend/.env.example`
- dependency frontend (`node_modules`) bila tersedia
- cache/build yang ada saat backup dibuat
- `database_backup.zip` berisi dump database aktif saat backup dibuat
- dokumentasi proyek

## 2. Prasyarat Lokal

Siapkan komponen berikut di komputer lokal Anda:
- Python 3.11+
- Node.js LTS
- Yarn
- MongoDB Community Edition
- `mongorestore` / `mongosh`

## 3. Ekstrak Backup

1. Ekstrak file backup ZIP utama ke folder lokal, misalnya:
   - `D:\projects\pltu-tenayan`
   - atau `/Users/yourname/projects/pltu-tenayan`
2. Pastikan Anda melihat struktur seperti:
   - `backend/`
   - `frontend/`
   - `database_backup.zip`
   - `LOCAL_SETUP.md`
   - file dokumentasi lainnya

## 4. Restore Database

### 4.1 Ekstrak database backup
Ekstrak `database_backup.zip` ke folder lokal, misalnya:

```bash
unzip database_backup.zip -d database_backup
```

Isi yang diharapkan di dalamnya:
- `mongodump/` atau folder dump database BSON
- `json_export/` atau export JSON per collection
- `metadata/` atau file ringkasan collection

### 4.2 Jalankan MongoDB lokal
Contoh Linux/macOS:

```bash
mongod --dbpath /path/to/your/mongodb-data
```

Atau gunakan service MongoDB lokal yang sudah terpasang.

### 4.3 Restore via mongorestore (disarankan)
Jika folder dump BSON tersedia, jalankan:

```bash
mongorestore --drop --db nama_database_lokal ./database_backup/mongodump/nama_database_backup
```

Catatan:
- Ganti `nama_database_lokal` dengan nama database tujuan di mesin lokal Anda.
- Ganti `nama_database_backup` dengan nama folder database hasil ekstrak dump.
- Untuk melihat nama database backup asli, cek `database_backup/metadata/summary.json` atau `backend/.env`.

### 4.4 Opsi review manual via JSON
Jika Anda hanya ingin review data tanpa restore penuh, buka folder export JSON pada backup database.

## 5. Konfigurasi Environment

### 5.1 Backend
Backup ini sudah menyertakan `backend/.env` asli dari environment saat backup dibuat.

Langkah review:
1. Buka `backend/.env`
2. Sesuaikan `MONGO_URL` agar mengarah ke MongoDB lokal Anda jika diperlukan
3. Pastikan `DB_NAME` sesuai dengan database hasil restore

Contoh lokal umum:

```env
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=pltu_tenayan
```

### 5.2 Frontend
Backup ini **tidak** menyertakan `frontend/.env` asli, tetapi menyertakan `frontend/.env.example`.

Buat file baru:

```bash
cp frontend/.env.example frontend/.env
```

Lalu sesuaikan nilainya untuk lokal, contoh:

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 6. Menjalankan Backend Lokal

Masuk ke folder backend:

```bash
cd backend
```

Buat virtual environment bila perlu:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependency jika Anda tidak ingin memakai environment hasil backup:

```bash
pip install -r requirements.txt
```

Jalankan backend:

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

Tes health check:

```bash
curl http://localhost:8001/api/health
```

## 7. Menjalankan Frontend Lokal

Masuk ke folder frontend:

```bash
cd frontend
```

Jika `node_modules` sudah ikut dalam backup, Anda bisa langsung mencoba:

```bash
yarn start
```

Jika dependency perlu disegarkan:

```bash
yarn install
yarn start
```

Frontend biasanya berjalan di:
- `http://localhost:3000`

## 8. Alur Menjalankan Secara Lokal

Urutan aman:
1. Jalankan MongoDB lokal
2. Restore database
3. Sesuaikan `backend/.env`
4. Jalankan backend di port `8001`
5. Buat `frontend/.env` dari `frontend/.env.example`
6. Jalankan frontend di port `3000`
7. Login dan review aplikasi

## 9. Kredensial Pengujian

Kredensial pengujian (admin / operator / viewer) hanya tersimpan secara lokal di
`pltu-tenayan-full-backup/memory/test_credentials.md` (gitignored, per AUTHFIX-05 dan
`docs/audit/CREDENTIAL_HYGIENE.md`). Jangan menulis ulang nilai literalnya di file
manapun yang dilacak git.

Cara menggunakan tanpa membocorkan nilai:

```bash
# Dari root inner repo
export TEST_ADMIN_EMAIL="$(awk '$0=="## Akun Admin"{in_section=1;next} in_section && /^## /{exit} in_section && /Email:/{sub(/^- Email:[[:space:]]*/,"");print;exit}' memory/test_credentials.md)"
export TEST_ADMIN_PASSWORD="$(awk '$0=="## Akun Admin"{in_section=1;next} in_section && /^## /{exit} in_section && /Password:/{sub(/^- Password:[[:space:]]*/,"");print;exit}' memory/test_credentials.md)"
# ... pakai $TEST_ADMIN_EMAIL / $TEST_ADMIN_PASSWORD pada perintah curl/login Anda ...
unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD
```

Jika `memory/test_credentials.md` belum ada di mesin lokal Anda, salin/sinkronkan
dari sumber operasional (mis. file backup terenkripsi atau channel tertutup). Jangan
commit isinya ke repo manapun.

## 10. Troubleshooting

### Backend tidak bisa konek MongoDB
- Pastikan MongoDB lokal aktif
- Pastikan `MONGO_URL` benar
- Pastikan `DB_NAME` sesuai dengan database hasil restore

### Frontend tidak bisa login / memanggil API
- Pastikan `frontend/.env` sudah dibuat
- Pastikan `REACT_APP_BACKEND_URL=http://localhost:8001`
- Pastikan backend aktif dan endpoint `/api/health` berjalan

### `mongorestore` gagal
- Cek apakah folder dump sudah diekstrak dengan benar
- Pastikan nama DB target valid
- Gunakan opsi `--drop` bila ingin overwrite total database lokal

### Dependency frontend bermasalah
- Hapus `node_modules` lalu jalankan ulang `yarn install`

### Smart Blending AI error
- Ini bisa terjadi jika key AI / budget tidak tersedia di environment lokal Anda
- Review fitur lain tetap bisa dilakukan tanpa AI berjalan sempurna

## 11. Rekomendasi Review Lokal

Untuk review cepat, cek urutan ini:
1. Login
2. Dashboard
3. Vessel / Barge / Trucking / Biomassa
4. Smart Stock
5. Laporan
6. COA Reconciliation
7. Export PDF/Excel
8. AI Intelligence dan Smart Blending

## 12. Catatan Penting

- Backup ini adalah snapshot dari kondisi saat file dibuat, bukan sinkronisasi live berkelanjutan.
- Jika Anda ingin saya buat paket backup kedua yang lebih ringan untuk tim developer lain, saya bisa buat versi tanpa cache/dependency.
- Jika Anda ingin saya buat paket restore script otomatis (`restore_local.sh` / `restore_local.ps1`), saya juga bisa siapkan.

## VPS Service Recovery (post-restart)

Promoted from `docs/audit/LOGIN_BUG_RESOLUTION.md` (Phase-2 plan 02-04, "VPS-restart note") per
Phase-3 D-11. Use this runbook when the VPS at `103.150.197.225` reboots and the FastAPI
backend (port 8013) and CRA frontend (port 3013) are no longer responding. Cross-reference:
`.planning/phases/02-authentication-stabilization/VERIFICATION.md` (SS-04 Phase-3 carry-forward).

### When to use

- `curl -fsS http://103.150.197.225:8013/api/health` returns connection-refused or non-2xx.
- The frontend at `http://103.150.197.225:3013/` shows a connection-refused / proxy error
  after a host reboot.
- `systemctl status mongod` should already report `active (running)` — MongoDB auto-starts
  via systemd. If it does not, start it first: `sudo systemctl start mongod` (the FastAPI
  backend will fail to connect otherwise).

### 1. Restore the backend (FastAPI / uvicorn on port 8013)

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup/backend

# Activate the project venv
source .venv/bin/activate

# Source the backend environment (JWT_SECRET, MONGO_URL, DB_NAME, CORS_ORIGINS, OPENROUTER_API_KEY, ...)
# Use `set -a` so the values export into the subprocess; never echo them.
set -a
. ./.env
set +a

# Start uvicorn on the production port. `--reload` is fine for the VPS dev posture today.
nohup ./.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8013 \
  >> /home/damnation/emits/logs/backend.log 2>&1 &

# Verify
sleep 2
curl -fsS http://localhost:8013/api/health
# Expected: HTTP 200 + JSON body with status indicator
```

### 2. Restore the frontend (CRA / craco on port 3013)

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup/frontend

# The frontend's REACT_APP_BACKEND_URL is read from frontend/.env at build/start time.
# Confirm it points at port 8013 (not 8001) before starting; if it doesn't, edit .env first.
grep -E '^REACT_APP_BACKEND_URL=' .env

nohup yarn start \
  >> /home/damnation/emits/logs/frontend.log 2>&1 &

# CRA will print a "Compiled successfully!" line in the log when ready (typically 30-90s on VPS).
# Verify
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3013/
# Expected: 200
```

### 3. Smoke-test login end-to-end

```bash
# Source admin credentials from the local (gitignored) memory/test_credentials.md
cd /home/damnation/emits/pltu-tenayan-full-backup
export TEST_ADMIN_EMAIL="$(awk '/^## Akun Admin$/,/^##/{ if(/Email:/){sub(/^- Email:[[:space:]]*/,"");print;exit} }' memory/test_credentials.md)"
export TEST_ADMIN_PASSWORD="$(awk '/^## Akun Admin$/,/^##/{ if(/Password:/){sub(/^- Password:[[:space:]]*/,"");print;exit} }' memory/test_credentials.md)"

# Login probe — expect HTTP 200 + access_token in response
curl -fsS -X POST http://localhost:8013/api/auth/login \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json,os;print(json.dumps({'email':os.environ['TEST_ADMIN_EMAIL'],'password':os.environ['TEST_ADMIN_PASSWORD']}))")" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK' if d.get('access_token') else 'FAIL'); print('user:', d.get('user', {}).get('email'))"

unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD
```

### Auto-restart units

Phase 19 ships production hardening artefacts:

- `ops/systemd/emits-backend.service.example` for backend auto-restart on port `8013`
- `ops/nginx/emits.conf.example` for static frontend + `/api` reverse proxy
- `ops/scripts/smoke_check.py` for post-restart verification
- `docs/operations/PRODUCTION_RUNBOOK.md` as the canonical deploy/restart/rollback runbook

MongoDB itself should already auto-start via systemd (`systemctl status mongod`).

### Cross-references

- Original procedure: `pltu-tenayan-full-backup/docs/audit/LOGIN_BUG_RESOLUTION.md` "VPS-restart note (Phase-3 follow-up trigger)" (lines 26-42).
- Backend env contract: `backend/.env` (gitignored; `JWT_SECRET`, `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`, optional `OPENROUTER_API_KEY`).
- Credential hygiene: `docs/audit/CREDENTIAL_HYGIENE.md` — never inline JWTs, MongoDB URIs with credentials, or admin passwords in this runbook.
