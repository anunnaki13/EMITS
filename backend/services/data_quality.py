from datetime import date, datetime, timezone
from typing import Any, Optional

from utils.database import db


DATA_QUALITY_RULES = {
    "stale_days": {
        "smartstock": 7,
        "sumberpemakaian": 7,
        "po_batubara": 30,
        "vessels": 30,
        "barges": 30,
        "trucking": 30,
        "biomassa": 30,
        "coa_reconciliation": 30,
    },
    "coa_delta_warning": 100,
    "coa_delta_critical": 150,
    "gcv_min": 2500,
    "gcv_max": 6000,
    "max_scan_docs": 5000,
    "sample_limit": 25,
}


MODULES = {
    "smartstock": {
        "collection": "smartstock",
        "label": "Smart Stock Penerimaan",
        "date_field": "date",
        "source_path": "/smart-stock/sumber-penerimaan",
        "duplicate_fields": ["date"],
        "numeric_fields": {
            "stock_awal": {"min": 0},
            "total_penerimaan": {"min": 0},
            "stock_akhir": {"min": 0},
        },
    },
    "sumberpemakaian": {
        "collection": "sumberpemakaian",
        "label": "Smart Stock Pemakaian",
        "date_field": "date",
        "source_path": "/smart-stock/sumber-pemakaian",
        "duplicate_fields": ["date"],
        "numeric_fields": {
            "total_pemakaian": {"min": 0},
            "stock_awal": {"min": 0},
        },
    },
    "po_batubara": {
        "collection": "po_batubara",
        "label": "PO Batubara",
        "date_field": "time_arrival",
        "source_path": "/po-batubara",
        "duplicate_fields": ["po_number", "no_jadwal"],
        "numeric_fields": {
            "tonase_po": {"min": 0},
            "total": {"min": 0},
        },
    },
    "vessels": {
        "collection": "vessels",
        "label": "Vessel TNY",
        "date_field": "completed_unloading",
        "source_path": "/vessel",
        "duplicate_fields": ["shipment_code"],
        "numeric_fields": {
            "bl_mt": {"min": 0},
            "ds_mt": {"min": 0},
            "gcv_arb": {"min": DATA_QUALITY_RULES["gcv_min"], "max": DATA_QUALITY_RULES["gcv_max"]},
        },
    },
    "barges": {
        "collection": "barges",
        "label": "Barge TNY",
        "date_field": "completed_unloading",
        "source_path": "/barge",
        "duplicate_fields": ["shipment_code"],
        "numeric_fields": {
            "bl_mt": {"min": 0},
            "ds_mt": {"min": 0},
            "gcv_arb": {"min": DATA_QUALITY_RULES["gcv_min"], "max": DATA_QUALITY_RULES["gcv_max"]},
        },
    },
    "trucking": {
        "collection": "trucking",
        "label": "Trucking TNY",
        "date_field": "completed_unloading",
        "source_path": "/trucking",
        "duplicate_fields": ["shipment_code"],
        "numeric_fields": {
            "ds_mt": {"min": 0},
            "gcv_arb": {"min": DATA_QUALITY_RULES["gcv_min"], "max": DATA_QUALITY_RULES["gcv_max"]},
        },
    },
    "biomassa": {
        "collection": "biomassa",
        "label": "Biomassa TNY",
        "date_field": "completed_unloading",
        "source_path": "/biomassa",
        "duplicate_fields": ["shipment_code"],
        "numeric_fields": {
            "jembatan_timbang_mt": {"min": 0},
            "gcv_arb": {"min": 1500, "max": DATA_QUALITY_RULES["gcv_max"]},
        },
    },
    "coa_reconciliation": {
        "collection": "coa_reconciliation",
        "label": "COA Reconciliation",
        "date_field": "completed_unloading",
        "source_path": "/coa-reconciliation",
        "duplicate_fields": ["shipment"],
        "numeric_fields": {
            "ds_mt": {"min": 0},
            "loading_gcv_arb": {"min": DATA_QUALITY_RULES["gcv_min"], "max": DATA_QUALITY_RULES["gcv_max"]},
            "unloading_gcv_arb": {"min": DATA_QUALITY_RULES["gcv_min"], "max": DATA_QUALITY_RULES["gcv_max"]},
            "internal_gcv_arb": {"min": DATA_QUALITY_RULES["gcv_min"], "max": DATA_QUALITY_RULES["gcv_max"]},
        },
    },
}


