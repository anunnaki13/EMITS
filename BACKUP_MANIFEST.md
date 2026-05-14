# BACKUP_MANIFEST.md

- Tipe backup: full application snapshot
- Isi utama:
  - source code frontend dan backend
  - backend/.env asli
  - frontend/.env.example
  - dependency/cache/build yang tersedia saat backup dibuat
  - `database_backup.zip` (mongodump BSON + export JSON per collection + metadata)
  - dokumentasi proyek
  - `LOCAL_SETUP.md`
- Tidak disertakan:
  - `frontend/.env` asli
  - folder download publik lama agar paket tidak recursive
  - legacy generated development metadata folders
