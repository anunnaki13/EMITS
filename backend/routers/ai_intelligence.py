from datetime import datetime, timezone
import json
import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.ai.client import AIClient, get_ai_client
from services.coa_reconciliation import calculate_kpis
from services.operational_advisor import build_operational_advisor
from services.query_filters import period_match, sum_collection
from utils.auth import get_current_user
from utils.database import db

router = APIRouter(tags=["AI Intelligence"])
logger = logging.getLogger(__name__)

# ==================== AI INTELLIGENCE AGENT ====================
# Uses OpenRouterClient via get_ai_client().

# AI Chat History Collection
ai_chat_collection = db.ai_chat_history
AI_CONTEXT_RECORD_LIMIT = 12
AI_CONTEXT_MAX_CHARS = 14000

class AIQueryRequest(BaseModel):
    query: str
    module: str = "general"  # general, blending, boiler_risk, contract, logistics
    session_id: Optional[str] = None
    parameters: Optional[dict] = None

class AISettingsUpdate(BaseModel):
    custom_api_key: Optional[str] = None
    llm_provider: Optional[str] = "openrouter"
    llm_model: Optional[str] = "openai/gpt-4o-mini"

def _clean_records(records: list[dict]) -> list[dict]:
    blocked = {"_id", "password", "hashed_password", "custom_api_key", "api_key", "token", "access_token"}
    return [
        {key: value for key, value in record.items() if key not in blocked}
        for record in records[:AI_CONTEXT_RECORD_LIMIT]
    ]


def _add_slice(slices: list[dict], name: str, collections: list[str], record_count: int, fields: list[str]) -> None:
    slices.append({
        "name": name,
        "collections": collections,
        "record_count": record_count,
        "fields": fields,
    })


async def build_contextual_ai_context(module: str, parameters: Optional[dict] = None) -> dict:
    """Build bounded, whitelist-only operational context for AI prompts."""
    parameters = parameters or {}
    period = parameters.get("period") or "all"
    context: dict = {"period": period, "generated_at": datetime.now(timezone.utc).isoformat()}
    slices: list[dict] = []

    include_all = module in {"general", "smart_stock", "coa_reconciliation", "logistics", "contract"}

    if include_all or module == "smart_stock":
        stock_match = period_match("date", period)
        latest_stock = await db.smartstock.find_one({}, {"_id": 0}, sort=[("date", -1)])
        latest_usage = await db.sumberpemakaian.find_one({}, {"_id": 0}, sort=[("date", -1)])
        total_penerimaan = await sum_collection(db.smartstock, stock_match, "total_penerimaan")
        total_pemakaian = await sum_collection(db.sumberpemakaian, stock_match, "total_pemakaian")
        current_stock = latest_stock.get("stock_akhir") if latest_stock and latest_stock.get("stock_akhir") is not None else None
        if current_stock is None:
            current_stock = (
                (latest_stock.get("stock_awal", 0) if latest_stock else 0)
                + (latest_stock.get("total_penerimaan", 0) if latest_stock else 0)
                - (latest_usage.get("total_pemakaian", 0) if latest_usage else 0)
            )
        avg_daily_usage = total_pemakaian / 30 if total_pemakaian else 0
        context["stock"] = {
            "current_stock": current_stock or 0,
            "latest_stock_date": latest_stock.get("date") if latest_stock else None,
            "latest_usage_date": latest_usage.get("date") if latest_usage else None,
            "total_penerimaan": total_penerimaan,
            "total_pemakaian": total_pemakaian,
            "avg_daily_usage": avg_daily_usage,
            "days_of_supply": int((current_stock or 0) / avg_daily_usage) if avg_daily_usage else None,
        }
        count = await db.smartstock.count_documents(stock_match) + await db.sumberpemakaian.count_documents(stock_match)
        _add_slice(slices, "stock_summary", ["smartstock", "sumberpemakaian"], count, list(context["stock"].keys()))

    if include_all or module in {"contract", "logistics"}:
        po_match = period_match("time_arrival", period)
        scheduled_count = await db.po_batubara.count_documents(po_match)
        scheduled_tonnage = await sum_collection(db.po_batubara, po_match, "tonase_po")
        realized_sources = [
            ("vessel", db.vessels, "completed_unloading", "ds_mt"),
            ("barge", db.barges, "completed_unloading", "ds_mt"),
            ("trucking", db.trucking, "completed_unloading", "ds_mt"),
            ("biomassa", db.biomassa, "completed_unloading", "jembatan_timbang_mt"),
        ]
        realized_by_mode = []
        realized_count = 0
        realized_tonnage = 0.0
        for mode, collection, date_field, tonnage_field in realized_sources:
            match = period_match(date_field, period)
            count = await collection.count_documents(match)
            tonnage = await sum_collection(collection, match, tonnage_field)
            realized_count += count
            realized_tonnage += tonnage
            realized_by_mode.append({"mode": mode, "count": count, "tonnage": tonnage})
        context["arrivals"] = {
            "scheduled_count": scheduled_count,
            "scheduled_tonnage": scheduled_tonnage,
            "realized_count": realized_count,
            "realized_tonnage": realized_tonnage,
            "tonnage_fulfillment_rate": (realized_tonnage / scheduled_tonnage * 100) if scheduled_tonnage else None,
            "realized_by_mode": realized_by_mode,
        }
        _add_slice(slices, "arrival_schedule_vs_realization", ["po_batubara", "vessels", "barges", "trucking", "biomassa"], scheduled_count + realized_count, list(context["arrivals"].keys()))

    if include_all or module in {"coa_reconciliation", "boiler_risk"}:
        coa_match = period_match("completed_unloading", period)
        coa_items = await db.coa_reconciliation.find(
            coa_match,
            {"_id": 0, "shipment": 1, "suppliers": 1, "status": 1, "umpire_status": 1, "delta_loading_internal": 1, "ds_mt": 1, "completed_unloading": 1, "dispute_history": 1, "loading_gcv_arb": 1, "unloading_gcv_arb": 1, "internal_gcv_arb": 1, "umpire_gcv_arb": 1},
        ).sort("completed_unloading", -1).limit(AI_CONTEXT_RECORD_LIMIT).to_list(AI_CONTEXT_RECORD_LIMIT)
        all_coa = await db.coa_reconciliation.find(
            coa_match,
            {"_id": 0, "shipment": 1, "status": 1, "umpire_status": 1, "delta_loading_internal": 1, "ds_mt": 1, "suppliers": 1, "completed_unloading": 1, "loading_gcv_arb": 1, "unloading_gcv_arb": 1, "internal_gcv_arb": 1, "umpire_gcv_arb": 1},
        ).to_list(5000)
        po_records = await db.po_batubara.find({}, {"_id": 0}).to_list(50000)
        coa_kpis = calculate_kpis(all_coa, po_records=po_records)
        supplier_delta = {}
        for item in all_coa:
            supplier = item.get("suppliers") or "Unknown"
            supplier_delta.setdefault(supplier, []).append(abs(float(item.get("delta_loading_internal") or 0)))
        top_supplier_patterns = sorted(
            [
                {"supplier": supplier, "avg_delta": sum(values) / len(values), "record_count": len(values)}
                for supplier, values in supplier_delta.items() if values
            ],
            key=lambda row: row["avg_delta"],
            reverse=True,
        )[:5]
        context["disputes"] = {
            "total_records": len(all_coa),
            "critical_count": sum(1 for item in all_coa if str(item.get("status", "")).lower() in {"critical", "kritis"}),
            "warning_count": sum(1 for item in all_coa if str(item.get("status", "")).lower() == "warning"),
            "active_umpire_count": sum(1 for item in all_coa if item.get("umpire_status") in {"proposed", "in_progress"}),
            "potential_loss_mt": sum(abs(float(item.get("delta_loading_internal") or 0)) for item in all_coa),
            "potential_loss_rp": coa_kpis["potential_loss_rp"],
            "potential_loss_price_basis": coa_kpis["potential_loss_price_basis"],
            "potential_loss_price_source_counts": coa_kpis["potential_loss_price_source_counts"],
            "umpire_savings_rp": coa_kpis["umpire_savings_rp"],
            "top_supplier_patterns": top_supplier_patterns,
            "recent_records": _clean_records(coa_items),
        }
        _add_slice(slices, "coa_dispute_summary", ["coa_reconciliation"], len(all_coa), ["status", "umpire_status", "delta_loading_internal", "ds_mt", "completed_unloading"])

    if module in {"general", "blending", "boiler_risk"}:
        quality_records = []
        for collection, source in [(db.vessels, "vessel"), (db.barges, "barge"), (db.trucking, "trucking")]:
            records = await collection.find(
                {"gcv_arb": {"$ne": None}},
                {"_id": 0, "suppliers": 1, "gcv_arb": 1, "tm_arb": 1, "ash_arb": 1, "slagging_index": 1, "fouling_index": 1, "completed_unloading": 1},
            ).sort("completed_unloading", -1).limit(4).to_list(4)
            for record in records:
                record["source"] = source
                quality_records.append(record)
        context["recent_quality"] = _clean_records(quality_records)
        _add_slice(slices, "recent_quality", ["vessels", "barges", "trucking"], len(quality_records), ["suppliers", "gcv_arb", "tm_arb", "ash_arb", "slagging_index", "fouling_index"])

    context_text = json.dumps(context, ensure_ascii=False, default=str)
    if len(context_text) > AI_CONTEXT_MAX_CHARS:
        context_text = context_text[:AI_CONTEXT_MAX_CHARS] + "\n...[context truncated by safety limit]"
    return {
        "context": context,
        "context_text": context_text,
        "context_slices": slices,
        "context_limit": {
            "max_records_per_slice": AI_CONTEXT_RECORD_LIMIT,
            "max_prompt_chars": AI_CONTEXT_MAX_CHARS,
        },
    }

