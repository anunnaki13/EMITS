from datetime import datetime, timezone
from typing import Optional

from services.management_reports import build_management_report


def _fmt(value, digits: int = 0, suffix: str = "") -> str:
    if value is None:
        return "-"
    try:
        formatted = f"{float(value):,.{digits}f}"
        return f"{formatted}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def _advisor_recommendations(report: dict) -> tuple[list[dict], list[str]]:
    recommendations = []
    refusals = []
    stock = report["stock"]
    arrivals = report["arrivals"]
    quality = report["quality"]
    disputes = report["disputes"]

    days_of_supply = stock.get("days_of_supply")
    if days_of_supply is None:
        refusals.append("Rekomendasi reorder stock tidak diberikan karena data pemakaian pada filter ini belum cukup untuk menghitung days of supply.")
    elif days_of_supply < 7:
        recommendations.append({
            "id": "stock-critical",
            "severity": "critical",
            "title": "Stock coverage kritis",
            "recommendation": "Aktifkan percepatan kedatangan terdekat dan review pemakaian harian sampai coverage kembali di atas 14 hari.",
            "source_slice": "stock_summary",
            "evidence": f"Days of supply {days_of_supply} hari; stok {_fmt(stock.get('current_stock'), 0, ' MT')}; burn rate {_fmt(stock.get('avg_daily_usage'), 0, ' MT/hari')}.",
            "next_steps": [
                "Cek jadwal PO yang at-risk.",
                "Prioritaskan supplier dengan realisasi paling cepat.",
                "Laporkan risiko coverage ke manajemen shift.",
            ],
        })
    elif days_of_supply < 14:
        recommendations.append({
            "id": "stock-warning",
            "severity": "warning",
            "title": "Stock mendekati threshold reorder",
            "recommendation": "Siapkan reorder atau percepatan pengiriman sebelum coverage turun di bawah 7 hari.",
            "source_slice": "stock_summary",
            "evidence": f"Days of supply {days_of_supply} hari dengan threshold operasional 14 hari.",
            "next_steps": ["Review jadwal 7 hari ke depan.", "Pastikan rencana pemakaian unit tidak naik mendadak."],
        })

    if arrivals.get("at_risk_count", 0) > 0 or arrivals.get("tonnage_gap", 0) > 0:
        recommendations.append({
            "id": "arrival-risk",
            "severity": "warning" if arrivals.get("at_risk_count", 0) < 3 else "critical",
            "title": "Jadwal kedatangan perlu follow-up",
            "recommendation": "Follow-up jadwal yang sudah melewati ETA dan cocokkan ulang dengan realisasi bongkar.",
            "source_slice": "arrival_schedule_vs_realization",
            "evidence": f"{arrivals.get('at_risk_count', 0)} jadwal at-risk; gap tonase {_fmt(arrivals.get('tonnage_gap'), 0, ' MT')}.",
            "next_steps": ["Hubungi PIC supplier/logistik.", "Update ETA aktual di PO Batubara.", "Cek apakah realisasi masuk di modul laporan."],
        })
    elif arrivals.get("scheduled_count", 0) == 0:
        refusals.append("Rekomendasi keterlambatan kedatangan tidak diberikan karena tidak ada jadwal PO pada filter ini.")

    if quality.get("critical_count", 0) > 0 or (quality.get("avg_coa_delta") or 0) >= 150:
        recommendations.append({
            "id": "coa-quality-risk",
            "severity": "critical" if quality.get("critical_count", 0) else "warning",
            "title": "Risiko kualitas COA tinggi",
            "recommendation": "Prioritaskan review COA critical/warning dan siapkan eskalasi umpire untuk shipment dengan delta terbesar.",
            "source_slice": "coa_quality_disputes",
            "evidence": f"{quality.get('critical_count', 0)} critical, {quality.get('warning_count', 0)} warning, avg delta {_fmt(quality.get('avg_coa_delta'), 0, ' kcal/kg')}.",
            "next_steps": ["Validasi data loading/internal.", "Cek attachment dan catatan dispute.", "Ajukan umpire jika bukti lengkap."],
        })
    elif quality.get("coa_records", 0) == 0:
        refusals.append("Rekomendasi COA tidak diberikan karena tidak ada record COA reconciliation pada filter ini.")

    if disputes.get("stale_count", 0) > 0:
        recommendations.append({
            "id": "stale-disputes",
            "severity": "warning",
            "title": "Dispute aktif mulai stale",
            "recommendation": "Tutup loop dispute/umpire yang berumur 7 hari atau lebih dengan PIC, target keputusan, dan tanggal follow-up.",
            "source_slice": "coa_quality_disputes",
            "evidence": f"{disputes.get('stale_count', 0)} dispute stale; aging tertua {disputes.get('oldest_active_aging_days') or '-'} hari.",
            "next_steps": ["Tag owner dispute.", "Minta update lab umpire.", "Masukkan status terbaru ke dispute monitor."],
        })

    if not recommendations and not report["data_health"]["empty"]:
        recommendations.append({
            "id": "monitor-normal",
            "severity": "info",
            "title": "Tidak ada risiko prioritas tinggi pada filter ini",
            "recommendation": "Lanjutkan monitoring rutin dan gunakan scorecard supplier untuk review mingguan.",
            "source_slice": "supplier_scorecard",
            "evidence": "Tidak ada indikator low stock, arrival at-risk, COA critical, atau stale dispute yang melewati threshold advisor.",
            "next_steps": ["Review supplier scorecard.", "Pastikan data harian tetap diinput lengkap."],
        })

    if report["data_health"]["empty"]:
        refusals.append("Memo dan rekomendasi detail dibatasi karena tidak ada data sumber pada filter ini.")

    return recommendations, refusals


