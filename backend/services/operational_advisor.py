import json
import os
from datetime import datetime, timezone
from typing import Optional

from app.ai.client import get_ai_client
from services.management_reports import build_management_report


URGENCY_ORDER = ["critical", "warning", "watch", "info"]
URGENCY_LABELS = {
    "critical": "Kritis",
    "warning": "Perlu tindakan",
    "watch": "Dipantau",
    "info": "Informasi",
}


def _fmt(value, digits: int = 0, suffix: str = "") -> str:
    if value is None:
        return "-"
    try:
        formatted = f"{float(value):,.{digits}f}"
        return f"{formatted}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def _recommendation(
    *,
    rec_id: str,
    severity: str,
    title: str,
    recommendation: str,
    source_slice: str,
    evidence: str,
    next_steps: list[str],
    owner_role: str,
    category: str,
    urgency: Optional[str] = None,
) -> dict:
    resolved_urgency = urgency or severity
    if resolved_urgency not in URGENCY_ORDER:
        resolved_urgency = "watch"
    return {
        "id": rec_id,
        "severity": severity,
        "urgency": resolved_urgency,
        "urgency_label": URGENCY_LABELS.get(resolved_urgency, "Dipantau"),
        "owner_role": owner_role,
        "category": category,
        "title": title,
        "recommendation": recommendation,
        "source_slice": source_slice,
        "evidence": evidence,
        "next_steps": next_steps,
    }


def _trend_context(report: dict) -> dict:
    trend = report.get("trend_analytics") or {}
    metrics = trend.get("metrics") or {}
    forecast = trend.get("stock_forecast") or {}
    supplier_trends = trend.get("supplier_trends") or []
    return {
        "confidence": trend.get("confidence", "low"),
        "sparse_data": bool(trend.get("sparse_data")),
        "caveats": trend.get("caveats", []),
        "period_comparison": trend.get("period_comparison", {}),
        "metrics": {
            key: {
                "label": value.get("label"),
                "current": value.get("current"),
                "previous": value.get("previous"),
                "delta": value.get("delta"),
                "delta_percent": value.get("delta_percent"),
                "direction": value.get("direction"),
                "direction_label": value.get("direction_label"),
                "status": value.get("status"),
                "unit": value.get("unit"),
            }
            for key, value in metrics.items()
        },
        "stock_forecast": {
            "projected_coverage_days": forecast.get("projected_coverage_days"),
            "avg_daily_usage": forecast.get("avg_daily_usage"),
            "expected_arrivals_30d": forecast.get("expected_arrivals_30d"),
            "confidence": forecast.get("confidence"),
            "caveats": forecast.get("caveats", []),
            "horizons": forecast.get("horizons", []),
        },
        "top_supplier_trends": supplier_trends[:5],
    }


def _data_quality_context(report: dict) -> dict:
    data_quality = report.get("data_quality") or {}
    return {
        "status": data_quality.get("status", "unknown"),
        "counts": data_quality.get("counts", {}),
        "caveats": data_quality.get("caveats", []),
        "issues": (data_quality.get("issues") or [])[:5],
    }


def _confidence(report: dict, trend_context: dict, data_quality_context: dict) -> dict:
    score = 100
    reasons = []
    data_health = report.get("data_health") or {}
    if data_health.get("empty"):
        score = 20
        reasons.append("Data sumber pada filter ini kosong.")
    partial_warnings = data_health.get("partial_warnings") or []
    if partial_warnings:
        score -= min(len(partial_warnings) * 10, 30)
        reasons.extend(partial_warnings[:3])
    if trend_context.get("confidence") == "medium":
        score -= 15
        reasons.append("Confidence trend sedang karena sebagian data pembanding terbatas.")
    elif trend_context.get("confidence") == "low":
        score -= 35
        reasons.append("Confidence trend rendah karena data historis atau pemakaian belum cukup.")
    if trend_context.get("sparse_data"):
        score -= 10
    dq_status = data_quality_context.get("status")
    if dq_status == "critical":
        score -= 35
        reasons.append("Ada issue critical kualitas data.")
    elif dq_status == "warning":
        score -= 15
        reasons.append("Ada warning kualitas data yang perlu direview.")
    score = max(min(score, 100), 0)
    if score >= 80:
        level = "high"
    elif score >= 50:
        level = "medium"
    else:
        level = "low"
    if not reasons:
        reasons.append("Data dan sumber pembanding cukup untuk rekomendasi deterministic.")
    return {"level": level, "score": score, "reasons": reasons}


