# Deployment Guide (VPS)

Dokumen ini menjelaskan cara deploy aplikasi PLTU Tenayan Fuel Management System ke VPS Linux secara detail. Panduan di bawah mengasumsikan arsitektur produksi yang stabil dan mudah dirawat:

- Frontend React dibuild menjadi static files
- Backend FastAPI berjalan sebagai service systemd di port internal
- Nginx menangani domain publik, SSL, static frontend, dan reverse proxy `/api`
- MongoDB berjalan di VPS yang sama atau server terpisah

Dokumen ini ditulis untuk deployment manual di VPS, bukan workflow preview.

## 1. Arsitektur Deployment yang Direkomendasikan

```text
Internet
   |
   v
Nginx (80/443)
   |---- /api/*  -> FastAPI Uvicorn (127.0.0.1:8013)
   |
   ---- /*      -> React build static files (/var/www/emits)

FastAPI
   |
   v
MongoDB
```

### Catatan: Postur VPS Produksi Saat Ini (2026-05-13)

Panduan umum ini menggunakan port internal standar **8013** untuk artefak operasional EMITS:

- Backend uvicorn: port **8013**, dikelola via systemd template `ops/systemd/emits-backend.service.example`
- Frontend: React static build disajikan nginx dari `/var/www/emits`
- Nginx: `ops/nginx/emits.conf.example` reverse-proxy `/api/*` ke `127.0.0.1:8013`
- MongoDB: `localhost:27017` (single-host, bukan MongoDB Atlas/external)
- `REACT_APP_BACKEND_URL`: origin publik nginx jika sudah aktif, atau `http://103.150.197.225:8013` sebagai fallback langsung

Runbook kanonis Phase 22: [docs/operations/PRODUCTION_RUNBOOK.md](docs/operations/PRODUCTION_RUNBOOK.md).

---

## 2. Spesifikasi VPS Minimum

Rekomendasi minimum untuk produksi kecil-menengah:
- Ubuntu 22.04 LTS atau 24.04 LTS
- 2 vCPU
- 4 GB RAM
- 40+ GB SSD
- 1 domain/subdomain publik

Jika trafik, upload, dan data meningkat:
- 4 vCPU
- 8 GB RAM
- storage lebih besar
- MongoDB dipisah ke server/managed service

## 3. Komponen yang Dibutuhkan

Install komponen berikut:
- `nginx`
- `python3`, `python3-venv`, `python3-pip`
- `nodejs`
- `yarn`
- `git`
- `mongodb` atau akses ke MongoDB eksternal
- `certbot` + plugin nginx untuk SSL

Contoh install awal di Ubuntu:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx python3 python3-venv python3-pip git curl certbot python3-certbot-nginx
```

### Install Node.js dan Yarn
Gunakan Node LTS.

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g yarn
```

## 4. Struktur Direktori yang Direkomendasikan

```text
/opt/pltu-tenayan/
├── app/                     # source code project
│   ├── backend/
│   └── frontend/
├── venv/                    # virtualenv python backend
└── logs/

/var/www/
└── emits/                   # hasil yarn build frontend untuk static nginx
```

## 5. Clone Source Code

```bash
sudo mkdir -p /opt/pltu-tenayan
sudo chown -R $USER:$USER /opt/pltu-tenayan
cd /opt/pltu-tenayan
git clone <REPO_URL> app
```

Jika source sudah didapat dari zip/manual copy, letakkan project pada:
- `/opt/pltu-tenayan/app`

## 6. Setup Backend

### 6.1 Buat Virtual Environment

```bash
cd /opt/pltu-tenayan
python3 -m venv venv
source /opt/pltu-tenayan/venv/bin/activate
pip install --upgrade pip
pip install -r /opt/pltu-tenayan/app/backend/requirements.txt
```

### 6.2 File Environment Backend
Buat file:
- `/opt/pltu-tenayan/app/backend/.env`

Contoh isi:

```env
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=pltu_tenayan
JWT_SECRET=ganti-dengan-secret-yang-kuat
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
OPENROUTER_API_KEY=isi-jika-memakai-default-global-key
APP_VERSION=2026.03
APP_BUILD_ID=<git-commit-or-build-id>
APP_ENV=production
FRONTEND_STATIC_ROOT=/var/www/emits
SMOKE_EVIDENCE_DIR=/var/log/emits/smoke
```