def _management_memo(report: dict, recommendations: list[dict], refusals: list[str]) -> str:
    scope = report["filter_scope"]
    scope_label = scope.get("period") or "all"
    if scope.get("date_from") or scope.get("date_to"):
        scope_label = f"{scope.get('date_from') or '-'} s.d. {scope.get('date_to') or '-'}"
    supplier = scope.get("supplier") or "all"
    stock = report["stock"]
    arrivals = report["arrivals"]
    disputes = report["disputes"]
    quality = report["quality"]
    top_supplier = (report.get("supplier_scorecard") or [{}])[0]
    priority_lines = "\n".join(
        f"- {item['title']}: {item['recommendation']} ({item['source_slice']})"
        for item in recommendations[:5]
    ) or "- Tidak ada rekomendasi prioritas dari advisor."
    refusal_lines = "\n".join(f"- {item}" for item in refusals) if refusals else "- Tidak ada penolakan klaim; data minimum tersedia."

    return f"""Memo Manajemen Bahan Bakar
Periode: {scope_label}
Supplier: {supplier}

Ringkasan:
- Stok saat ini {_fmt(stock.get('current_stock'), 0, ' MT')} dengan coverage {stock.get('days_of_supply') if stock.get('days_of_supply') is not None else '-'} hari dan status {stock.get('status')}.
- Realisasi kedatangan {_fmt(arrivals.get('realized_tonnage'), 0, ' MT')} dari jadwal {_fmt(arrivals.get('scheduled_tonnage'), 0, ' MT')}; jadwal at-risk {arrivals.get('at_risk_count', 0)}.
- COA: {quality.get('critical_count', 0)} critical, {quality.get('warning_count', 0)} warning, avg delta {_fmt(quality.get('avg_coa_delta'), 0, ' kcal/kg')}.
- Dispute/umpire aktif {disputes.get('umpire', {}).get('active', 0)}, stale {disputes.get('stale_count', 0)}.
- Supplier risiko tertinggi: {top_supplier.get('supplier', '-')} dengan status {top_supplier.get('risk_status', '-')}.

Rekomendasi Prioritas:
{priority_lines}

Batasan Data:
{refusal_lines}

Sumber Data:
{", ".join(slice_item["name"] for slice_item in report.get("source_slices", []))}
"""


async def build_operational_advisor(
    period: Optional[str] = "all",
    supplier: Optional[str] = "all",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: Optional[dict] = None,
) -> dict:
    """Build deterministic operational recommendations and a management memo."""
    report = await build_management_report(period, supplier, date_from, date_to, user)
    recommendations, refusals = _advisor_recommendations(report)
    memo_draft = _management_memo(report, recommendations, refusals)
    return {
        "period": report["period"],
        "supplier": report["supplier"],
        "date_from": report["date_from"],
        "date_to": report["date_to"],
        "filter_scope": report["filter_scope"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_slices": report["source_slices"],
        "source_counts": report["source_counts"],
        "data_health": report["data_health"],
        "recommendations": recommendations,
        "memo_draft": memo_draft,
        "guardrails": {
            "bounded_context": True,
            "llm_required": False,
            "unsupported_claims_refused": refusals,
            "rule_thresholds": {
                "stock_critical_days": 7,
                "stock_warning_days": 14,
                "coa_high_delta_kcal": 150,
                "stale_dispute_days": 7,
            },
        },
    }