async def get_database_context(module: str, parameters: dict = None) -> str:
    """Gather relevant data from database based on module"""
    context_parts = []
    
    if module in ["general", "blending", "contract"]:
        # Get PO Batubara summary
        po_data = await db.po_batubara.aggregate([
            {"$group": {
                "_id": "$spec",
                "total_tonase": {"$sum": "$tonase_po"},
                "count": {"$sum": 1}
            }}
        ]).to_list(100)
        context_parts.append(f"PO Batubara Summary: {po_data}")
        
        # Get Merit Order data (top suppliers by efficiency)
        merit_data = await db.merit_order.find(
            {"rp_kcal": {"$ne": None}},
            {"_id": 0, "pemasok": 1, "moda": 1, "tipikal_kcal_kg": 1, "harga_cif": 1, "rp_kcal": 1}
        ).sort("rp_kcal", 1).limit(10).to_list(10)
        context_parts.append(f"Top 10 Efficient Suppliers (Merit Order): {merit_data}")
    
    if module in ["general", "blending", "boiler_risk"]:
        # Get recent vessel quality data
        vessel_quality = await db.vessels.find(
            {"gcv_arb": {"$ne": None}},
            {"_id": 0, "name_of_vessel": 1, "suppliers": 1, "gcv_arb": 1, "tm_arb": 1, 
             "ash_arb": 1, "slagging_index": 1, "fouling_index": 1, "completed_unloading": 1}
        ).sort("completed_unloading", -1).limit(20).to_list(20)
        context_parts.append(f"Recent Vessel Quality Data: {vessel_quality}")
        
        # Get barge quality data
        barge_quality = await db.barges.find(
            {"gcv_arb": {"$ne": None}},
            {"_id": 0, "suppliers": 1, "gcv_arb": 1, "tm_arb": 1, "ash_arb": 1,
             "slagging_index": 1, "fouling_index": 1, "completed_unloading": 1}
        ).sort("completed_unloading", -1).limit(20).to_list(20)
        context_parts.append(f"Recent Barge Quality Data: {barge_quality}")
    
    if module in ["general", "logistics"]:
        # Get logistics data (B/L vs DS differences)
        vessel_logistics = await db.vessels.find(
            {"bl_mt": {"$ne": None}, "ds_mt": {"$ne": None}},
            {"_id": 0, "name_of_vessel": 1, "suppliers": 1, "bl_mt": 1, "ds_mt": 1, 
             "commenced_unloading": 1, "completed_unloading": 1}
        ).sort("completed_unloading", -1).limit(30).to_list(30)
        context_parts.append(f"Vessel Logistics Data (B/L vs DS): {vessel_logistics}")
        
        barge_logistics = await db.barges.find(
            {"bl_mt": {"$ne": None}, "ds_mt": {"$ne": None}},
            {"_id": 0, "suppliers": 1, "bl_mt": 1, "ds_mt": 1,
             "commenced_unloading": 1, "completed_unloading": 1}
        ).sort("completed_unloading", -1).limit(30).to_list(30)
        context_parts.append(f"Barge Logistics Data: {barge_logistics}")
    
    if module in ["general", "contract"]:
        # Get contract compliance data
        po_summary = await db.po_batubara.aggregate([
            {"$group": {
                "_id": "$supplier_name",
                "total_po_tonase": {"$sum": "$tonase_po"},
                "po_count": {"$sum": 1}
            }},
            {"$sort": {"total_po_tonase": -1}},
            {"$limit": 15}
        ]).to_list(15)
        context_parts.append(f"PO by Supplier: {po_summary}")
        
        # Get actual receipts
        vessel_receipts = await db.vessels.aggregate([
            {"$group": {
                "_id": "$suppliers",
                "total_received": {"$sum": "$ds_mt"},
                "shipment_count": {"$sum": 1}
            }},
            {"$sort": {"total_received": -1}},
            {"$limit": 15}
        ]).to_list(15)
        context_parts.append(f"Vessel Receipts by Supplier: {vessel_receipts}")
    
    if module == "blending" and parameters:
        target_gcv = parameters.get("target_gcv", 4000)
        context_parts.append(f"User Target GCV: {target_gcv} Kcal/kg")
        
        # Get available stock for blending
        available_stock = await db.vessels.find(
            {"gcv_arb": {"$ne": None}, "ds_mt": {"$gt": 0}},
            {"_id": 0, "name_of_vessel": 1, "suppliers": 1, "gcv_arb": 1, "ds_mt": 1, "ash_arb": 1}
        ).sort("completed_unloading", -1).limit(15).to_list(15)
        context_parts.append(f"Available Vessel Stock for Blending: {available_stock}")
        
        biomass_stock = await db.biomassa.find(
            {"jembatan_timbang_mt": {"$gt": 0}},
            {"_id": 0, "biomass_type": 1, "jembatan_timbang_mt": 1, "gcv_arb": 1}
        ).sort("completed_unloading", -1).limit(10).to_list(10)
        context_parts.append(f"Available Biomass Stock: {biomass_stock}")
    
    # Smart Stock Module Data
    if module in ["general", "smart_stock"]:
        # Get smart stock penerimaan data
        penerimaan_data = await db.smartstock.find(
            {},
            {"_id": 0, "date": 1, "total_penerimaan": 1, "suppliers": 1}
        ).sort("date", -1).limit(30).to_list(30)
        if penerimaan_data:
            context_parts.append(f"Smart Stock - Sumber Penerimaan (30 terbaru): {penerimaan_data}")
        
        # Get smart stock pemakaian data
        pemakaian_data = await db.sumberpemakaian.find(
            {},
            {"_id": 0, "date": 1, "total_pemakaian": 1, "suppliers": 1}
        ).sort("date", -1).limit(30).to_list(30)
        if pemakaian_data:
            context_parts.append(f"Smart Stock - Sumber Pemakaian (30 terbaru): {pemakaian_data}")
        
        # Calculate stock summary
        total_penerimaan = await db.smartstock.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$total_penerimaan"}}}
        ]).to_list(1)
        total_pemakaian = await db.sumberpemakaian.aggregate([
            {"$group": {"_id": None, "total_pemakaian": {"$sum": "$total_pemakaian"}}}
        ]).to_list(1)
        
        if total_penerimaan and total_pemakaian:
            penerimaan = total_penerimaan[0].get("total", 0) if total_penerimaan else 0
            pemakaian = total_pemakaian[0].get("total_pemakaian", 0) if total_pemakaian else 0
            context_parts.append(f"Ringkasan Stok: Total Penerimaan={penerimaan} MT, Total Pemakaian={pemakaian} MT")
    
    # COA Reconciliation Module Data
    if module in ["general", "coa_reconciliation"]:
        # Get COA reconciliation data
        coa_data = await db.coa_reconciliation.find(
            {},
            {"_id": 0, "shipment": 1, "supplier": 1, "loading_gcv_arb": 1, "unloading_gcv_arb": 1, 
             "internal_gcv_arb": 1, "delta_loading_internal": 1, "status": 1, "umpire_status": 1,
             "completed_unloading": 1}
        ).sort("completed_unloading", -1).limit(30).to_list(30)
        if coa_data:
            context_parts.append(f"COA Reconciliation Data (30 terbaru): {coa_data}")
        
        # Get KPIs summary
        all_coa = await db.coa_reconciliation.find({}, {"_id": 0}).to_list(10000)
        if all_coa:
            kritis_count = sum(1 for c in all_coa if str(c.get("status", "")).lower() in {"critical", "kritis"})
            umpire_count = sum(1 for c in all_coa if c.get("umpire_status") not in [None, "none", ""])
            po_records = await db.po_batubara.find({}, {"_id": 0}).to_list(50000)
            coa_kpis = calculate_kpis(all_coa, po_records=po_records)

            context_parts.append(
                f"COA KPIs: Total Records={len(all_coa)}, Status Kritis={kritis_count}, "
                f"Dalam Proses Umpire={umpire_count}, Potential Loss Berbasis PO=Rp {coa_kpis['potential_loss_rp']:,.0f}, "
                f"Estimasi Diselamatkan Umpire=Rp {coa_kpis['umpire_savings_rp']:,.0f}"
            )
            
            # Supplier dengan deviasi tertinggi
            supplier_deviasi = {}
            for c in all_coa:
                supplier = c.get("suppliers") or c.get("supplier") or "Unknown"
                delta = abs(c.get("delta_loading_internal", 0) or 0)
                if supplier not in supplier_deviasi:
                    supplier_deviasi[supplier] = []
                supplier_deviasi[supplier].append(delta)
            
            top_deviasi = sorted(
                [(s, sum(d)/len(d)) for s, d in supplier_deviasi.items() if d],
                key=lambda x: x[1], reverse=True
            )[:5]
            context_parts.append(f"Top 5 Supplier dengan Deviasi GCV Tertinggi: {top_deviasi}")
    
    return "\n\n".join(context_parts)