Catatan penting:
- jangan gunakan fallback default jika environment penting belum tersedia
- `MONGO_URL` dan `DB_NAME` wajib benar
- `CORS_ORIGINS` harus memuat domain frontend publik
- jika user memakai custom AI key per user, `OPENROUTER_API_KEY` tetap berguna sebagai default backend

### 6.3 Uji Backend Manual

```bash
source /opt/pltu-tenayan/venv/bin/activate
cd /opt/pltu-tenayan/app/backend
uvicorn server:app --host 127.0.0.1 --port 8013
```

Tes cepat:

```bash
curl http://127.0.0.1:8013/api/health
```

Jika response sehat, hentikan proses manual dan lanjut ke systemd.

## 7. Setup Frontend

### 7.1 File Environment Frontend
Buat file:
- `/opt/pltu-tenayan/app/frontend/.env`

Contoh isi jika frontend dan backend berada di domain yang sama:

```env
REACT_APP_BACKEND_URL=https://your-domain.com
```

Untuk fallback langsung jika nginx/domain belum aktif:
```env
REACT_APP_BACKEND_URL=http://103.150.197.225:8013
```

Untuk jalur produksi static nginx, gunakan origin nginx yang sama dengan frontend. Nginx akan mem-proxy `/api/*` ke backend internal.

Untuk dev lokal:
```env
REACT_APP_BACKEND_URL=http://localhost:8013
```

Penting:
- backend route harus tetap dipanggil dengan prefix `/api`
- nilai ini harus domain publik, bukan `localhost` (kecuali untuk dev lokal)

### 7.2 Install Dependency dan Build

```bash
cd /opt/pltu-tenayan/app/frontend
yarn install
yarn build
```

### 7.3 Salin Build ke Direktori Web

```bash
sudo mkdir -p /var/www/emits
sudo rsync -av --delete /opt/pltu-tenayan/app/frontend/build/ /var/www/emits/
```

---

## 8. Setup MongoDB

### Opsi A — MongoDB Lokal di VPS
Install MongoDB Community Edition sesuai versi Ubuntu. Setelah terpasang:

```bash
sudo systemctl enable mongod
sudo systemctl start mongod
sudo systemctl status mongod
```

Tes koneksi lokal:

```bash
mongosh --eval 'db.runCommand({ ping: 1 })'
```

### Opsi B — MongoDB Eksternal / Managed
Gunakan connection string penuh pada `MONGO_URL`, misalnya:

# Set MONGO_URL in backend/.env; example shape mongodb://localhost:27017 (single-host VPS topology per ADR-001).
```env
MONGO_URL=${MONGO_URL}
DB_NAME=pltu_tenayan
```

### Rekomendasi keamanan MongoDB
- jangan buka port MongoDB ke publik jika tidak diperlukan
- gunakan bind internal/private network
- aktifkan auth jika instalasi mandiri
- backup database secara berkala

---

## 9. Menjalankan Backend dengan systemd

Template siap pakai ada di `ops/systemd/emits-backend.service.example`. Salin template tersebut ke `/etc/systemd/system/emits-backend.service`, lalu sesuaikan path jika instalasi tidak memakai `/opt/pltu-tenayan/app`.

Buat service file:
- `/etc/systemd/system/pltu-tenayan-backend.service`

Isi contoh:

```ini
[Unit]
Description=PLTU Tenayan Backend FastAPI
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/pltu-tenayan/app/backend
Environment="PATH=/opt/pltu-tenayan/venv/bin"
ExecStart=/opt/pltu-tenayan/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8013
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Set permission yang sesuai:

```bash
sudo chown -R www-data:www-data /opt/pltu-tenayan
sudo systemctl daemon-reload
sudo systemctl enable pltu-tenayan-backend
sudo systemctl start pltu-tenayan-backend
sudo systemctl status pltu-tenayan-backend
```

Lihat log backend:

```bash
journalctl -u pltu-tenayan-backend -f
```

---

## 10. Setup Nginx

Template siap pakai ada di `ops/nginx/emits.conf.example`. Template ini menggunakan backend port `8013`, React static root `/var/www/emits`, dan upload limit `100M`.

Buat file config:
- `/etc/nginx/sites-available/pltu-tenayan`

Contoh konfigurasi:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    root /var/www/emits;
    index index.html;

    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://127.0.0.1:8013/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    location / {
        try_files $uri /index.html;
    }
}
```

