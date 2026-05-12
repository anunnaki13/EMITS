import requests


ACTIVE_BACKUP_COLLECTIONS = {
    "users",
    "user_settings",
    "audit_logs",
    "vessels",
    "barges",
    "trucking",
    "biomassa",
    "po_batubara",
    "merit_order",
    "smartstock",
    "sumberpemakaian",
    "coa_reconciliation",
    "app_settings",
    "ai_chat_history",
}


def test_admin_backup_returns_all_active_collections_without_mongo_ids(base_url, admin_headers):
    response = requests.post(f"{base_url}/api/admin/backup", headers=admin_headers, timeout=20)
    assert response.status_code == 200, response.text[:300]

    body = response.json()
    assert body["schema_version"] == 1
    assert body["application"] == "emits-pltu-tenayan"
    assert set(body["collections"].keys()) == ACTIVE_BACKUP_COLLECTIONS
    assert set(body["counts"].keys()) == ACTIVE_BACKUP_COLLECTIONS

    for collection_name, documents in body["collections"].items():
        assert isinstance(documents, list), collection_name
        assert body["counts"][collection_name] == len(documents)
        assert all("_id" not in document for document in documents)


def test_restore_rejects_missing_confirmation(base_url, admin_headers):
    backup_response = requests.post(f"{base_url}/api/admin/backup", headers=admin_headers, timeout=20)
    assert backup_response.status_code == 200, backup_response.text[:300]

    response = requests.post(
        f"{base_url}/api/admin/restore",
        headers=admin_headers,
        json={"confirmation": "restore", "backup": backup_response.json(), "dry_run": True},
        timeout=20,
    )
    assert response.status_code == 400
    assert "RESTORE" in response.json()["detail"]


def test_restore_dry_run_validates_complete_backup_without_writing(base_url, admin_headers):
    backup_response = requests.post(f"{base_url}/api/admin/backup", headers=admin_headers, timeout=20)
    assert backup_response.status_code == 200, backup_response.text[:300]
    backup = backup_response.json()

    response = requests.post(
        f"{base_url}/api/admin/restore",
        headers=admin_headers,
        json={"confirmation": "RESTORE", "backup": backup, "dry_run": True},
        timeout=20,
    )
    assert response.status_code == 200, response.text[:300]

    body = response.json()
    assert body["dry_run"] is True
    assert set(body["collections"]) == ACTIVE_BACKUP_COLLECTIONS
    assert body["counts"] == backup["counts"]


def test_restore_rejects_incomplete_backup(base_url, admin_headers):
    backup_response = requests.post(f"{base_url}/api/admin/backup", headers=admin_headers, timeout=20)
    assert backup_response.status_code == 200, backup_response.text[:300]
    backup = backup_response.json()
    backup["collections"].pop("vessels")

    response = requests.post(
        f"{base_url}/api/admin/restore",
        headers=admin_headers,
        json={"confirmation": "RESTORE", "backup": backup, "dry_run": True},
        timeout=20,
    )
    assert response.status_code == 400
    assert "tidak lengkap" in response.json()["detail"]


def test_managed_backup_settings_history_and_run(base_url, admin_headers):
    settings_response = requests.get(f"{base_url}/api/admin/backup/settings", headers=admin_headers, timeout=20)
    assert settings_response.status_code == 200, settings_response.text[:300]
    assert "settings" in settings_response.json()
    assert "health" in settings_response.json()

    update_response = requests.put(
        f"{base_url}/api/admin/backup/settings",
        headers=admin_headers,
        json={
            "enabled": False,
            "interval_hours": 24,
            "retention_days": 7,
            "max_backups": 3,
        },
        timeout=20,
    )
    assert update_response.status_code == 200, update_response.text[:300]
    assert update_response.json()["settings"]["max_backups"] == 3

    run_response = requests.post(f"{base_url}/api/admin/backup/run", headers=admin_headers, timeout=30)
    assert run_response.status_code == 200, run_response.text[:300]
    backup = run_response.json()["backup"]
    assert backup["status"] == "success"
    assert backup["total_documents"] >= 0
    assert backup["file_size_bytes"] > 0
    assert backup["counts"].keys() >= ACTIVE_BACKUP_COLLECTIONS

    history_response = requests.get(f"{base_url}/api/admin/backup/history", headers=admin_headers, timeout=20)
    assert history_response.status_code == 200, history_response.text[:300]
    assert any(item["id"] == backup["id"] for item in history_response.json()["items"])