def get_system_prompt(module: str) -> str:
    """Get system prompt based on module"""
    base_prompt = """Anda adalah Tenayan Fuel Intelligence Agent - Asisten ahli Rendal Bahan Bakar PLTU Tenayan.
Tugas Anda adalah mengolah data dari database (Vessel, Barge, Trucking, Biomassa, PO, Merit Order, dan COA Reconciliation) 
untuk memberikan wawasan berbasis Data Science, Machine Learning, dan AI.

PENTING:
- Jawab dalam Bahasa Indonesia
- Berikan analisis yang akurat berdasarkan data
- Sertakan perhitungan numerik jika diperlukan
- Format output dalam tabel atau bullet points untuk kemudahan membaca
- Berikan rekomendasi actionable

FITUR APLIKASI YANG TERSEDIA:

1. **Dashboard**: Ringkasan KPI penerimaan bahan bakar, chart tren, dan statistik.

2. **Data Penerimaan**: Halaman untuk melihat, menambah, dan mengelola data penerimaan dari Vessel, Barge, Trucking, dan Biomassa.

3. **Merit Order**: Tabel ranking supplier berdasarkan harga per kCal (Rp/kCal) dari yang termurah.

4. **Smart Stock**: Monitoring stok batubara di stockpile dengan visualisasi.

5. **Laporan**: Generate laporan dalam format PDF dan Excel.

6. **COA Reconciliation (Triple Check)**: 
   - Fitur untuk membandingkan data kualitas batubara dari 3 sumber: Loading COA (dari supplier), Unloading COA (di pelabuhan), dan Lab Internal (hasil uji lab PLTU).
   - Menampilkan parameter kunci: GCV, TM (Total Moisture), Ash, dan Sulphur dari ketiga sumber secara berdampingan.
   - Menghitung Delta GCV = Loading GCV - Internal GCV untuk mengidentifikasi perbedaan klaim supplier vs hasil lab internal.
   - Status "Kritis" ditandai jika Delta GCV > 150 kCal/kg DAN Loading GCV > Internal GCV (supplier overclaim).
   - KPI Dashboard: High Deviation Alert, Potential Loss (Rp), dan Umpire Status.
   - Radar Chart untuk visualisasi perbandingan profil kualitas antar sumber.

7. **Dispute Monitor (Umpire Process)**:
   - Halaman untuk mengelola proses umpire/arbitrase ketika terjadi dispute kualitas batubara.
   - Workflow: Propose Umpire → Sedang Proses → Selesai (dengan input hasil lab umpire).
   - Mendukung "Quad Check" - membandingkan 4 sumber data termasuk hasil lab umpire.
   - Input hasil umpire: GCV, TM, Ash, Sulphur, Nama Lab, dan Tanggal Hasil.

8. **Settings**: Konfigurasi parameter aplikasi. Potential Loss COA utama dihitung dari harga PO Batubara, bukan angka COA manual.

9. **AI Intelligence**: Fitur AI Assistant (Anda) untuk analisis data dan rekomendasi.
"""
    
    module_prompts = {
        "blending": base_prompt + """
MODUL: Smart Blending Optimizer
Fokus: Optimasi campuran batubara & biomassa secara ekonomis.

Tugas spesifik:
1. Identifikasi kargo tersedia berdasarkan 'Completed Unloading' terbaru
2. Lakukan perhitungan optimasi untuk mencari porsi (%) campuran LRC, MRC, dan Biomassa
3. Batasan: Total campuran harus mencapai Target GCV, dengan Ash Content < 10%
4. Utamakan stok dengan Rp/Kcal terendah dari Merit Order
5. Tampilkan hasil: [Nama Supplier] | [Porsi %] | [Tonase Rekomendasi] | [Harga Estimasi]

Rumus GCV Campuran: GCV_mix = Σ(GCV_i × Porsi_i)
""",
        "boiler_risk": base_prompt + """
MODUL: Boiler Risk Warning
Fokus: Deteksi potensi kerusakan boiler dari data laboratorium.

Tugas spesifik:
1. Analisis data kualitas kimia: SiO2, Al2O3, Fe2O3, CaO, Na2O, K2O
2. Hitung indeks Slagging dan Fouling menggunakan rumus standar industri
3. Kriteria risiko:
   - Slagging Index > 0.6 atau Fouling Index > 0.4 = 'HIGH RISK'
   - Na2O > 2% = Peringatan khusus potensi kerak pipa
4. Tampilkan 'Alert Board' daftar kargo berisiko tinggi di stockpile
5. Berikan rekomendasi strategi sootblowing

Rumus Slagging Index: Rs = (Base/Acid) × (S content)
Rumus Fouling Index: Rf = (Base/Acid) × Na2O
""",
        "contract": base_prompt + """
MODUL: Contract Compliance & PO Tracker
Fokus: Digitalisasi monitoring kontrak tanpa rekap manual.

Tugas spesifik:
1. Lakukan vlookup otomatis antara PO BB dengan penerimaan (barge, vessel, trucking)
2. Hitung: Sisa Kuota = Tonase PO - Total DS MT yang diterima
3. Bandingkan GCV Kontrak (di PO) dengan GCV Realisasi (di Penerimaan)
4. Output Dashboard:
   - List PO yang hampir habis (< 10% sisa)
   - List Supplier dengan GCV di bawah spek kontrak (Defisit Kalori)
5. Berikan early warning untuk kontrak yang perlu diperpanjang
""",
        "logistics": base_prompt + """
MODUL: Logistic Efficiency & Loss Analysis
Fokus: Data Science pada efisiensi pengiriman.

Tugas spesifik:
1. Hitung selisih antara B/L (MT) dan DS (MT) - Draft Survey
2. Hitung rata-rata % Losses per supplier: ((B/L - DS) / B/L) × 100%
3. Hitung 'Durasi Pembongkaran' rata-rata per moda transportasi
4. Output:
   - 3 Supplier dengan tingkat penyusutan (losses) tertinggi
   - Tren durasi bongkar per bulan untuk deteksi inefisiensi di Jetty
   - Anomali pengiriman yang perlu investigasi
""",
        "general": base_prompt + """
MODUL: General Intelligence
Fokus: Menjawab pertanyaan umum tentang data bahan bakar PLTU Tenayan.

Anda dapat:
1. Memberikan ringkasan statistik dari semua data
2. Menjawab pertanyaan spesifik tentang supplier, kualitas, atau pengiriman
3. Memberikan rekomendasi berdasarkan analisis data
4. Menjelaskan tren dan pola dalam data historis
""",
        "smart_stock": base_prompt + """
MODUL: Smart Stock Management
Fokus: Analisis stok batubara dan biomassa di stockpile.

Tugas spesifik:
1. Monitoring stok aktual batubara di stockpile dari berbagai sumber (Vessel, Barge, Trucking, Biomassa)
2. Analisis pemakaian harian dan tren konsumsi bahan bakar
3. Perhitungan estimasi hari stok tersedia (Days of Supply)
4. Identifikasi anomali penerimaan vs pemakaian
5. Rekomendasi waktu optimal untuk pemesanan ulang

Data yang tersedia:
- Sumber Penerimaan: Data penerimaan batubara dari Vessel, Barge, Trucking, dan Biomassa
- Sumber Pemakaian: Data pemakaian harian batubara termasuk energi (MWh) dan tonase
- Merit Order: Ranking supplier berdasarkan harga per kCal

Output yang diharapkan:
- Total Stok Saat Ini (MT)
- Rata-rata Pemakaian Harian (MT/hari)
- Estimasi Hari Stok Tersisa
- Rekomendasi pengisian stok
""",
        "coa_reconciliation": base_prompt + """
MODUL: COA Reconciliation & Quality Dispute
Fokus: Rekonsiliasi kualitas batubara dari tiga sumber dan manajemen dispute.

Tugas spesifik:
1. Analisis Triple Check: Bandingkan Loading COA (supplier), Unloading COA (surveyor), dan Lab Internal (PLTU)
2. Identifikasi lot dengan deviasi GCV tinggi (Delta > 150 kCal/kg)
3. Deteksi potensi overclaim dari supplier (Loading GCV > Internal GCV)
4. Hitung Potential Loss (Rp) dari defisit kalori memakai harga PO Batubara
5. Monitoring status umpire/arbitrase yang sedang berjalan
6. Analisis konsistensi supplier berdasarkan historis deviasi

Parameter Kunci yang dianalisis:
- GCV ARB (Gross Calorific Value As Received Basis)
- TM ARB (Total Moisture)
- Ash ARB (Kadar Abu)
- Sulphur ARB (Kadar Belerang)

Status Kritis: Ditandai jika Delta_GCV > 150 kCal/kg DAN Loading GCV > Internal GCV (overclaim)

Rumus Perhitungan:
- Delta GCV = Loading_GCV - Internal_GCV
- Potential Loss = Tonase × Delta_GCV × (Harga_PO_per_MT / Loading_GCV)

Output yang diharapkan:
- High Deviation Alert: Jumlah lot dengan status Kritis
- Potential Loss (Rp): Estimasi kerugian finansial berbasis PO Batubara
- Supplier dengan deviasi tertinggi
- Rekomendasi pengajuan umpire
"""
    }
    
    return module_prompts.get(module, module_prompts["general"])