Aktifkan site:

```bash
sudo ln -s /etc/nginx/sites-available/pltu-tenayan /etc/nginx/sites-enabled/pltu-tenayan
sudo nginx -t
sudo systemctl reload nginx
```

### Catatan penting React Router
Baris berikut wajib ada agar route frontend seperti `/dashboard` tidak 404 saat refresh:

```nginx
try_files $uri /index.html;
```

### Catatan upload file
Karena aplikasi memiliki upload Excel, pastikan `client_max_body_size` cukup besar. Sesuaikan jika file cenderung besar, misalnya `50M` atau `100M`.

---

## 11. Setup SSL dengan Certbot

Jika DNS domain sudah mengarah ke VPS:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Setelah sukses, certbot akan memperbarui konfigurasi Nginx menjadi HTTPS.

Verifikasi auto-renew:

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

---

## 12. Checklist Verifikasi Setelah Deploy

Phase 19 menyediakan smoke check otomatis:

```bash
cd /opt/pltu-tenayan/app
set -a
. backend/.env
set +a
backend/.venv/bin/python ops/scripts/smoke_check.py \
  --base-url http://127.0.0.1:8013 \
  --frontend-url http://127.0.0.1 \
  --json-output /var/log/emits/smoke/manual-smoke-$(date -u +%Y%m%dT%H%M%SZ).json
```

Smoke check ini mencakup frontend, backend health, MongoDB, login, dashboard, COA, dan management report.

Untuk status gabungan backend, static nginx, systemd, nginx config, disk, backup, dan smoke evidence:

```bash
cd /opt/pltu-tenayan/app
ops/scripts/runtime_status.sh
```

### 12.1 Cek service
```bash
sudo systemctl status pltu-tenayan-backend
sudo systemctl status nginx
sudo systemctl status mongod
```

### 12.2 Cek endpoint backend
```bash
curl https://your-domain.com/api/health
```

### 12.3 Cek frontend
Buka:
- `https://your-domain.com/login`
- `https://your-domain.com/dashboard`

### 12.4 Cek login API
# Source from gitignored memory/test_credentials.md — see docs/audit/CREDENTIAL_HYGIENE.md
```bash
curl -X POST "http://103.150.197.225:8013/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"${TEST_ADMIN_PASSWORD}\"}"
```

### 12.5 Cek upload dan export
- Upload Excel pada salah satu halaman data
- Export COA PDF/Excel
- Cek Smart Blending AI bila `OPENROUTER_API_KEY` tersedia dan budget cukup

---

## 13. Prosedur Update Deployment

Phase 19 menyediakan helper deploy repeatable:

```bash
cd /opt/pltu-tenayan/app
ops/scripts/deploy.sh
```

Script tersebut melakukan clean-tree check, `git pull --ff-only`, pre-deploy `mongodump`, install dependency backend, build frontend, publish static build, restart backend, reload nginx, dan menjalankan smoke check.

Saat ada update kode baru:

```bash
cd /opt/pltu-tenayan/app
git pull
```

### Update backend dependency (jika berubah)
```bash
source /opt/pltu-tenayan/venv/bin/activate
pip install -r /opt/pltu-tenayan/app/backend/requirements.txt
```

### Rebuild frontend
```bash
cd /opt/pltu-tenayan/app/frontend
yarn install
yarn build
sudo rsync -av --delete /opt/pltu-tenayan/app/frontend/build/ /var/www/emits/
```

### Restart backend dan reload nginx
```bash
sudo systemctl restart pltu-tenayan-backend
sudo systemctl reload nginx
```

---

## 14. Strategi Backup

### 14.1 Backup MongoDB
Contoh backup harian:

```bash
mkdir -p /opt/pltu-tenayan/backups
mongodump --uri="mongodb://127.0.0.1:27017" --db pltu_tenayan --out /opt/pltu-tenayan/backups/$(date +%F)
```

### 14.2 Backup source dan env
Backup juga:
- `/opt/pltu-tenayan/app/backend/.env`
- `/opt/pltu-tenayan/app/frontend/.env`
- file Nginx site config
- systemd service file

### 14.3 Rotasi backup
Gunakan cron untuk backup dan hapus backup lama secara berkala.