SEVERITY_ORDER = {"critical": 3, "warning": 2, "info": 1}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _date_prefix(value: Any) -> str:
    return str(value or "")[:10]


def _parse_date(value: Any) -> Optional[date]:
    prefix = _date_prefix(value)
    if not prefix:
        return None
    try:
        return date.fromisoformat(prefix)
    except ValueError:
        return None


def _days_since(value: Any) -> Optional[int]:
    parsed = _parse_date(value)
    if not parsed:
        return None
    return max((date.today() - parsed).days, 0)


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _source_label(record: dict, fields: list[str]) -> str:
    for field in ["shipment", "po_number", "no_jadwal", "shipment_code", "suppliers", "supplier_name", "date", *fields]:
        value = record.get(field)
        if value not in [None, ""]:
            return str(value)
    return record.get("id") or "record"


def _issue(
    *,
    module: str,
    collection: str,
    severity: str,
    issue_type: str,
    field: Optional[str],
    source_record_id: Optional[str],
    source_label: str,
    source_path: str,
    message: str,
    suggested_fix: str,
    metadata: Optional[dict] = None,
) -> dict:
    key_source = source_record_id or source_label
    return {
        "key": f"{collection}:{issue_type}:{field or 'record'}:{key_source}",
        "module": module,
        "collection": collection,
        "severity": severity,
        "type": issue_type,
        "field": field,
        "source_record_id": source_record_id,
        "source_label": source_label,
        "source_path": source_path,
        "message": message,
        "suggested_fix": suggested_fix,
        "metadata": metadata or {},
    }


def _missing_query(field: str) -> dict:
    return {"$or": [{field: {"$exists": False}}, {field: None}, {field: ""}]}


def _issue_sort_key(issue: dict):
    return (-SEVERITY_ORDER.get(issue.get("severity"), 0), issue.get("module", ""), issue.get("type", ""), issue.get("source_label", ""))


def _filter_issues(issues: list[dict], module: str = "all", severity: str = "all") -> list[dict]:
    filtered = issues
    if module and module != "all":
        filtered = [issue for issue in filtered if issue.get("module") == module or issue.get("collection") == module]
    if severity and severity != "all":
        filtered = [issue for issue in filtered if issue.get("severity") == severity]
    return sorted(filtered, key=_issue_sort_key)


def _summary(issues: list[dict], generated_at: Optional[str] = None) -> dict:
    counts = {
        "critical": sum(1 for issue in issues if issue.get("severity") == "critical"),
        "warning": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "info": sum(1 for issue in issues if issue.get("severity") == "info"),
    }
    counts["total"] = counts["critical"] + counts["warning"] + counts["info"]
    status = "healthy"
    if counts["critical"]:
        status = "critical"
    elif counts["warning"]:
        status = "warning"
    elif counts["info"]:
        status = "info"

    module_map: dict[str, dict] = {}
    for issue in issues:
        module = issue.get("module") or issue.get("collection") or "unknown"
        row = module_map.setdefault(module, {"module": module, "critical": 0, "warning": 0, "info": 0, "total": 0})
        severity = issue.get("severity") or "info"
        row[severity] = row.get(severity, 0) + 1
        row["total"] += 1

    caveats = []
    if counts["critical"]:
        caveats.append(f"{counts['critical']} issue critical kualitas data perlu ditindaklanjuti sebelum laporan dipakai final.")
    if counts["warning"]:
        caveats.append(f"{counts['warning']} warning kualitas data perlu direview.")
    if not caveats:
        caveats.append("Tidak ada issue kualitas data pada filter ini.")

    return {
        "status": status,
        "generated_at": generated_at or _now(),
        "counts": counts,
        "modules": sorted(module_map.values(), key=lambda item: (-item["total"], item["module"])),
        "caveats": caveats,
    }