@router.post("/ai/query")
async def ai_query(request: AIQueryRequest, user: dict = Depends(get_current_user), ai: AIClient = Depends(get_ai_client)):
    """Process AI query with database context"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"tenayan-ai-{user['id']}-{uuid.uuid4()}"

        # Get bounded structured database context
        context_bundle = await build_contextual_ai_context(request.module, request.parameters)

        # Get system prompt
        system_prompt = get_system_prompt(request.module)

        # Prepare message with context
        full_query = f"""DATA CONTEXT (structured, bounded, whitelist-only):
{context_bundle["context_text"]}

DATA SLICES USED:
{json.dumps(context_bundle["context_slices"], ensure_ascii=False)}

USER QUERY:
{request.query}

Berikan analisis dan jawaban berdasarkan data di atas. Akhiri jawaban dengan bagian "Sumber Data" yang menyebutkan nama slice data yang dipakai."""

        # Get AI response via injected client
        response = await ai.send_message(session_id, system_prompt, full_query)
        
        # Save to chat history
        chat_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "session_id": session_id,
            "module": request.module,
            "query": request.query,
            "response": response,
            "parameters": request.parameters,
            "context_slices": context_bundle["context_slices"],
            "context_limit": context_bundle["context_limit"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await ai_chat_collection.insert_one(chat_entry)
        
        return {
            "response": response,
            "session_id": session_id,
            "module": request.module,
            "context_slices": context_bundle["context_slices"],
            "context_limit": context_bundle["context_limit"],
        }
        
    except Exception as e:
        logger.error(f"AI Query Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Query failed: {str(e)}")

@router.get("/ai/history")
async def get_ai_chat_history(
    session_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """Get AI chat history for user"""
    query = {"user_id": user["id"]}
    if session_id:
        query["session_id"] = session_id
    
    history = await ai_chat_collection.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return history

@router.delete("/ai/history")
async def clear_ai_chat_history(user: dict = Depends(get_current_user)):
    """Clear AI chat history for user"""
    result = await ai_chat_collection.delete_many({"user_id": user["id"]})
    return {"message": f"Berhasil menghapus {result.deleted_count} riwayat chat"}

@router.get("/ai/settings")
async def get_ai_settings(user: dict = Depends(get_current_user)):
    """Get user's AI settings"""
    settings = await db.user_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        return {
            "custom_api_key": None,
            "llm_provider": "openrouter",
            "llm_model": "openai/gpt-4o-mini",
            "using_default": True
        }
    return {
        **settings,
        "using_default": not bool(settings.get("custom_api_key"))
    }