---

## 15. Hardening dan Keamanan

Rekomendasi minimum:
- gunakan firewall `ufw`
- buka hanya port `80`, `443`, dan `22`
- nonaktifkan login password SSH, gunakan key-based auth
- gunakan `JWT_SECRET` yang kuat dan unik
- jangan expose MongoDB ke publik
- batasi size upload sesuai kebutuhan
- log error backend dan awasi brute force login

Contoh UFW:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 16. Monitoring dan Logging

### Backend
```bash
journalctl -u pltu-tenayan-backend -f
```

### Nginx
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Resource server
```bash
htop
df -h
free -m
```

---

## 17. Troubleshooting Umum

### 17.1 Frontend blank page
Penyebab umum:
- `REACT_APP_BACKEND_URL` salah saat build
- build frontend belum disalin ke direktori Nginx
- route fallback React belum dikonfigurasi

Cek:
```bash
cat /opt/pltu-tenayan/app/frontend/.env
sudo ls -la /var/www/emits
sudo nginx -t
```

### 17.2 Login gagal / 401
Penyebab umum:
- user belum ada di database
- `JWT_SECRET` berubah setelah token lama dibuat
- backend tidak bisa membaca database yang benar

Cek:
```bash
journalctl -u pltu-tenayan-backend -f
```

### 17.3 Request `/api/*` 502 Bad Gateway
Penyebab umum:
- backend mati
- uvicorn gagal start
- dependency belum terinstall
- `.env` backend belum lengkap

Cek:
```bash
sudo systemctl status pltu-tenayan-backend
journalctl -u pltu-tenayan-backend -n 100 --no-pager
curl http://127.0.0.1:8013/api/health
```

### 17.4 Upload Excel gagal
Penyebab umum:
- `client_max_body_size` terlalu kecil
- parser gagal membaca format Excel
- dependency parser belum lengkap

Cek:
- log backend
- ukuran file
- sheet/format aktual file

### 17.5 Smart Blending AI gagal
Penyebab umum:
- `OPENROUTER_API_KEY` tidak tersedia
- budget Universal Key habis
- user settings AI tidak valid

---

## 18. Deployment Checklist Ringkas

Sebelum go-live, pastikan:
- [ ] DNS domain sudah mengarah ke VPS
- [ ] Backend `.env` sudah benar
- [ ] Frontend `.env` sudah berisi domain publik
- [ ] MongoDB dapat diakses dari backend
- [ ] `uvicorn` berjalan di port internal `8013`
- [ ] Nginx proxy `/api` ke backend
- [ ] React build sudah disalin ke `/var/www/emits` untuk static nginx
- [ ] SSL aktif
- [ ] Login berhasil
- [ ] Upload Excel berhasil
- [ ] Export PDF/Excel berhasil
- [ ] Backup dasar tersedia
- [ ] Monitoring log aktif

---

## 19. Rekomendasi Pengembangan Deployment Berikutnya

Jika aplikasi berkembang lebih besar, langkah evolusi berikutnya yang disarankan:
- pisahkan MongoDB ke managed database
- tambah reverse proxy cache dan rate limit dasar
- tambah CI/CD build pipeline
- gunakan object storage untuk file upload besar
- tambahkan observability (Sentry, metrics, uptime monitor)
- buat script deploy otomatis

---

## 20. Kesimpulan

Untuk tahap sekarang, model deployment paling stabil adalah satu VPS dengan Nginx + systemd + FastAPI + MongoDB, dengan frontend React dibuild statis. Struktur ini sederhana, mudah di-debug, murah untuk awal, dan sudah cukup baik untuk aplikasi operasional internal maupun semi-produksi selama backup, SSL, logging, dan kontrol environment dijaga dengan benar.

---

## 21. Service Recovery (post-restart)

Untuk post-restart atau operasi berulang, gunakan runbook kanonis:

- [docs/operations/PRODUCTION_RUNBOOK.md](docs/operations/PRODUCTION_RUNBOOK.md)
- `sudo systemctl restart emits-backend`
- `sudo systemctl reload nginx`
- `backend/.venv/bin/python ops/scripts/smoke_check.py --base-url http://127.0.0.1:8013 --frontend-url http://127.0.0.1`
- `ops/scripts/runtime_status.sh`