def _limitations(report: dict, trend_context: dict, data_quality_context: dict, refusals: list[str]) -> list[str]:
    limitations = list(refusals)
    data_health = report.get("data_health") or {}
    limitations.extend(data_health.get("partial_warnings") or [])
    limitations.extend(trend_context.get("caveats") or [])
    limitations.extend(data_quality_context.get("caveats") or [])
    if data_health.get("empty"):
        limitations.append("Memo dan rekomendasi detail dibatasi karena tidak ada data sumber pada filter ini.")

    deduped = []
    seen = set()
    for item in limitations:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def _advisor_recommendations(report: dict, trend_context: dict, data_quality_context: dict) -> tuple[list[dict], list[str]]:
    recommendations = []
    refusals = []
    stock = report["stock"]
    arrivals = report["arrivals"]
    quality = report["quality"]
    disputes = report["disputes"]
    trend_metrics = trend_context.get("metrics") or {}
    stock_forecast = trend_context.get("stock_forecast") or {}

    days_of_supply = stock.get("days_of_supply")
    if days_of_supply is None:
        refusals.append("Rekomendasi reorder stock tidak diberikan karena data pemakaian pada filter ini belum cukup untuk menghitung days of supply.")
    elif days_of_supply < 7:
        recommendations.append(_recommendation(
            rec_id="stock-critical",
            severity="critical",
            urgency="critical",
            owner_role="operator",
            category="stock",
            title="Stock coverage kritis",
            recommendation="Aktifkan percepatan kedatangan terdekat dan review pemakaian harian sampai coverage kembali di atas 14 hari.",
            source_slice="stock_summary",
            evidence=f"Days of supply {days_of_supply} hari; stok {_fmt(stock.get('current_stock'), 0, ' MT')}; burn rate {_fmt(stock.get('avg_daily_usage'), 0, ' MT/hari')}.",
            next_steps=[
                "Cek jadwal PO yang at-risk.",
                "Prioritaskan supplier dengan realisasi paling cepat.",
                "Laporkan risiko coverage ke manajemen shift.",
            ],
        ))
    elif days_of_supply < 14:
        recommendations.append(_recommendation(
            rec_id="stock-warning",
            severity="warning",
            urgency="warning",
            owner_role="operator",
            category="stock",
            title="Stock mendekati threshold reorder",
            recommendation="Siapkan reorder atau percepatan pengiriman sebelum coverage turun di bawah 7 hari.",
            source_slice="stock_summary",
            evidence=f"Days of supply {days_of_supply} hari dengan threshold operasional 14 hari.",
            next_steps=["Review jadwal 7 hari ke depan.", "Pastikan rencana pemakaian unit tidak naik mendadak."],
        ))

    projected_coverage = stock_forecast.get("projected_coverage_days")
    if projected_coverage is not None and projected_coverage < 14:
        recommendations.append(_recommendation(
            rec_id="forecast-stock-risk",
            severity="warning" if projected_coverage >= 7 else "critical",
            urgency="warning" if projected_coverage >= 7 else "critical",
            owner_role="operator",
            category="trend",
            title="Forecast coverage stok perlu dikawal",
            recommendation="Gunakan forecast 7/14/30 hari untuk mengunci prioritas kedatangan dan burn assumption harian.",
            source_slice="stock_summary",
            evidence=f"Forecast coverage {projected_coverage} hari; expected arrivals 30 hari {_fmt(stock_forecast.get('expected_arrivals_30d'), 0, ' MT')}; burn {_fmt(stock_forecast.get('avg_daily_usage'), 0, ' MT/hari')}.",
            next_steps=["Review horizon 14 hari.", "Cocokkan PO mendatang dengan kebutuhan burn.", "Update forecast setelah realisasi baru masuk."],
        ))

    if arrivals.get("at_risk_count", 0) > 0 or arrivals.get("tonnage_gap", 0) > 0:
        recommendations.append(_recommendation(
            rec_id="arrival-risk",
            severity="warning" if arrivals.get("at_risk_count", 0) < 3 else "critical",
            urgency="warning" if arrivals.get("at_risk_count", 0) < 3 else "critical",
            owner_role="logistics",
            category="arrivals",
            title="Jadwal kedatangan perlu follow-up",
            recommendation="Follow-up jadwal yang sudah melewati ETA dan cocokkan ulang dengan realisasi bongkar.",
            source_slice="arrival_schedule_vs_realization",
            evidence=f"{arrivals.get('at_risk_count', 0)} jadwal at-risk; gap tonase {_fmt(arrivals.get('tonnage_gap'), 0, ' MT')}.",
            next_steps=["Hubungi PIC supplier/logistik.", "Update ETA aktual di PO Batubara.", "Cek apakah realisasi masuk di modul laporan."],
        ))
    elif arrivals.get("scheduled_count", 0) == 0:
        refusals.append("Rekomendasi keterlambatan kedatangan tidak diberikan karena tidak ada jadwal PO pada filter ini.")

    arrival_trend = trend_metrics.get("arrivals") or {}
    if arrival_trend.get("status") == "worsening":
        recommendations.append(_recommendation(
            rec_id="trend-arrival-worsening",
            severity="warning",
            urgency="watch",
            owner_role="logistics",
            category="trend",
            title="Trend fulfillment kedatangan memburuk",
            recommendation="Bandingkan PO periode berjalan dengan periode pembanding dan cari supplier/moda yang menjadi sumber penurunan.",
            source_slice="arrival_schedule_vs_realization",
            evidence=f"Fulfillment berubah {arrival_trend.get('delta')} {arrival_trend.get('unit', '')}; arah {arrival_trend.get('direction_label')}.",
            next_steps=["Review supplier trend.", "Validasi tanggal realisasi bongkar.", "Prioritaskan PO yang gap tonasenya terbesar."],
        ))

    if quality.get("critical_count", 0) > 0 or (quality.get("avg_coa_delta") or 0) >= 150:
        recommendations.append(_recommendation(
            rec_id="coa-quality-risk",
            severity="critical" if quality.get("critical_count", 0) else "warning",
            urgency="critical" if quality.get("critical_count", 0) else "warning",
            owner_role="coal_analyst",
            category="quality",
            title="Risiko kualitas COA tinggi",
            recommendation="Prioritaskan review COA critical/warning dan siapkan eskalasi umpire untuk shipment dengan delta terbesar.",
            source_slice="coa_quality_disputes",
            evidence=f"{quality.get('critical_count', 0)} critical, {quality.get('warning_count', 0)} warning, avg delta {_fmt(quality.get('avg_coa_delta'), 0, ' kcal/kg')}.",
            next_steps=["Validasi data loading/internal.", "Cek attachment dan catatan dispute.", "Ajukan umpire jika bukti lengkap."],
        ))
    elif quality.get("coa_records", 0) == 0:
        refusals.append("Rekomendasi COA tidak diberikan karena tidak ada record COA reconciliation pada filter ini.")

    quality_trend = trend_metrics.get("quality_delta") or {}
    if quality_trend.get("status") == "worsening":
        recommendations.append(_recommendation(
            rec_id="trend-quality-worsening",
            severity="warning",
            urgency="watch",
            owner_role="coal_analyst",
            category="trend",
            title="Trend delta COA memburuk",
            recommendation="Cek supplier dan shipment dengan delta COA naik sebelum dispute bertambah.",
            source_slice="coa_quality_disputes",
            evidence=f"Delta COA berubah {quality_trend.get('delta')} {quality_trend.get('unit', '')}; arah {quality_trend.get('direction_label')}.",
            next_steps=["Bandingkan loading, unloading, dan internal lab.", "Cek supplier trend kualitas.", "Siapkan bukti untuk dispute bila threshold terlewati."],
        ))

    if disputes.get("stale_count", 0) > 0:
        recommendations.append(_recommendation(
            rec_id="stale-disputes",
            severity="warning",
            urgency="warning",
            owner_role="coal_analyst",
            category="dispute",
            title="Dispute aktif mulai stale",
            recommendation="Tutup loop dispute/umpire yang berumur 7 hari atau lebih dengan PIC, target keputusan, dan tanggal follow-up.",
            source_slice="coa_quality_disputes",
            evidence=f"{disputes.get('stale_count', 0)} dispute stale; aging tertua {disputes.get('oldest_active_aging_days') or '-'} hari.",
            next_steps=["Tag owner dispute.", "Minta update lab umpire.", "Masukkan status terbaru ke dispute monitor."],
        ))

    data_quality_status = data_quality_context.get("status")
    dq_counts = data_quality_context.get("counts") or {}
    if data_quality_status in {"critical", "warning"}:
        recommendations.append(_recommendation(
            rec_id="data-quality-followup",
            severity="critical" if data_quality_status == "critical" else "warning",
            urgency="critical" if data_quality_status == "critical" else "warning",
            owner_role="admin",
            category="data_quality",
            title="Kualitas data memengaruhi interpretasi advisor",
            recommendation="Review issue kualitas data sebelum memo ini dipakai sebagai keputusan final.",
            source_slice="data_quality",
            evidence=f"{dq_counts.get('critical', 0)} critical dan {dq_counts.get('warning', 0)} warning kualitas data.",
            next_steps=["Buka Data Quality Monitor.", "Perbaiki record sumber prioritas.", "Generate ulang laporan/advisor setelah data diperbaiki."],
        ))

    top_supplier = (trend_context.get("top_supplier_trends") or [{}])[0]
    if top_supplier.get("risk_status") == "high":
        recommendations.append(_recommendation(
            rec_id="supplier-risk-trend",
            severity="warning",
            urgency="watch",
            owner_role="management",
            category="supplier",
            title="Supplier trend risiko tinggi perlu review",
            recommendation="Jadwalkan review supplier dengan risiko trend tertinggi dan bandingkan volume, kualitas, serta dispute.",
            source_slice="supplier_scorecard",
            evidence=f"{top_supplier.get('supplier')} berstatus {top_supplier.get('risk_label')} dengan score {top_supplier.get('risk_score')}.",
            next_steps=["Review supplier scorecard.", "Cek pola dispute dan realisasi.", "Tentukan tindakan komersial/operasional."],
        ))

    if not recommendations and not report["data_health"]["empty"]:
        recommendations.append(_recommendation(
            rec_id="monitor-normal",
            severity="info",
            urgency="info",
            owner_role="operator",
            category="monitoring",
            title="Tidak ada risiko prioritas tinggi pada filter ini",
            recommendation="Lanjutkan monitoring rutin dan gunakan scorecard supplier untuk review mingguan.",
            source_slice="supplier_scorecard",
            evidence="Tidak ada indikator low stock, arrival at-risk, COA critical, stale dispute, atau caveat kualitas data yang melewati threshold advisor.",
            next_steps=["Review supplier scorecard.", "Pastikan data harian tetap diinput lengkap."],
        ))

    if report["data_health"]["empty"]:
        refusals.append("Memo dan rekomendasi detail dibatasi karena tidak ada data sumber pada filter ini.")

    return recommendations, refusals