@router.put("/ai/settings")
async def update_ai_settings(settings: AISettingsUpdate, user: dict = Depends(get_current_user)):
    """Update user's AI settings"""
    update_data = {
        "user_id": user["id"],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if settings.custom_api_key is not None:
        update_data["custom_api_key"] = settings.custom_api_key if settings.custom_api_key else None
    if settings.llm_provider:
        update_data["llm_provider"] = settings.llm_provider
    if settings.llm_model:
        update_data["llm_model"] = settings.llm_model
    
    await db.user_settings.update_one(
        {"user_id": user["id"]},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Pengaturan AI berhasil disimpan"}

# Quick Analysis Endpoints for Dashboard Modules
@router.get("/ai/quick/blending-suggestion")
async def get_blending_suggestion(target_gcv: int = 4000, user: dict = Depends(get_current_user)):
    """Get quick blending suggestion without full AI query"""
    # Get available coal stock
    vessels = await db.vessels.find(
        {"gcv_arb": {"$ne": None}, "ds_mt": {"$gt": 0}},
        {"_id": 0, "name_of_vessel": 1, "suppliers": 1, "gcv_arb": 1, "ds_mt": 1, "ash_arb": 1}
    ).sort("completed_unloading", -1).limit(10).to_list(10)
    
    biomass = await db.biomassa.find(
        {"jembatan_timbang_mt": {"$gt": 0}},
        {"_id": 0, "biomass_type": 1, "jembatan_timbang_mt": 1}
    ).limit(5).to_list(5)
    
    return {
        "target_gcv": target_gcv,
        "available_coal": vessels,
        "available_biomass": biomass,
        "recommendation": "Gunakan modul AI untuk analisis blending yang lebih detail"
    }

@router.get("/ai/quick/boiler-alerts")
async def get_boiler_alerts(user: dict = Depends(get_current_user)):
    """Get quick boiler risk alerts"""
    # Get high risk items
    high_risk_vessels = await db.vessels.find(
        {"$or": [
            {"slagging_index": {"$regex": "HIGH|SEVERE", "$options": "i"}},
            {"fouling_index": {"$regex": "HIGH|SEVERE", "$options": "i"}}
        ]},
        {"_id": 0, "name_of_vessel": 1, "suppliers": 1, "slagging_index": 1, "fouling_index": 1}
    ).sort("completed_unloading", -1).limit(10).to_list(10)
    
    high_risk_barges = await db.barges.find(
        {"$or": [
            {"slagging_index": {"$regex": "HIGH|SEVERE", "$options": "i"}},
            {"fouling_index": {"$regex": "HIGH|SEVERE", "$options": "i"}}
        ]},
        {"_id": 0, "suppliers": 1, "slagging_index": 1, "fouling_index": 1}
    ).sort("completed_unloading", -1).limit(10).to_list(10)
    
    return {
        "high_risk_vessels": high_risk_vessels,
        "high_risk_barges": high_risk_barges,
        "total_alerts": len(high_risk_vessels) + len(high_risk_barges)
    }

@router.get("/ai/quick/contract-status")
async def get_contract_status(user: dict = Depends(get_current_user)):
    """Get quick contract compliance status"""
    # Get PO summary
    po_summary = await db.po_batubara.aggregate([
        {"$group": {
            "_id": "$supplier_name",
            "total_po": {"$sum": "$tonase_po"},
            "po_count": {"$sum": 1}
        }},
        {"$sort": {"total_po": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Get receipts
    receipts = await db.vessels.aggregate([
        {"$group": {
            "_id": "$suppliers",
            "total_received": {"$sum": "$ds_mt"}
        }}
    ]).to_list(100)
    
    receipts_map = {r["_id"]: r["total_received"] for r in receipts if r["_id"]}
    
    contract_status = []
    for po in po_summary:
        supplier = po["_id"]
        received = receipts_map.get(supplier, 0)
        remaining = po["total_po"] - received
        percentage = (received / po["total_po"] * 100) if po["total_po"] > 0 else 0
        
        contract_status.append({
            "supplier": supplier,
            "total_po": po["total_po"],
            "received": received,
            "remaining": remaining,
            "percentage": percentage,
            "status": "CRITICAL" if percentage > 90 else "WARNING" if percentage > 70 else "OK"
        })
    
    return {"contracts": contract_status}

@router.get("/ai/quick/logistics-losses")
async def get_logistics_losses(user: dict = Depends(get_current_user)):
    """Get quick logistics losses analysis"""
    # Calculate losses from vessels
    vessels = await db.vessels.find(
        {"bl_mt": {"$ne": None}, "ds_mt": {"$ne": None}},
        {"_id": 0, "suppliers": 1, "bl_mt": 1, "ds_mt": 1}
    ).to_list(1000)
    
    supplier_losses = {}
    for v in vessels:
        supplier = v.get("suppliers", "Unknown")
        bl = v.get("bl_mt", 0) or 0
        ds = v.get("ds_mt", 0) or 0
        if bl > 0:
            loss_pct = ((bl - ds) / bl) * 100
            if supplier not in supplier_losses:
                supplier_losses[supplier] = []
            supplier_losses[supplier].append(loss_pct)
    
    # Calculate averages
    losses_summary = []
    for supplier, losses in supplier_losses.items():
        avg_loss = sum(losses) / len(losses)
        losses_summary.append({
            "supplier": supplier,
            "avg_loss_pct": avg_loss,
            "shipment_count": len(losses)
        })
    
    # Sort by highest loss
    losses_summary.sort(key=lambda x: x["avg_loss_pct"], reverse=True)
    
    return {
        "top_losses": losses_summary[:5],
        "lowest_losses": losses_summary[-5:] if len(losses_summary) > 5 else []
    }

@router.get("/ai/quick/smart-stock")
async def get_smart_stock_summary(user: dict = Depends(get_current_user)):
    """Get quick smart stock summary"""
    # Get total penerimaan
    total_penerimaan = await db.smartstock.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total_penerimaan"}}}
    ]).to_list(1)

    # Get total pemakaian
    total_pemakaian = await db.sumberpemakaian.aggregate([
        {"$group": {
            "_id": None,
            "total_pemakaian": {"$sum": "$total_pemakaian"}
        }}
    ]).to_list(1)

    # Get average daily usage (last 30 days)
    avg_usage = await db.sumberpemakaian.aggregate([
        {"$sort": {"date": -1}},
        {"$limit": 30},
        {"$group": {
            "_id": None,
            "avg_pemakaian": {"$avg": "$total_pemakaian"}
        }}
    ]).to_list(1)
    
    # Latent-bug hotfix (Phase-5 CP2, 2026-05-11): MongoDB aggregation can return
    # None for $sum/$avg when source fields are null; dict.get(key, default) does NOT
    # convert None → default. Coerce with `or 0` so downstream arithmetic is safe.
    # RESEARCH §Focus 6 flagged this exposure risk; smoke test caught it on real data.
    penerimaan = (total_penerimaan[0].get("total") if total_penerimaan else 0) or 0
    pemakaian = (total_pemakaian[0].get("total_pemakaian") if total_pemakaian else 0) or 0
    avg_daily = (avg_usage[0].get("avg_pemakaian") if avg_usage else 0) or 0

    current_stock = penerimaan - pemakaian
    days_of_supply = int(current_stock / avg_daily) if avg_daily > 0 else 0

    return {
        "total_penerimaan": penerimaan,
        "total_pemakaian": pemakaian,
        "current_stock": current_stock,
        "avg_daily_usage": avg_daily,
        "days_of_supply": days_of_supply,
        "status": "CRITICAL" if days_of_supply < 7 else "WARNING" if days_of_supply < 14 else "OK"
    }

@router.get("/ai/quick/coa-alerts")
async def get_coa_alerts(user: dict = Depends(get_current_user)):
    """Get quick COA reconciliation alerts"""
    # Get all COA data
    all_coa = await db.coa_reconciliation.find({}, {"_id": 0}).to_list(10000)
    
    if not all_coa:
        return {
            "total_records": 0,
            "kritis_count": 0,
            "umpire_count": 0,
            "potential_loss": 0,
            "top_supplier_deviasi": None
        }
    
    # Count kritis status
    kritis_count = sum(1 for c in all_coa if str(c.get("status", "")).lower() in {"critical", "kritis"})
    
    # Count umpire in progress
    umpire_count = sum(1 for c in all_coa if c.get("umpire_status") not in [None, "none", ""])

    po_records = await db.po_batubara.find({}, {"_id": 0}).to_list(50000)
    coa_kpis = calculate_kpis(all_coa, po_records=po_records)

    supplier_deviasi = {}
    
    for c in all_coa:
        delta = c.get("delta_loading_internal", 0) or 0
        supplier = c.get("suppliers") or c.get("supplier") or "Unknown"
        
        if supplier not in supplier_deviasi:
            supplier_deviasi[supplier] = []
        supplier_deviasi[supplier].append(abs(delta))
    
    # Find supplier with highest average deviation
    top_supplier = None
    max_avg_deviasi = 0
    for supplier, deviasi_list in supplier_deviasi.items():
        if deviasi_list:
            avg = sum(deviasi_list) / len(deviasi_list)
            if avg > max_avg_deviasi:
                max_avg_deviasi = avg
                top_supplier = {"name": supplier, "avg_deviasi": avg}
    
    return {
        "total_records": len(all_coa),
        "kritis_count": kritis_count,
        "umpire_count": umpire_count,
        "potential_loss": coa_kpis["potential_loss_rp"],
        "potential_loss_price_basis": coa_kpis["potential_loss_price_basis"],
        "potential_loss_price_source_counts": coa_kpis["potential_loss_price_source_counts"],
        "umpire_savings": coa_kpis["umpire_savings_rp"],
        "top_supplier_deviasi": top_supplier
    }


@router.get("/ai/quick/contextual-prompts")
async def get_contextual_prompts(user: dict = Depends(get_current_user)):
    """Ready-made operational prompts backed by contextual AI data slices."""
    return {
        "items": [
            {
                "id": "daily-summary",
                "module": "general",
                "title": "Ringkasan Harian",
                "prompt": "Buat ringkasan harian operasional bahan bakar: posisi stock, realisasi kedatangan, kualitas, dan dispute prioritas hari ini.",
            },
            {
                "id": "seven-day-stock-risk",
                "module": "smart_stock",
                "title": "Risiko Stock 7 Hari",
                "prompt": "Analisis risiko stock 7 hari ke depan. Hitung days of supply, status reorder, dan tindakan prioritas.",
            },
            {
                "id": "supplier-dispute-pattern",
                "module": "coa_reconciliation",
                "title": "Pola Dispute Supplier",
                "prompt": "Identifikasi pola dispute per supplier dari COA dan umpire. Supplier mana yang paling perlu diprioritaskan untuk review?",
            },
            {
                "id": "weekly-report-draft",
                "module": "general",
                "title": "Draft Laporan Mingguan",
                "prompt": "Susun draft laporan mingguan manajemen berisi stock, jadwal vs realisasi, supplier performance, potential loss, dan status dispute/umpire.",
            },
            {
                "id": "management-memo",
                "module": "general",
                "title": "Memo Manajemen",
                "prompt": "Buat memo manajemen Indonesia dari data laporan saat ini. Cantumkan rekomendasi, batasan data, dan source slice yang dipakai.",
            },
        ]
    }


@router.get("/ai/advisor/operational")
async def get_operational_advisor(
    period: Optional[str] = Query("all"),
    supplier: Optional[str] = Query("all"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Source-backed operational recommendations and Indonesian management memo."""
    return await build_operational_advisor(period, supplier, date_from, date_to, user)

# ==================== AI CONVERSATION SESSIONS ====================

@router.get("/ai/sessions")
async def get_ai_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """Get list of user's AI conversation sessions"""
    skip = (page - 1) * page_size
    
    # Aggregate to get unique sessions with their last message
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": "$session_id",
            "module": {"$first": "$module"},
            "last_query": {"$first": "$query"},
            "last_response": {"$first": "$response"},
            "message_count": {"$sum": 1},
            "created_at": {"$min": "$created_at"},
            "updated_at": {"$max": "$created_at"}
        }},
        {"$sort": {"updated_at": -1}},
        {"$skip": skip},
        {"$limit": page_size}
    ]
    
    sessions = await ai_chat_collection.aggregate(pipeline).to_list(page_size)
    
    # Count total unique sessions
    total_pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$group": {"_id": "$session_id"}},
        {"$count": "total"}
    ]
    total_result = await ai_chat_collection.aggregate(total_pipeline).to_list(1)
    total = total_result[0]["total"] if total_result else 0
    
    return {
        "items": sessions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/ai/sessions/{session_id}")
async def get_session_messages(session_id: str, user: dict = Depends(get_current_user)):
    """Get all messages in a specific session"""
    messages = await ai_chat_collection.find(
        {"session_id": session_id, "user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    if not messages:
        raise HTTPException(status_code=404, detail="Session tidak ditemukan")
    
    return {
        "session_id": session_id,
        "module": messages[0].get("module") if messages else "general",
        "messages": messages,
        "message_count": len(messages)
    }

@router.delete("/ai/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific conversation session"""
    result = await ai_chat_collection.delete_many({"session_id": session_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session tidak ditemukan")
    return {"message": f"Berhasil menghapus {result.deleted_count} pesan dalam sesi"}

@router.post("/ai/sessions/new")
async def create_new_session(module: str = "general", user: dict = Depends(get_current_user)):
    """Create a new conversation session"""
    session_id = f"tenayan-ai-{user['id']}-{uuid.uuid4()}"
    return {
        "session_id": session_id,
        "module": module,
        "message": "Sesi percakapan baru telah dibuat"
    }

# ==================== AI CONVERSATIONS (D-18, OPS-04) ====================

@router.get("/ai/conversations")
async def list_conversations(user: dict = Depends(get_current_user)):
    """List user's conversations from ai_chat_history grouped by session_id, newest first."""
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$sort": {"created_at": 1}},
        {"$group": {
            "_id": "$session_id",
            "first_query": {"$first": "$query"},
            "last_message_at": {"$max": "$created_at"},
        }},
        {"$sort": {"last_message_at": -1}},
    ]
    sessions = await ai_chat_collection.aggregate(pipeline).to_list(100)
    return [
        {
            "id": s["_id"],
            "title": (s.get("first_query") or "Percakapan tanpa judul")[:50],
            "last_message_at": s["last_message_at"],
        }
        for s in sessions
    ]


@router.post("/ai/conversations", status_code=201)
async def create_conversation(user: dict = Depends(get_current_user)):
    """Create a new empty conversation. Returns conversation id."""
    conv_id = f"tenayan-ai-{user['id']}-{uuid.uuid4()}"
    return {
        "id": conv_id,
        "title": "Percakapan tanpa judul",
        "last_message_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ai/conversations/{conv_id}/messages")
async def get_conversation_messages(
    conv_id: str,
    before: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    """Paginated message retrieval for a conversation. Returns messages oldest-first."""
    query: dict = {"session_id": conv_id, "user_id": user["id"]}
    if before:
        query["id"] = {"$lt": before}
    docs = await ai_chat_collection.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    if not docs and before is None:
        raise HTTPException(status_code=404, detail="Percakapan tidak ditemukan")
    messages = []
    for doc in reversed(docs):
        messages.append({
            "id": f"u-{doc['id']}",
            "role": "user",
            "content": doc.get("query", ""),
            "created_at": doc["created_at"],
        })
        if doc.get("response"):
            messages.append({
                "id": f"a-{doc['id']}",
                "role": "assistant",
                "content": doc["response"],
                "created_at": doc["created_at"],
            })
    return messages


@router.post("/ai/conversations/{conv_id}/messages")
async def send_conversation_message(
    conv_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
    ai: AIClient = Depends(get_ai_client),
):
    """Send a user message; backend calls LLM; persists exchange; returns AI response."""
    body = await request.json()
    content = (body.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="content is required")
    context_bundle = await build_contextual_ai_context("general", None)
    system_prompt = get_system_prompt("general")
    full_content = f"""DATA CONTEXT (structured, bounded, whitelist-only):
{context_bundle["context_text"]}

DATA SLICES USED:
{json.dumps(context_bundle["context_slices"], ensure_ascii=False)}

USER QUERY:
{content}

Berikan jawaban berdasarkan data di atas dan akhiri dengan bagian "Sumber Data"."""
    response = await ai.send_message(conv_id, system_prompt, full_content)
    now_iso = datetime.now(timezone.utc).isoformat()
    doc_id = str(uuid.uuid4())
    await ai_chat_collection.insert_one({
        "id": doc_id,
        "user_id": user["id"],
        "session_id": conv_id,
        "module": "general",
        "query": content,
        "response": response,
        "parameters": None,
        "context_slices": context_bundle["context_slices"],
        "context_limit": context_bundle["context_limit"],
        "created_at": now_iso,
    })
    return {
        "id": f"a-{doc_id}",
        "role": "assistant",
        "content": response,
        "context_slices": context_bundle["context_slices"],
        "created_at": now_iso,
    }

# ==================== SMART BLENDING AI ENDPOINTS ====================

class SmartBlendingRequest(BaseModel):
    target_gcv: float  # Target GCV in kcal/kg (3700-4700)
    max_ash: float  # Max Ash content in % (3.3-6.0)
    max_sulphur: float  # Max Sulphur in % (0.13-2.2)
    max_total_moisture: float = 35.0  # Max Total Moisture in % (25-40)
    max_inherent_moisture: float = 18.0  # Max Inherent Moisture in % (13.8-25)
    min_volatile_matter: float = 35.0  # Min Volatile Matter in % (27.9-40)
    min_fixed_carbon: float = 25.0  # Min Fixed Carbon in % (23-41)
    target_quantity: float  # Target quantity in MT

@router.post("/smart-blending/recommend")
async def get_smart_blending_recommendation(
    request: SmartBlendingRequest,
    user: dict = Depends(get_current_user),
    ai: AIClient = Depends(get_ai_client)
):
    """Get AI-powered smart blending recommendation using Gemini"""
    
    try:
        # Calculate 6 months ago date for filtering suppliers
        from dateutil.relativedelta import relativedelta
        six_months_ago = datetime.now(timezone.utc) - relativedelta(months=6)
        
        # 1. Fetch quality data from suppliers in the last 6 months
        # Filter by various date fields that exist in the collections
        date_filter_vessel = {
            "$or": [
                {"time_arrival": {"$gte": six_months_ago.isoformat()}},
                {"periode_realisasi": {"$gte": six_months_ago.isoformat()}},
                {"created_at": {"$gte": six_months_ago.isoformat()}}
            ]
        }
        date_filter_barge = {
            "$or": [
                {"ta": {"$gte": six_months_ago.isoformat()}},
                {"periode": {"$gte": six_months_ago.isoformat()}},
                {"created_at": {"$gte": six_months_ago.isoformat()}}
            ]
        }
        date_filter_trucking = {
            "$or": [
                {"ta": {"$gte": six_months_ago.isoformat()}},
                {"periode_ta": {"$gte": six_months_ago.isoformat()}},
                {"created_at": {"$gte": six_months_ago.isoformat()}}
            ]
        }
        
        vessels = await db.vessels.find(date_filter_vessel, {"_id": 0}).sort("time_arrival", -1).limit(50).to_list(50)
        barges = await db.barges.find(date_filter_barge, {"_id": 0}).sort("ta", -1).limit(50).to_list(50)
        trucking = await db.trucking.find(date_filter_trucking, {"_id": 0}).sort("ta", -1).limit(50).to_list(50)
        
        # 2. Fetch stock availability from Smart Stock (Sumber Penerimaan)
        latest_stock = await db.smartstock.find_one({}, {"_id": 0}, sort=[("date", -1)])
        
        # 3. Fetch pricing from Merit Order
        merit_order = await db.merit_order.find({}, {"_id": 0}).to_list(100)
        
        # 4. Prepare data for AI analysis
        coal_inventory = []
        
        # Process vessels
        for v in vessels:
            supplier_name = v.get("suppliers", "Unknown")
            if supplier_name and supplier_name != "Unknown":
                coal_inventory.append({
                    "source": "Vessel",
                    "supplier": supplier_name,
                    "type": "MRC" if "MRC" in supplier_name.upper() else "LRC",
                    "gcv_ar": v.get("gcv_arb"),
                    "ash_ar": v.get("ash_arb"),
                    "ts_ar": v.get("ts_arb"),
                    "tm_ar": v.get("tm_arb"),  # Total Moisture
                    "im_adb": v.get("im_adb"),  # Inherent Moisture
                    "vm_ar": v.get("vm_arb"),  # Volatile Matter
                    "fc_ar": v.get("fc_arb"),  # Fixed Carbon
                    "available_mt": v.get("bl_mt", 0),
                    "date": v.get("time_arrival")
                })
        
        # Process barges
        for b in barges:
            supplier_name = b.get("suppliers", "Unknown")
            if supplier_name and supplier_name != "Unknown":
                coal_inventory.append({
                    "source": "Barge",
                    "supplier": supplier_name,
                    "type": "MRC" if "MRC" in supplier_name.upper() else "LRC",
                    "gcv_ar": b.get("gcv_arb"),
                    "ash_ar": b.get("ash_arb"),
                    "ts_ar": b.get("ts_arb"),
                    "tm_ar": b.get("tm_arb"),  # Total Moisture
                    "im_adb": b.get("im_adb"),  # Inherent Moisture
                    "vm_ar": b.get("vm_arb"),  # Volatile Matter
                    "fc_ar": b.get("fc_arb"),  # Fixed Carbon
                    "available_mt": b.get("bl_mt", 0),
                    "date": b.get("time_arrival")
                })
        
        # Process trucking
        for t in trucking:
            supplier_name = t.get("suppliers", "Unknown")
            if supplier_name and supplier_name != "Unknown":
                coal_inventory.append({
                    "source": "Trucking",
                    "supplier": supplier_name,
                    "type": "MRC" if "MRC" in supplier_name.upper() else "LRC",
                    "gcv_ar": t.get("gcv_arb"),
                    "ash_ar": t.get("ash_arb"),
                    "ts_ar": t.get("ts_arb"),
                    "tm_ar": t.get("tm_arb"),  # Total Moisture
                    "im_adb": t.get("im_adb"),  # Inherent Moisture
                    "vm_ar": t.get("vm_arb"),  # Volatile Matter
                    "fc_ar": t.get("fc_arb"),  # Fixed Carbon
                    "available_mt": t.get("quantity", 0),
                    "date": t.get("date_received")
                })
        
        # 5. Create AI prompt for Gemini
        ai_prompt = f"""Anda adalah Ahli Kimia Batubara Digital untuk PLTU Tenayan. Tugas Anda adalah memberikan rekomendasi blending batubara yang optimal.

**PERSYARATAN BLENDING:**
- Target GCV: {request.target_gcv} kcal/kg (As Received)
- Maksimal Kandungan Abu: {request.max_ash}% (As Received)
- Maksimal Total Sulphur: {request.max_sulphur}% (As Received)
- Maksimal Total Moisture: {request.max_total_moisture}% (As Received)
- Maksimal Inherent Moisture: {request.max_inherent_moisture}% (Air Dried Basis)
- Minimal Volatile Matter: {request.min_volatile_matter}% (As Received)
- Minimal Fixed Carbon: {request.min_fixed_carbon}% (As Received)
- Total Kuantitas yang Dibutuhkan: {request.target_quantity:,.0f} MT

**INVENTORI BATUBARA TERSEDIA:**
{json.dumps(coal_inventory, indent=2)}

**CATATAN PENTING:**
- LRC (Low Rank Coal): GCV lebih rendah (3000-4500 kcal/kg), moisture tinggi, lebih murah
- MRC (Medium Rank Coal): GCV lebih tinggi (4500-6000 kcal/kg), moisture rendah, lebih mahal
- Formula blending: Hasil_GCV = (Batubara1_GCV × Batubara1_%) + (Batubara2_GCV × Batubara2_%)
- Prioritas: CAPAI TARGET GCV DULU, kemudian pertimbangkan parameter lainnya
- WAJIB: Gunakan NAMA SUPPLIER ASLI dari data di atas, JANGAN buat nama dummy seperti "Supplier Alpha"
- tm_ar = Total Moisture (As Received), im_adb = Inherent Moisture (Air Dried Basis)
- vm_ar = Volatile Matter (As Received), fc_ar = Fixed Carbon (As Received)

**TUGAS ANDA:**
1. Analisis batubara yang tersedia (pertimbangkan semua parameter: GCV, Abu, Sulphur, Moisture, VM, FC)
2. Hitung persentase blend yang optimal
3. Pastikan target GCV tercapai
4. Jaga semua parameter dalam batas yang ditentukan
5. Rekomendasikan 2-4 batubara untuk blending
6. GUNAKAN nama supplier SEBENARNYA dari data (contoh: "PT PLN BATUBARA", "PT BUKIT ASAM")

**FORMAT OUTPUT (JSON):**
{{
  "recommendation": [
    {{
      "supplier": "PT PLN BATUBARA",
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
    }}
  ],
  "predicted_quality": {{
    "gcv": 4050,
    "ash": 4.8,
    "sulphur": 0.25,
    "total_moisture": 35.0,
    "inherent_moisture": 16.0,
    "volatile_matter": 33.0,
    "fixed_carbon": 27.0
  }},
  "meets_target": true,
  "reasoning": "Jelaskan mengapa blend ini optimal dalam Bahasa Indonesia",
  "cost_warning": "Catatan jika menggunakan batubara mahal (dalam Bahasa Indonesia)"
}}

Respons HANYA dengan JSON yang valid, tanpa teks tambahan. WAJIB gunakan nama supplier asli dari data."""

        # 6. Call AI via injected client (AI_FAKE=1 swaps in FakeAIClient in test env)
        session_id = f"smart-blending-{uuid.uuid4()}"
        system_message = "You are an expert coal blending optimization AI for power plants."
        response = await ai.send_message(session_id, system_message, ai_prompt)
        
        # 7. Parse AI response
        try:
            # Clean response (remove markdown code blocks if present)
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            ai_result = json.loads(clean_response)
            if isinstance(ai_result, dict) and "blend" not in ai_result and isinstance(ai_result.get("recommendation"), list):
                ai_result["blend"] = ai_result["recommendation"]
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            ai_result = {
                "error": "Failed to parse AI response",
                "raw_response": response
            }
        
        return {
            "request": request.dict(),
            "ai_recommendation": ai_result,
            "data_sources": {
                "vessels_count": len(vessels),
                "barges_count": len(barges),
                "trucking_count": len(trucking),
                "latest_stock_date": latest_stock.get("date") if latest_stock else None
            }
        }
    
    except Exception as e:
        logger.error(f"Smart Blending AI error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI recommendation failed: {str(e)}")