async def _collect_stale_issues(module: str, config: dict) -> list[dict]:
    collection_name = config["collection"]
    collection = db[collection_name]
    date_field = config["date_field"]
    threshold = DATA_QUALITY_RULES["stale_days"].get(collection_name, 30)
    latest = await collection.find_one(
        {date_field: {"$nin": [None, ""]}},
        {"_id": 0, "id": 1, date_field: 1},
        sort=[(date_field, -1)],
    )
    if not latest:
        return [_issue(
            module=module,
            collection=collection_name,
            severity="warning",
            issue_type="stale_data",
            field=date_field,
            source_record_id=None,
            source_label=config["label"],
            source_path=config["source_path"],
            message=f"Belum ada tanggal valid untuk {config['label']}.",
            suggested_fix="Upload atau koreksi data terbaru dengan tanggal yang valid.",
            metadata={"threshold_days": threshold},
        )]
    age = _days_since(latest.get(date_field))
    if age is not None and age > threshold:
        return [_issue(
            module=module,
            collection=collection_name,
            severity="warning",
            issue_type="stale_data",
            field=date_field,
            source_record_id=latest.get("id"),
            source_label=_source_label(latest, [date_field]),
            source_path=config["source_path"],
            message=f"Data terbaru {config['label']} berumur {age} hari.",
            suggested_fix="Periksa apakah data periode terbaru sudah diinput atau upload ulang data terakhir.",
            metadata={"age_days": age, "threshold_days": threshold, "latest_date": latest.get(date_field)},
        )]
    return []


async def _collect_missing_date_issues(module: str, config: dict) -> list[dict]:
    collection_name = config["collection"]
    date_field = config["date_field"]
    docs = await db[collection_name].find(
        _missing_query(date_field),
        {"_id": 0, "id": 1, "shipment": 1, "po_number": 1, "no_jadwal": 1, "shipment_code": 1, "suppliers": 1, "supplier_name": 1},
    ).limit(DATA_QUALITY_RULES["sample_limit"]).to_list(DATA_QUALITY_RULES["sample_limit"])
    return [
        _issue(
            module=module,
            collection=collection_name,
            severity="warning",
            issue_type="missing_date",
            field=date_field,
            source_record_id=doc.get("id"),
            source_label=_source_label(doc, config.get("duplicate_fields") or []),
            source_path=config["source_path"],
            message=f"Tanggal {date_field} kosong pada {config['label']}.",
            suggested_fix="Lengkapi tanggal sumber agar filter periode dan tren tidak menyesatkan.",
        )
        for doc in docs
    ]