def _recommendation_groups(recommendations: list[dict]) -> list[dict]:
    groups = []
    for urgency in URGENCY_ORDER:
        items = [item for item in recommendations if item.get("urgency") == urgency]
        if not items:
            continue
        groups.append({
            "urgency": urgency,
            "label": URGENCY_LABELS[urgency],
            "count": len(items),
            "item_ids": [item["id"] for item in items],
            "items": items,
        })
    return groups


def _management_memo(report: dict, recommendations: list[dict], limitations: list[str], trend_context: dict, data_quality_context: dict) -> str:
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
    trend_metrics = trend_context.get("metrics") or {}
    stock_forecast = trend_context.get("stock_forecast") or {}
    priority_lines = "\n".join(
        f"- [{item['urgency_label']}/{item['owner_role']}] {item['title']}: {item['recommendation']} ({item['source_slice']})"
        for item in recommendations[:6]
    ) or "- Tidak ada rekomendasi prioritas dari advisor."
    limitation_lines = "\n".join(f"- {item}" for item in limitations) if limitations else "- Tidak ada batasan material; data minimum tersedia."

    return f"""Memo Manajemen Bahan Bakar
Periode: {scope_label}
Supplier: {supplier}

Ringkasan:
- Stok saat ini {_fmt(stock.get('current_stock'), 0, ' MT')} dengan coverage {stock.get('days_of_supply') if stock.get('days_of_supply') is not None else '-'} hari dan status {stock.get('status')}.
- Forecast coverage {stock_forecast.get('projected_coverage_days') if stock_forecast.get('projected_coverage_days') is not None else '-'} hari; burn assumption {_fmt(stock_forecast.get('avg_daily_usage'), 0, ' MT/hari')}; expected arrivals 30 hari {_fmt(stock_forecast.get('expected_arrivals_30d'), 0, ' MT')}.
- Realisasi kedatangan {_fmt(arrivals.get('realized_tonnage'), 0, ' MT')} dari jadwal {_fmt(arrivals.get('scheduled_tonnage'), 0, ' MT')}; trend fulfillment {trend_metrics.get('arrivals', {}).get('direction_label', '-')}.
- COA: {quality.get('critical_count', 0)} critical, {quality.get('warning_count', 0)} warning, avg delta {_fmt(quality.get('avg_coa_delta'), 0, ' kcal/kg')}; trend delta {trend_metrics.get('quality_delta', {}).get('direction_label', '-')}.
- Dispute/umpire aktif {disputes.get('umpire', {}).get('active', 0)}, stale {disputes.get('stale_count', 0)}.
- Supplier risiko tertinggi: {top_supplier.get('supplier', '-')} dengan status {top_supplier.get('risk_status', '-')}.
- Kualitas data: {data_quality_context.get('status', 'unknown')} ({data_quality_context.get('counts', {}).get('critical', 0)} critical, {data_quality_context.get('counts', {}).get('warning', 0)} warning).

Rekomendasi Prioritas:
{priority_lines}

Batasan dan Confidence:
{limitation_lines}

Sumber Data:
{", ".join(slice_item["name"] for slice_item in report.get("source_slices", []))}
"""


async def _maybe_polish_memo(deterministic_memo: str, report: dict, recommendations: list[dict], limitations: list[str]) -> tuple[str, dict]:
    llm_enabled = os.environ.get("ADVISOR_LLM_POLISH") == "1"
    polish = {
        "llm_enabled": llm_enabled,
        "llm_used": False,
        "fallback_reason": None if llm_enabled else "LLM polish nonaktif; memo deterministic digunakan.",
    }
    if not llm_enabled:
        return deterministic_memo, polish

    system_prompt = (
        "Anda memoles memo manajemen EMITS dalam Bahasa Indonesia. "
        "Jangan menambah fakta baru, angka baru, rekomendasi baru, atau klaim tanpa sumber. "
        "Gunakan hanya memo deterministic, rekomendasi, source_slices, dan limitations yang diberikan. "
        "Jika data terbatas, pertahankan batasannya."
    )
    payload = {
        "deterministic_memo": deterministic_memo,
        "recommendations": recommendations,
        "limitations": limitations,
        "source_slices": report.get("source_slices", []),
        "filter_scope": report.get("filter_scope", {}),
    }
    try:
        client = get_ai_client()
        polished = await client.send_message(
            session_id="advisor-polish",
            system_prompt=system_prompt,
            user_message=json.dumps(payload, ensure_ascii=False),
        )
        if polished and str(polished).strip():
            polish["llm_used"] = True
            polish["fallback_reason"] = None
            return str(polished).strip(), polish
        polish["fallback_reason"] = "LLM polish kosong; memo deterministic digunakan."
    except Exception:
        polish["fallback_reason"] = "LLM polish gagal; memo deterministic digunakan."
    return deterministic_memo, polish