async def _collect_duplicate_issues(module: str, config: dict) -> list[dict]:
    fields = config.get("duplicate_fields") or []
    if not fields:
        return []
    collection_name = config["collection"]
    group_id = {field: f"${field}" for field in fields}
    non_empty = [{field: {"$nin": [None, ""]}} for field in fields]
    pipeline = [
        {"$match": {"$and": non_empty}},
        {"$group": {"_id": group_id, "count": {"$sum": 1}, "sample_id": {"$first": "$id"}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$limit": DATA_QUALITY_RULES["sample_limit"]},
    ]
    rows = await db[collection_name].aggregate(pipeline).to_list(DATA_QUALITY_RULES["sample_limit"])
    issues = []
    for row in rows:
        label = " / ".join(str(value) for value in (row.get("_id") or {}).values() if value not in [None, ""])
        issues.append(_issue(
            module=module,
            collection=collection_name,
            severity="warning",
            issue_type="duplicate_key",
            field=",".join(fields),
            source_record_id=row.get("sample_id"),
            source_label=label or config["label"],
            source_path=config["source_path"],
            message=f"Ditemukan {row.get('count', 0)} record duplikat untuk key {label or '-'} di {config['label']}.",
            suggested_fix="Gabungkan atau hapus data duplikat sebelum digunakan untuk laporan final.",
            metadata={"duplicate_count": row.get("count"), "key_fields": fields},
        ))
    return issues


async def _collect_numeric_issues(module: str, config: dict) -> list[dict]:
    numeric_fields = config.get("numeric_fields") or {}
    if not numeric_fields:
        return []
    projection = {"_id": 0, "id": 1, "shipment": 1, "po_number": 1, "no_jadwal": 1, "shipment_code": 1, "suppliers": 1, "supplier_name": 1}
    for field in numeric_fields:
        projection[field] = 1
    docs = await db[config["collection"]].find({}, projection).limit(DATA_QUALITY_RULES["max_scan_docs"]).to_list(DATA_QUALITY_RULES["max_scan_docs"])
    issues = []
    for doc in docs:
        for field, rule in numeric_fields.items():
            value = _safe_float(doc.get(field))
            if value is None:
                continue
            if "min" in rule and value < rule["min"]:
                issues.append(_issue(
                    module=module,
                    collection=config["collection"],
                    severity="critical",
                    issue_type="negative_or_unrealistic_value",
                    field=field,
                    source_record_id=doc.get("id"),
                    source_label=_source_label(doc, config.get("duplicate_fields") or []),
                    source_path=config["source_path"],
                    message=f"Nilai {field} bernilai {value:g}, di bawah batas minimum {rule['min']:g}.",
                    suggested_fix="Cek kembali angka sumber/import dan koreksi record sebelum dipakai untuk perhitungan.",
                    metadata={"value": value, "min": rule["min"]},
                ))
            elif "max" in rule and value > rule["max"]:
                issues.append(_issue(
                    module=module,
                    collection=config["collection"],
                    severity="warning",
                    issue_type="negative_or_unrealistic_value",
                    field=field,
                    source_record_id=doc.get("id"),
                    source_label=_source_label(doc, config.get("duplicate_fields") or []),
                    source_path=config["source_path"],
                    message=f"Nilai {field} bernilai {value:g}, di atas batas wajar {rule['max']:g}.",
                    suggested_fix="Validasi ulang nilai kualitas/tonase dari dokumen sumber.",
                    metadata={"value": value, "max": rule["max"]},
                ))
            if len(issues) >= DATA_QUALITY_RULES["sample_limit"] * max(len(numeric_fields), 1):
                return issues
    return issues


async def _collect_coa_delta_issues() -> list[dict]:
    fields = ["delta_loading_internal", "delta_unloading_internal", "delta_loading_unloading"]
    projection = {"_id": 0, "id": 1, "shipment": 1, "suppliers": 1, "status": 1, **{field: 1 for field in fields}}
    docs = await db.coa_reconciliation.find({}, projection).limit(DATA_QUALITY_RULES["max_scan_docs"]).to_list(DATA_QUALITY_RULES["max_scan_docs"])
    issues = []
    for doc in docs:
        for field in fields:
            value = _safe_float(doc.get(field))
            if value is None:
                continue
            delta = abs(value)
            if delta >= DATA_QUALITY_RULES["coa_delta_warning"]:
                severity = "critical" if delta >= DATA_QUALITY_RULES["coa_delta_critical"] else "warning"
                issues.append(_issue(
                    module="coa_reconciliation",
                    collection="coa_reconciliation",
                    severity=severity,
                    issue_type="coa_outlier_delta",
                    field=field,
                    source_record_id=doc.get("id"),
                    source_label=_source_label(doc, ["shipment"]),
                    source_path="/coa-reconciliation",
                    message=f"Delta COA {doc.get('shipment') or '-'} mencapai {delta:g}.",
                    suggested_fix="Validasi nilai loading/unloading/internal dan lanjutkan dispute atau umpire bila bukti lengkap.",
                    metadata={"delta": delta, "warning_threshold": DATA_QUALITY_RULES["coa_delta_warning"], "critical_threshold": DATA_QUALITY_RULES["coa_delta_critical"]},
                ))
                break
    return issues


async def collect_data_quality_issues() -> list[dict]:
    issues: list[dict] = []
    for module, config in MODULES.items():
        issues.extend(await _collect_stale_issues(module, config))
        issues.extend(await _collect_missing_date_issues(module, config))
        issues.extend(await _collect_duplicate_issues(module, config))
        issues.extend(await _collect_numeric_issues(module, config))
    issues.extend(await _collect_coa_delta_issues())
    return sorted(issues, key=_issue_sort_key)


async def build_data_quality_report(module: str = "all", severity: str = "all", limit: int = 100) -> dict:
    generated_at = _now()
    all_issues = await collect_data_quality_issues()
    filtered = _filter_issues(all_issues, module=module, severity=severity)
    summary = _summary(filtered, generated_at)
    return {
        **summary,
        "filter_scope": {"module": module or "all", "severity": severity or "all", "limit": limit},
        "rule_config": DATA_QUALITY_RULES,
        "issues": filtered[:limit],
        "total_issues": len(filtered),
    }


async def build_data_quality_export_rows(module: str = "all", severity: str = "all") -> list[dict]:
    issues = _filter_issues(await collect_data_quality_issues(), module=module, severity=severity)
    return [
        {
            "severity": issue.get("severity"),
            "module": issue.get("module"),
            "type": issue.get("type"),
            "field": issue.get("field"),
            "source_record_id": issue.get("source_record_id"),
            "source_label": issue.get("source_label"),
            "message": issue.get("message"),
            "suggested_fix": issue.get("suggested_fix"),
            "source_path": issue.get("source_path"),
        }
        for issue in issues
    ]


async def build_data_quality_caveat(module: str = "all", limit: int = 5) -> dict:
    report = await build_data_quality_report(module=module, severity="all", limit=limit)
    return {
        "status": report["status"],
        "counts": report["counts"],
        "caveats": report["caveats"],
        "top_issues": report["issues"][:limit],
        "generated_at": report["generated_at"],
    }


def _preview_issue_severity(issue: dict) -> str:
    if issue.get("severity") in SEVERITY_ORDER:
        return issue["severity"]
    issue_type = str(issue.get("type") or "")
    if issue_type in {"missing_required_column", "missing_key", "duplicate_in_file"}:
        return "critical"
    if issue_type in {"duplicate_existing", "missing_completed_unloading", "missing_quality_value"}:
        return "warning"
    return "info"


def _preview_issue(dataset: str, issue: dict) -> dict:
    severity = _preview_issue_severity(issue)
    field = issue.get("field")
    row = issue.get("row")
    return {
        "key": f"import:{dataset}:{issue.get('type') or 'issue'}:{field}:{row}",
        "module": dataset,
        "collection": dataset,
        "severity": severity,
        "type": issue.get("type") or "import_issue",
        "field": field,
        "source_record_id": None,
        "source_label": f"Row {row}" if row else dataset,
        "source_path": "/po-batubara" if dataset == "po-batubara" else "/merit-order" if dataset == "merit-order" else "/coa-reconciliation",
        "message": issue.get("message") or "Issue kualitas data pada preview import.",
        "suggested_fix": "Perbaiki workbook sumber lalu ulangi preview sebelum commit.",
        "metadata": {"row": row},
    }


def summarize_import_quality(dataset: str, records: list[dict], issues: list[dict]) -> dict:
    quality_issues = [_preview_issue(dataset, issue) for issue in issues or []]
    for index, record in enumerate(records or [], start=2):
        numeric_checks = []
        if dataset == "po-batubara":
            numeric_checks = [("tonase_po", 0), ("total", 0)]
        elif dataset == "merit-order":
            numeric_checks = [("rp_kcal", 0), ("harga_cif", 0)]
        for field, minimum in numeric_checks:
            value = _safe_float(record.get(field))
            if value is not None and value < minimum:
                quality_issues.append(_issue(
                    module=dataset,
                    collection=dataset,
                    severity="critical",
                    issue_type="negative_or_unrealistic_value",
                    field=field,
                    source_record_id=record.get("id"),
                    source_label=f"Row {index}",
                    source_path="/po-batubara" if dataset == "po-batubara" else "/merit-order",
                    message=f"Nilai {field} pada row {index} bernilai negatif.",
                    suggested_fix="Koreksi angka pada workbook sumber sebelum commit.",
                    metadata={"row": index, "value": value},
                ))
    summary = _summary(quality_issues)
    return {**summary, "issues": sorted(quality_issues, key=_issue_sort_key)[:25], "total_issues": len(quality_issues)}


def summarize_coa_preview_quality(preview: dict) -> dict:
    issues = [_preview_issue("coa-reconciliation", issue) for issue in preview.get("issues") or []]
    validation_summary = preview.get("validation_summary") or {}
    if validation_summary.get("critical", 0) > 0 and not any(issue["severity"] == "critical" for issue in issues):
        issues.append(_issue(
            module="coa-reconciliation",
            collection="coa_reconciliation",
            severity="critical",
            issue_type="coa_import_critical_summary",
            field=None,
            source_record_id=None,
            source_label="COA preview",
            source_path="/coa-reconciliation",
            message=f"Preview COA memiliki {validation_summary.get('critical')} issue critical.",
            suggested_fix="Perbaiki issue critical pada workbook sebelum commit.",
        ))
    summary = _summary(issues)
    return {**summary, "issues": sorted(issues, key=_issue_sort_key)[:25], "total_issues": len(issues)}