async def build_operational_advisor(
    period: Optional[str] = "all",
    supplier: Optional[str] = "all",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: Optional[dict] = None,
) -> dict:
    """Build source-backed operational recommendations and a management memo."""
    report = await build_management_report(period, supplier, date_from, date_to, user)
    trend = _trend_context(report)
    data_quality = _data_quality_context(report)
    recommendations, refusals = _advisor_recommendations(report, trend, data_quality)
    limitations = _limitations(report, trend, data_quality, refusals)
    confidence = _confidence(report, trend, data_quality)
    memo_deterministic = _management_memo(report, recommendations, limitations, trend, data_quality)
    memo_draft, llm_guardrails = await _maybe_polish_memo(memo_deterministic, report, recommendations, limitations)
    groups = _recommendation_groups(recommendations)
    return {
        "period": report["period"],
        "supplier": report["supplier"],
        "date_from": report["date_from"],
        "date_to": report["date_to"],
        "filter_scope": report["filter_scope"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_slices": report["source_slices"],
        "source_counts": report["source_counts"],
        "source_context": {
            "source_slices": report["source_slices"],
            "source_counts": report["source_counts"],
            "filter_scope": report["filter_scope"],
        },
        "data_health": report["data_health"],
        "data_quality_context": data_quality,
        "trend_context": trend,
        "confidence": confidence,
        "limitations": limitations,
        "recommendations": recommendations,
        "recommendation_groups": groups,
        "memo_draft": memo_draft,
        "memo_deterministic": memo_deterministic,
        "guardrails": {
            "bounded_context": True,
            "llm_required": False,
            **llm_guardrails,
            "unsupported_claims_refused": limitations,
            "rule_thresholds": {
                "stock_critical_days": 7,
                "stock_warning_days": 14,
                "forecast_warning_days": 14,
                "coa_high_delta_kcal": 150,
                "stale_dispute_days": 7,
            },
        },
    }

