import { useState, useEffect, useMemo, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  FileText,
  Search,
  Download,
  Filter,
  Loader2,
  Ship,
  Anchor,
  Truck,
  Leaf,
  FileSpreadsheet,
  File,
  ShoppingCart,
  ListOrdered,
  RotateCcw,
  BarChart3,
  Brain,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus
} from "lucide-react";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import jsPDF from "jspdf";
import "jspdf-autotable";
import DashboardDrilldownBar from "@/components/DashboardDrilldownBar";
import { buildResetPath, dashboardEmptyText, parseDashboardDrilldown, periodToDateRange, periodToYearMonth } from "@/utils/dashboardDrilldown";

const API_URL = process.env.REACT_APP_BACKEND_URL;
const PAGE_SIZE = 50;
const REPORT_PERIOD_OPTIONS = [
  { value: "all", label: "Semua Periode" },
  { value: "2026", label: "2026" },
  { value: "2026-01", label: "Januari 2026" },
  { value: "2026-02", label: "Februari 2026" },
  { value: "2026-03", label: "Maret 2026" },
  { value: "2026-04", label: "April 2026" },
  { value: "2026-05", label: "Mei 2026" },
  { value: "2025", label: "2025" },
  { value: "2024", label: "2024" }
];

const getInitialReportState = () => {
  const params = new URLSearchParams(window.location.search);
  const tab = params.get("tab");
  const mode = params.get("mode");
  const period = params.get("period") || "all";
  const periodRange = periodToDateRange(period);
  const validTabs = ["management", "vessel", "barge", "trucking", "biomassa", "po_batubara", "merit_order"];
  const initialTab = validTabs.includes(tab)
    ? tab
    : validTabs.includes(mode)
      ? mode
      : (params.has("period") || params.has("supplier") || params.has("date_from") || params.has("date_to"))
        ? "management"
        : "vessel";
  return {
    activeTab: initialTab,
    supplier: params.get("supplier") || "all",
    period,
    dateFrom: params.get("date_from") || periodRange.dateFrom || "",
    dateTo: params.get("date_to") || periodRange.dateTo || ""
  };
};

const LaporanPage = () => {
  const { getAuthHeader } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const drilldown = useMemo(() => parseDashboardDrilldown(location.search), [location.search]);
  const initialState = getInitialReportState();
  const [activeTab, setActiveTab] = useState(initialState.activeTab);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [data, setData] = useState([]);
  const [managementReport, setManagementReport] = useState(null);
  const [advisorReport, setAdvisorReport] = useState(null);
  const [search, setSearch] = useState("");
  const [filterSupplier, setFilterSupplier] = useState(initialState.supplier);
  const [filterPeriod, setFilterPeriod] = useState(initialState.period);
  const [dateFrom, setDateFrom] = useState(initialState.dateFrom);
  const [dateTo, setDateTo] = useState(initialState.dateTo);
  const [suppliersList, setSuppliersList] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });
  const categories = [
    { id: "management", label: "Manajemen", icon: BarChart3, color: "cyan" },
    { id: "vessel", label: "Vessel", icon: Ship, color: "cyan" },
    { id: "barge", label: "Barge", icon: Anchor, color: "blue" },
    { id: "trucking", label: "Trucking", icon: Truck, color: "amber" },
    { id: "biomassa", label: "Biomassa", icon: Leaf, color: "green" },
    { id: "po_batubara", label: "PO Batubara", icon: ShoppingCart, color: "purple" },
    { id: "merit_order", label: "Merit Order", icon: ListOrdered, color: "pink" }
  ];

  const fetchSuppliers = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/suppliers`, {
        headers: getAuthHeader()
      });
      setSuppliersList(response.data.suppliers || []);
    } catch (error) {
      console.error("Error fetching suppliers:", error);
    }
  }, [getAuthHeader]);

  const fetchData = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      if (activeTab === "management") {
        const params = {};
        if (filterPeriod && filterPeriod !== "all") params.period = filterPeriod;
        if (filterSupplier && filterSupplier !== "all") params.supplier = filterSupplier;
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;
        const [reportResponse, advisorResponse] = await Promise.all([
          axios.get(`${API_URL}/api/reports/management`, {
            headers: getAuthHeader(),
            params
          }),
          axios.get(`${API_URL}/api/ai/advisor/operational`, {
            headers: getAuthHeader(),
            params
          })
        ]);
        setManagementReport(reportResponse.data);
        setAdvisorReport(advisorResponse.data);
        setData([]);
        const totalSources = Object.values(reportResponse.data.source_counts || {}).reduce((sum, value) => sum + Number(value || 0), 0);
        setPagination({ page: 1, total: totalSources, totalPages: 1 });
        return;
      }
      setAdvisorReport(null);

      const endpoint = activeTab === "vessel" ? "vessels" : 
                       activeTab === "barge" ? "barges" : 
                       activeTab === "trucking" ? "trucking" : 
                       activeTab === "biomassa" ? "biomassa" :
                       activeTab === "po_batubara" ? "po-batubara" : "merit-order";
      const params = { page, page_size: PAGE_SIZE };
      if (search) params.search = search;
      if (filterSupplier && filterSupplier !== "all") params.supplier = filterSupplier;
      if (["vessel", "barge", "trucking", "biomassa"].includes(activeTab)) {
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;
      }
      if (["po_batubara", "merit_order"].includes(activeTab)) {
        const periodParts = periodToYearMonth(filterPeriod);
        if (periodParts.year) params.year = periodParts.year;
        if (periodParts.month) params.month = periodParts.month;
      }
      
      const response = await axios.get(`${API_URL}/api/${endpoint}`, { 
        headers: getAuthHeader(), 
        params 
      });
      
      // Handle paginated response
      const responseData = response.data;
      if (responseData.items) {
        setData(responseData.items);
        setPagination({
          page: responseData.page,
          total: responseData.total,
          totalPages: responseData.total_pages
        });
      } else {
        // Fallback for old response format
        setData(Array.isArray(responseData) ? responseData : []);
        setPagination({ page: 1, total: responseData.length || 0, totalPages: 1 });
      }
    } catch (error) {
      toast.error("Gagal memuat data laporan");
    } finally {
      setLoading(false);
    }
  }, [activeTab, dateFrom, dateTo, filterPeriod, filterSupplier, getAuthHeader, search]);

  useEffect(() => {
    fetchData(1);
  }, [fetchData]);

  useEffect(() => {
    fetchSuppliers();
  }, [fetchSuppliers]);

  const resetFilters = () => {
    setSearch("");
    setFilterSupplier("all");
    setFilterPeriod("all");
    setDateFrom("");
    setDateTo("");
    setPagination({ page: 1, total: 0, totalPages: 0 });
  };

  const resetDashboardFilters = () => {
    resetFilters();
    navigate(buildResetPath(location.pathname, location.search), { replace: true });
  };

  const getTableColumns = () => {
    switch (activeTab) {
      case "vessel":
        return [
          { key: "periode_realisasi", label: "Periode" },
          { key: "shipment_code", label: "Shipment" },
          { key: "name_of_vessel", label: "Nama Vessel" },
          { key: "suppliers", label: "Supplier" },
          { key: "bl_mt", label: "B/L (MT)", type: "number" },
          { key: "ds_mt", label: "DS (MT)", type: "number" },
          { key: "gcv_arb", label: "GCV ARB", type: "number" }
        ];
      case "barge":
        return [
          { key: "periode", label: "Periode" },
          { key: "shipment_code", label: "Shipment" },
          { key: "suppliers", label: "Supplier" },
          { key: "tb", label: "TB" },
          { key: "bg", label: "BG" },
          { key: "bl_mt", label: "B/L (MT)", type: "number" },
          { key: "gcv_arb", label: "GCV ARB", type: "number" }
        ];
      case "trucking":
        return [
          { key: "periode_realisasi", label: "Periode" },
          { key: "shipment_code", label: "Shipment" },
          { key: "suppliers", label: "Supplier" },
          { key: "coal_from", label: "Lokasi" },
          { key: "ds_mt", label: "Total Tonase (MT)", type: "number" },
          { key: "gcv_arb", label: "GCV ARB", type: "number" }
        ];
      case "biomassa":
        return [
          { key: "periode", label: "Periode" },
          { key: "shipment_code", label: "Shipment" },
          { key: "suppliers", label: "Supplier" },
          { key: "coal_from", label: "Asal" },
          { key: "bl_mt", label: "B/L (MT)", type: "number" },
          { key: "gcv_arb", label: "GCV ARB", type: "number" }
        ];
      case "po_batubara":
        return [
          { key: "periode", label: "Periode" },
          { key: "po_number", label: "No. PO" },
          { key: "supplier_name", label: "Supplier" },
          { key: "spec", label: "Spec" },
          { key: "no_shipment", label: "Shipment" },
          { key: "tonase_po", label: "Tonase (MT)", type: "number" },
          { key: "inventory_price", label: "Harga", type: "number" }
        ];
      case "merit_order":
        return [
          { key: "periode", label: "Periode" },
          { key: "pemasok", label: "Pemasok" },
          { key: "moda", label: "Moda" },
          { key: "tipikal_kcal_kg", label: "Tipikal (kcal/kg)", type: "number" },
          { key: "jenis_kontrak", label: "Jenis Kontrak" },
          { key: "harga_cif", label: "Harga CIF", type: "number" },
          { key: "rp_kcal", label: "Rp/Kcal", type: "number" }
        ];
      default:
        return [];
    }
  };

  const formatValue = (value, type) => {
    if (value === null || value === undefined) return "-";
    if (type === "number") return value.toLocaleString("id-ID");
    return value;
  };

  const formatNumber = (value, digits = 0) => {
    if (value === null || value === undefined) return "-";
    return Number(value).toLocaleString("id-ID", { maximumFractionDigits: digits });
  };

  const trendTone = (metric = {}) => {
    if (metric.status === "improving") return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
    if (metric.status === "worsening") return "bg-red-500/15 text-red-300 border-red-500/30";
    if (metric.status === "stable") return "bg-blue-500/15 text-blue-300 border-blue-500/30";
    return "bg-slate-500/15 text-slate-300 border-slate-500/30";
  };

  const advisorConfidenceTone = (level) => {
    if (level === "high") return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
    if (level === "medium") return "border-amber-500/40 bg-amber-500/10 text-amber-300";
    return "border-red-500/40 bg-red-500/10 text-red-300";
  };

  const urgencyTone = (urgency) => {
    if (urgency === "critical") return "bg-red-500/20 text-red-300";
    if (urgency === "warning") return "bg-amber-500/20 text-amber-300";
    if (urgency === "watch") return "bg-blue-500/20 text-blue-300";
    return "bg-cyan-500/20 text-cyan-300";
  };

  const TrendDirectionIcon = ({ metric }) => {
    if (metric?.direction === "up") return <TrendingUp className="w-4 h-4" />;
    if (metric?.direction === "down") return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const trendMetricRows = () => {
    const metrics = managementReport?.trend_analytics?.metrics || {};
    return Object.entries(metrics).map(([key, metric]) => ({
      Area: key,
      Metrik: metric.label,
      Current: metric.current,
      Previous: metric.previous,
      Delta: metric.delta,
      "Delta %": metric.delta_percent ?? "-",
      Direction: metric.direction_label,
      Status: metric.status,
      Satuan: metric.unit || "-"
    }));
  };

  const supplierTrendRows = () => {
    return (managementReport?.trend_analytics?.supplier_trends || []).map((item) => ({
      Supplier: item.supplier,
      Risk: item.risk_label,
      "Risk Score": item.risk_score,
      "Volume Current": item.volume?.current,
      "Volume Previous": item.volume?.previous,
      "Volume Direction": item.volume?.direction_label,
      "Timeliness Current": item.timeliness?.current,
      "Timeliness Previous": item.timeliness?.previous,
      "Quality Delta Current": item.quality_delta?.current,
      "Quality Delta Previous": item.quality_delta?.previous,
      "Disputes Current": item.disputes?.current,
      "Disputes Previous": item.disputes?.previous
    }));
  };

  const stockForecastRows = () => {
    const forecast = managementReport?.trend_analytics?.stock_forecast || {};
    return (forecast.horizons || []).map((item) => ({
      Horizon: `${item.days} hari`,
      "Expected Arrivals": item.expected_arrivals,
      "Projected Stock": item.projected_stock,
      "Projected Coverage Days": item.projected_coverage_days,
      Status: item.status,
      "Avg Daily Usage": forecast.avg_daily_usage,
      Confidence: forecast.confidence
    }));
  };

  const managementSummaryRows = () => {
    if (!managementReport) return [];
    return [
      { Area: "Stock", Metrik: "Stock Saat Ini", Nilai: formatNumber(managementReport.stock?.current_stock), Satuan: "MT" },
      { Area: "Stock", Metrik: "Days of Supply", Nilai: managementReport.stock?.days_of_supply ?? "-", Satuan: "hari" },
      { Area: "Kedatangan", Metrik: "Jadwal", Nilai: formatNumber(managementReport.arrivals?.scheduled_tonnage), Satuan: "MT" },
      { Area: "Kedatangan", Metrik: "Realisasi", Nilai: formatNumber(managementReport.arrivals?.realized_tonnage), Satuan: "MT" },
      { Area: "Kedatangan", Metrik: "Fulfillment Tonase", Nilai: formatNumber(managementReport.arrivals?.tonnage_fulfillment_rate, 2), Satuan: "%" },
      { Area: "Kedatangan", Metrik: "Jadwal At-risk", Nilai: formatNumber(managementReport.arrivals?.at_risk_count), Satuan: "jadwal" },
      { Area: "Kualitas", Metrik: "Rata-rata GCV", Nilai: formatNumber(managementReport.quality?.avg_gcv, 2), Satuan: "kcal/kg" },
      { Area: "Kualitas", Metrik: "Rata-rata Delta COA", Nilai: formatNumber(managementReport.quality?.avg_coa_delta, 2), Satuan: "kcal/kg" },
      { Area: "Potential Loss", Metrik: "Selisih Internal", Nilai: formatNumber(managementReport.potential_loss?.potential_loss_mt, 2), Satuan: "MT" },
      { Area: "Dispute", Metrik: "Critical", Nilai: formatNumber(managementReport.disputes?.critical_count), Satuan: "record" },
      { Area: "Dispute", Metrik: "Warning", Nilai: formatNumber(managementReport.disputes?.warning_count), Satuan: "record" },
      { Area: "Umpire", Metrik: "Aktif", Nilai: formatNumber(managementReport.disputes?.umpire?.active), Satuan: "record" },
      { Area: "Umpire", Metrik: "Stale", Nilai: formatNumber(managementReport.disputes?.stale_count), Satuan: "record" }
    ];
  };

  const exportManagementExcel = () => {
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(managementSummaryRows()), "Ringkasan");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(trendMetricRows()), "Trend Analytics");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(supplierTrendRows()), "Supplier Trends");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(stockForecastRows()), "Stock Forecast");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(managementReport.supplier_scorecard || []), "Supplier Scorecard");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(managementReport.supplier_performance || []), "Supplier Volume");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(advisorReport?.recommendations || []), "AI Advisor");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([["Memo Manajemen"], [advisorReport?.memo_draft || "-"]]), "Memo");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(Object.entries(managementReport.filter_scope || {}).map(([filter, value]) => ({ filter, value: value ?? "all" }))), "Filter Scope");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(managementReport.source_slices || []), "Source Slices");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(Object.entries(managementReport.source_counts || {}).map(([source, count]) => ({ source, count }))), "Traceability");
    const fileName = `Laporan_Manajemen_${new Date().toISOString().split("T")[0]}.xlsx`;
    XLSX.writeFile(wb, fileName);
    toast.success(`Berhasil export ke ${fileName}`);
  };

  const exportManagementPDF = () => {
    const doc = new jsPDF("landscape", "mm", "a4");
    const trendRows = trendMetricRows();
    const forecastRows = stockForecastRows();
    doc.setFontSize(16);
    doc.setFont("helvetica", "bold");
    doc.text("Laporan Manajemen Bahan Bakar", 14, 15);
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.text(`Generated: ${formatDateForExport(managementReport.generated_at)} | Period: ${managementReport.period || "all"} | Supplier: ${managementReport.supplier || "all"}`, 14, 22);
    doc.autoTable({
      head: [["Area", "Metrik", "Nilai", "Satuan"]],
      body: managementSummaryRows().map(row => [row.Area, row.Metrik, row.Nilai, row.Satuan]),
      startY: 30,
      styles: { fontSize: 9, cellPadding: 2 },
      headStyles: { fillColor: [30, 41, 59], textColor: 255 }
    });
    if (trendRows.length > 0) {
      doc.autoTable({
        head: [["Metrik", "Current", "Previous", "Delta", "Arah", "Status"]],
        body: trendRows.map(row => [row.Metrik, row.Current, row.Previous, row.Delta, row.Direction, row.Status]),
        startY: doc.lastAutoTable.finalY + 8,
        styles: { fontSize: 8, cellPadding: 2 },
        headStyles: { fillColor: [8, 145, 178], textColor: 255 }
      });
    }
    if (forecastRows.length > 0) {
      doc.autoTable({
        head: [["Horizon", "Expected Arrivals", "Projected Stock", "Coverage", "Status"]],
        body: forecastRows.map(row => [row.Horizon, row["Expected Arrivals"], row["Projected Stock"], row["Projected Coverage Days"], row.Status]),
        startY: doc.lastAutoTable.finalY + 8,
        styles: { fontSize: 8, cellPadding: 2 },
        headStyles: { fillColor: [21, 128, 61], textColor: 255 }
      });
    }
    doc.autoTable({
      head: [["Rank", "Supplier", "Risk", "Realisasi MT", "Delta COA", "Dispute"]],
      body: (managementReport.supplier_scorecard || []).slice(0, 10).map(row => [
        row.rank,
        row.supplier,
        row.risk_status,
        formatNumber(row.realized_tonnage),
        formatNumber(row.avg_coa_delta, 2),
        row.active_disputes
      ]),
      startY: doc.lastAutoTable.finalY + 8,
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [15, 23, 42], textColor: 255 }
    });
    doc.autoTable({
      head: [["AI Advisor", "Severity", "Source"]],
      body: (advisorReport?.recommendations || []).slice(0, 8).map(row => [row.title, row.severity, row.source_slice]),
      startY: doc.lastAutoTable.finalY + 8,
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [88, 28, 135], textColor: 255 }
    });
    doc.autoTable({
      head: [["Source", "Count"]],
      body: Object.entries(managementReport.source_counts || {}).map(([source, count]) => [source, count]),
      startY: doc.lastAutoTable.finalY + 8,
      styles: { fontSize: 9, cellPadding: 2 },
      headStyles: { fillColor: [15, 23, 42], textColor: 255 }
    });
    const fileName = `Laporan_Manajemen_${new Date().toISOString().split("T")[0]}.pdf`;
    doc.save(fileName);
    toast.success(`Berhasil export ke ${fileName}`);
  };

  const formatDateForExport = (value) => {
    if (!value) return "-";
    try {
      const date = new Date(value);
      return date.toLocaleDateString("id-ID", { year: "numeric", month: "short", day: "numeric" });
    } catch {
      return value;
    }
  };

  const getTotalTonase = () => {
    if (activeTab === "po_batubara") {
      return data.reduce((sum, item) => sum + (item.tonase_po || 0), 0);
    }
    if (activeTab === "merit_order") {
      return data.reduce((sum, item) => sum + (item.harga_cif || 0), 0);
    }
    const field = activeTab === "trucking" ? "ds_mt" : "bl_mt";
    return data.reduce((sum, item) => sum + (item[field] || 0), 0);
  };

  const getTonaseLabel = () => {
    if (activeTab === "po_batubara") return "Total Tonase PO";
    if (activeTab === "merit_order") return "Total Harga CIF";
    return "Total Tonase";
  };

  const getTonaseUnit = () => {
    if (activeTab === "merit_order") return "Rupiah";
    return "MT (Metric Ton)";
  };

  const getAvgGCV = () => {
    if (activeTab === "po_batubara" || activeTab === "merit_order") {
      // For PO Batubara, use tipikal from merit order or return 0
      if (activeTab === "merit_order") {
        const validData = data.filter(item => item.tipikal_kcal_kg);
        if (validData.length === 0) return 0;
        return validData.reduce((sum, item) => sum + item.tipikal_kcal_kg, 0) / validData.length;
      }
      return 0;
    }
    const validData = data.filter(item => item.gcv_arb);
    if (validData.length === 0) return 0;
    return validData.reduce((sum, item) => sum + item.gcv_arb, 0) / validData.length;
  };

  const getGCVLabel = () => {
    if (activeTab === "merit_order") return "Rata-rata Tipikal";
    if (activeTab === "po_batubara") return "Rata-rata Harga";
    return "Rata-rata GCV";
  };

  // Export to Excel
  const handleExportExcel = () => {
    if (activeTab === "management") {
      if (!managementReport) {
        toast.error("Tidak ada data untuk diekspor");
        return;
      }
      setExporting(true);
      try {
        exportManagementExcel();
      } catch (error) {
        console.error("Export error:", error);
        toast.error("Gagal export ke Excel");
      } finally {
        setExporting(false);
      }
      return;
    }

    if (data.length === 0) {
      toast.error("Tidak ada data untuk diekspor");
      return;
    }
    
    setExporting(true);
    try {
      const columns = getTableColumns();
      const currentCategory = categories.find(c => c.id === activeTab);
      
      // Prepare data for export
      const exportData = data.map((item, index) => {
        const row = { "No": index + 1 };
        columns.forEach(col => {
          let value = item[col.key];
          if (col.key.includes("periode") || col.key.includes("ta") || col.key.includes("time")) {
            value = formatDateForExport(value);
          } else if (col.type === "number" && value !== null && value !== undefined) {
            value = Number(value);
          }
          row[col.label] = value ?? "-";
        });
        return row;
      });

      // Add summary row
      exportData.push({});
      exportData.push({
        "No": "",
        [columns[0].label]: "TOTAL",
        [columns.find(c => c.type === "number")?.label || "Total"]: getTotalTonase(),
      });
      exportData.push({
        "No": "",
        [columns[0].label]: "Rata-rata GCV",
        [columns.find(c => c.key === "gcv_arb")?.label || "GCV"]: getAvgGCV().toFixed(2),
      });

      const ws = XLSX.utils.json_to_sheet(exportData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, currentCategory?.label || "Data");
      
      // Auto-size columns
      const colWidths = columns.map(col => ({ wch: Math.max(col.label.length + 2, 15) }));
      colWidths.unshift({ wch: 5 }); // No column
      ws["!cols"] = colWidths;

      const fileName = `Laporan_${currentCategory?.label}_${new Date().toISOString().split("T")[0]}.xlsx`;
      XLSX.writeFile(wb, fileName);
      toast.success(`Berhasil export ke ${fileName}`);
    } catch (error) {
      console.error("Export error:", error);
      toast.error("Gagal export ke Excel");
    } finally {
      setExporting(false);
    }
  };

  // Export to PDF
  const handleExportPDF = () => {
    if (activeTab === "management") {
      if (!managementReport) {
        toast.error("Tidak ada data untuk diekspor");
        return;
      }
      setExporting(true);
      try {
        exportManagementPDF();
      } catch (error) {
        console.error("PDF Export error:", error);
        toast.error("Gagal export ke PDF");
      } finally {
        setExporting(false);
      }
      return;
    }

    if (data.length === 0) {
      toast.error("Tidak ada data untuk diekspor");
      return;
    }

    setExporting(true);
    try {
      const columns = getTableColumns();
      const currentCategory = categories.find(c => c.id === activeTab);
      
      const doc = new jsPDF("landscape", "mm", "a4");
      
      // Header
      doc.setFontSize(16);
      doc.setFont("helvetica", "bold");
      doc.text(`Laporan Data ${currentCategory?.label}`, 14, 15);
      
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      doc.text(`PLTU Tenayan - Sistem Manajemen Bahan Bakar Digital`, 14, 22);
      doc.text(`Tanggal Export: ${new Date().toLocaleDateString("id-ID", { 
        weekday: "long", year: "numeric", month: "long", day: "numeric" 
      })}`, 14, 28);

      // Summary
      doc.setFontSize(10);
      doc.text(`Total Data: ${data.length} record`, 14, 36);
      doc.text(`Total Tonase: ${getTotalTonase().toLocaleString("id-ID")} MT`, 80, 36);
      doc.text(`Rata-rata GCV: ${getAvgGCV().toLocaleString("id-ID", { maximumFractionDigits: 2 })} Kcal/Kg`, 160, 36);

      // Table
      const tableColumns = ["No", ...columns.map(c => c.label)];
      const tableData = data.map((item, index) => {
        const row = [index + 1];
        columns.forEach(col => {
          let value = item[col.key];
          if (col.key.includes("periode") || col.key.includes("ta") || col.key.includes("time")) {
            value = formatDateForExport(value);
          } else if (col.type === "number" && value !== null && value !== undefined) {
            value = Number(value).toLocaleString("id-ID");
          }
          row.push(value ?? "-");
        });
        return row;
      });

      doc.autoTable({
        head: [tableColumns],
        body: tableData,
        startY: 42,
        styles: { fontSize: 8, cellPadding: 2 },
        headStyles: { fillColor: [30, 41, 59], textColor: 255 },
        alternateRowStyles: { fillColor: [241, 245, 249] },
        margin: { left: 14, right: 14 }
      });

      // Footer
      const pageCount = doc.internal.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.text(`Halaman ${i} dari ${pageCount}`, doc.internal.pageSize.width - 30, doc.internal.pageSize.height - 10);
      }

      const fileName = `Laporan_${currentCategory?.label}_${new Date().toISOString().split("T")[0]}.pdf`;
      doc.save(fileName);
      toast.success(`Berhasil export ke ${fileName}`);
    } catch (error) {
      console.error("PDF Export error:", error);
      toast.error("Gagal export ke PDF");
    } finally {
      setExporting(false);
    }
  };

  const columns = getTableColumns();
  const currentCategory = categories.find(c => c.id === activeTab);
  const reportTrend = managementReport?.trend_analytics || {};
  const reportTrendMetrics = reportTrend.metrics || {};
  const reportForecast = reportTrend.stock_forecast || {};
  const advisorConfidence = advisorReport?.confidence || {};
  const advisorLimitations = advisorReport?.limitations || [];
  const advisorGroups = advisorReport?.recommendation_groups || [];

  return (
    <div className="space-y-6" data-testid="laporan-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <FileText className="w-8 h-8 text-purple-400" />
            Laporan Data
          </h1>
          <p className="text-slate-400 mt-1">Rekapitulasi data penerimaan bahan bakar</p>
        </div>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="outline" 
              className="border-slate-700 text-slate-300 hover:bg-slate-800" 
              data-testid="export-btn"
              disabled={exporting || (activeTab === "management" ? !managementReport : data.length === 0)}
            >
              {exporting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              Export
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="bg-slate-900 border-slate-700">
            <DropdownMenuItem 
              onClick={handleExportExcel}
              className="text-slate-300 hover:bg-slate-800 cursor-pointer"
              data-testid="export-excel-btn"
            >
              <FileSpreadsheet className="w-4 h-4 mr-2 text-green-400" />
              Export ke Excel (.xlsx)
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={handleExportPDF}
              className="text-slate-300 hover:bg-slate-800 cursor-pointer"
              data-testid="export-pdf-btn"
            >
              <File className="w-4 h-4 mr-2 text-red-400" />
              Export ke PDF
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <DashboardDrilldownBar drilldown={drilldown} onReset={resetDashboardFilters} />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass-card border-white/5 p-4">
          <p className="text-slate-400 text-sm">Total Data</p>
          <p className="text-2xl font-bold text-white mt-1">{activeTab === "management" ? formatNumber(pagination.total) : (pagination.total || data.length)}</p>
          <p className="text-slate-500 text-xs mt-1">record {currentCategory?.label}</p>
        </Card>
        <Card className="glass-card border-white/5 p-4">
          <p className="text-slate-400 text-sm">{activeTab === "management" ? "Stock Saat Ini" : getTonaseLabel()}</p>
          <p className="text-2xl font-bold text-cyan-400 mt-1">{activeTab === "management" ? formatNumber(managementReport?.stock?.current_stock) : getTotalTonase().toLocaleString("id-ID")}</p>
          <p className="text-slate-500 text-xs mt-1">{activeTab === "management" ? "MT" : getTonaseUnit()}</p>
        </Card>
        <Card className="glass-card border-white/5 p-4">
          <p className="text-slate-400 text-sm">{activeTab === "management" ? "Fulfillment Kedatangan" : getGCVLabel()}</p>
          <p className="text-2xl font-bold text-green-400 mt-1">{activeTab === "management" ? formatNumber(managementReport?.arrivals?.tonnage_fulfillment_rate, 2) : getAvgGCV().toLocaleString("id-ID", { maximumFractionDigits: 2 })}</p>
          <p className="text-slate-500 text-xs mt-1">{activeTab === "management" ? "% tonase PO vs realisasi" : "Kcal/Kg (ARB)"}</p>
        </Card>
      </div>

      <Card className="glass-card border-white/5 p-4">
        <Tabs value={activeTab} onValueChange={(val) => { setActiveTab(val); setPagination({ page: 1, total: 0, totalPages: 0 }); }} className="w-full">
          <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 lg:grid-cols-7 bg-slate-900/50 mb-4 h-auto">
            {categories.map(cat => (
              <TabsTrigger 
                key={cat.id} 
                value={cat.id} 
                className={`text-xs data-[state=active]:bg-${cat.color}-500/20`}
                data-testid={`tab-${cat.id}`}
              >
                <cat.icon className="w-4 h-4 mr-1 hidden sm:block" />
                <span className="truncate">{cat.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[minmax(180px,1fr)_180px_250px_160px_160px_auto] gap-3 items-end mb-4">
            <div className="relative">
              <Label className="text-slate-400 text-xs">Cari</Label>
              <Search className="absolute left-3 bottom-3 w-4 h-4 text-slate-500" />
              <Input
                placeholder="Cari data..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-slate-950/50 border-slate-800 text-white"
                data-testid="search-laporan-input"
              />
            </div>
            <Select value={filterPeriod} onValueChange={(val) => { setFilterPeriod(val); setPagination({ page: 1, total: 0, totalPages: 0 }); }} disabled={activeTab !== "management"}>
              <SelectTrigger className="w-full bg-slate-950/50 border-slate-800 text-white disabled:opacity-40" data-testid="filter-period-select">
                <BarChart3 className="w-4 h-4 mr-2" />
                <SelectValue placeholder="Periode Laporan" />
              </SelectTrigger>
              <SelectContent className="bg-[#0B1221] border-slate-800 max-h-[300px]">
                {REPORT_PERIOD_OPTIONS.map((item) => (
                  <SelectItem key={item.value} value={item.value} className="text-white text-sm">
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterSupplier} onValueChange={(val) => { setFilterSupplier(val); setPagination({ page: 1, total: 0, totalPages: 0 }); }}>
              <SelectTrigger className="w-full bg-slate-950/50 border-slate-800 text-white" data-testid="filter-supplier-select">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue placeholder="Filter Supplier" />
              </SelectTrigger>
              <SelectContent className="bg-[#0B1221] border-slate-800 max-h-[300px]">
                <SelectItem value="all" className="text-white">Semua Supplier</SelectItem>
                {suppliersList.map((supplier) => (
                  <SelectItem key={supplier} value={supplier} className="text-white text-sm">
                    {supplier.length > 35 ? supplier.substring(0, 35) + "..." : supplier}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div>
              <Label className="text-slate-400 text-xs">Dari</Label>
              <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} disabled={!["management", "vessel", "barge", "trucking", "biomassa"].includes(activeTab)} className="bg-slate-950/50 border-slate-800 text-white disabled:opacity-40" data-testid="laporan-date-from-filter" />
            </div>
            <div>
              <Label className="text-slate-400 text-xs">Sampai</Label>
              <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} disabled={!["management", "vessel", "barge", "trucking", "biomassa"].includes(activeTab)} className="bg-slate-950/50 border-slate-800 text-white disabled:opacity-40" data-testid="laporan-date-to-filter" />
            </div>
            <Button type="button" variant="outline" onClick={resetFilters} className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="laporan-reset-filters">
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>

          {categories.map(cat => (
            <TabsContent key={cat.id} value={cat.id}>
              {cat.id === "management" ? (
                <div className="space-y-4">
                  {loading ? (
                    <div className="py-10">
                      <Loader2 className="w-6 h-6 animate-spin text-purple-400 mx-auto" />
                    </div>
                  ) : !managementReport ? (
                    <div className="text-center py-8 text-slate-500">{dashboardEmptyText(drilldown, "Tidak ada data ditemukan")}</div>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                        <Card className="bg-slate-950/40 border-white/5 p-4">
                          <p className="text-slate-400 text-sm">Monitoring Stock</p>
                          <p className="text-2xl font-bold text-white mt-1">{formatNumber(managementReport.stock.current_stock)} MT</p>
                          <p className="text-slate-500 text-xs mt-1">{managementReport.stock.status} | {managementReport.stock.days_of_supply ?? "-"} hari supply</p>
                        </Card>
                        <Card className="bg-slate-950/40 border-white/5 p-4">
                          <p className="text-slate-400 text-sm">Jadwal vs Realisasi</p>
                          <p className="text-2xl font-bold text-cyan-400 mt-1">{formatNumber(managementReport.arrivals.tonnage_fulfillment_rate, 2)}%</p>
                          <p className="text-slate-500 text-xs mt-1">{formatNumber(managementReport.arrivals.scheduled_tonnage)} MT PO | {formatNumber(managementReport.arrivals.realized_tonnage)} MT realisasi</p>
                        </Card>
                        <Card className="bg-slate-950/40 border-white/5 p-4">
                          <p className="text-slate-400 text-sm">Potential Loss</p>
                          <p className="text-2xl font-bold text-amber-400 mt-1">{formatNumber(managementReport.potential_loss.potential_loss_mt, 2)} MT</p>
                          <p className="text-slate-500 text-xs mt-1">{managementReport.potential_loss.critical_count} critical | {managementReport.potential_loss.warning_count} warning</p>
                        </Card>
                        <Card className="bg-slate-950/40 border-white/5 p-4">
                          <p className="text-slate-400 text-sm">Dispute/Umpire</p>
                          <p className="text-2xl font-bold text-red-400 mt-1">{managementReport.disputes.umpire.active}</p>
                          <p className="text-slate-500 text-xs mt-1">aktif | {managementReport.disputes.stale_count || 0} stale</p>
                        </Card>
                      </div>

                      {(managementReport.data_health?.partial_warnings || []).length > 0 && (
                        <Card className="border-amber-500/30 bg-amber-500/10 p-4">
                          <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-amber-300 mt-0.5" />
                            <div>
                              <p className="text-sm font-semibold text-amber-200">Data parsial pada filter ini</p>
                              <div className="mt-2 space-y-1">
                                {managementReport.data_health.partial_warnings.map((item) => (
                                  <p key={item} className="text-xs text-amber-100/80">{item}</p>
                                ))}
                              </div>
                            </div>
                          </div>
                        </Card>
                      )}

                      {managementReport.trend_analytics && (
                        <div className="rounded-lg border border-white/5 bg-slate-950/40 p-4">
                          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                            <div>
                              <p className="text-slate-300 text-sm font-semibold flex items-center gap-2">
                                <BarChart3 className="w-4 h-4 text-cyan-400" />
                                Trend & Forecast
                              </p>
                              <p className="text-xs text-slate-500 mt-1">
                                {reportTrend.period_comparison?.current?.label || "-"} dibanding {reportTrend.period_comparison?.previous?.label || "-"}
                              </p>
                            </div>
                            <span className={`w-fit rounded border px-2 py-1 text-[10px] font-semibold uppercase ${
                              reportTrend.confidence === "high" ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300" :
                              reportTrend.confidence === "medium" ? "border-amber-500/40 bg-amber-500/10 text-amber-300" :
                              "border-red-500/40 bg-red-500/10 text-red-300"
                            }`}>
                              Confidence: {reportTrend.confidence || "low"}
                            </span>
                          </div>

                          {reportTrend.sparse_data && (
                            <div className="mt-3 rounded border border-amber-500/30 bg-amber-500/10 p-3">
                              {(reportTrend.caveats || []).slice(0, 3).map((item) => (
                                <p key={item} className="text-xs text-amber-100/90">{item}</p>
                              ))}
                            </div>
                          )}

                          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
                            {[
                              reportTrendMetrics.stock,
                              reportTrendMetrics.arrivals,
                              reportTrendMetrics.supplier_performance,
                              reportTrendMetrics.quality_delta,
                              reportTrendMetrics.disputes
                            ].filter(Boolean).map((metric) => (
                              <div key={metric.label} className="rounded-lg border border-white/5 bg-slate-900/60 p-3">
                                <div className="flex items-center justify-between gap-2">
                                  <p className="text-[11px] text-slate-400">{metric.label}</p>
                                  <span className={`flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] ${trendTone(metric)}`}>
                                    <TrendDirectionIcon metric={metric} />
                                    {metric.direction_label}
                                  </span>
                                </div>
                                <p className="mt-2 text-xl font-bold text-white">{formatNumber(metric.current, 2)} {metric.unit}</p>
                                <p className="text-[11px] text-slate-500">Sebelumnya {formatNumber(metric.previous, 2)} | delta {formatNumber(metric.delta, 2)}</p>
                              </div>
                            ))}
                          </div>

                          <div className="mt-4 grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-4">
                            <div className="rounded-lg border border-white/5 bg-slate-900/60 p-3">
                              <p className="text-xs text-slate-400">Forecast stok</p>
                              <p className="mt-1 text-2xl font-bold text-white">{reportForecast.projected_coverage_days ?? "-"} hari</p>
                              <p className="text-[11px] text-slate-500">
                                Burn {formatNumber(reportForecast.avg_daily_usage, 2)} MT/hari | arrivals 30 hari {formatNumber(reportForecast.expected_arrivals_30d, 2)} MT
                              </p>
                              <div className="mt-3 grid grid-cols-3 gap-2">
                                {(reportForecast.horizons || []).map((item) => (
                                  <div key={item.days} className="rounded bg-slate-950/70 p-2">
                                    <p className="text-[10px] text-slate-500">{item.days} hari</p>
                                    <p className="text-sm font-semibold text-white">{formatNumber(item.projected_stock, 0)} MT</p>
                                    <p className="text-[10px] text-slate-500">{item.projected_coverage_days} hari</p>
                                  </div>
                                ))}
                              </div>
                            </div>

                            <div className="rounded-lg border border-white/5 overflow-hidden">
                              <Table>
                                <TableHeader>
                                  <TableRow className="border-white/5 hover:bg-transparent">
                                    <TableHead className="text-slate-400 font-mono text-xs">Supplier</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Risk</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Volume</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">On-time</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Delta COA</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Dispute</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {(reportTrend.supplier_trends || []).slice(0, 5).map((item) => (
                                    <TableRow key={item.supplier} className="border-white/5 hover:bg-slate-900/50">
                                      <TableCell className="text-slate-300 max-w-[220px] whitespace-normal">{item.supplier}</TableCell>
                                      <TableCell>
                                        <span className={`rounded px-2 py-1 text-[10px] uppercase ${
                                          item.risk_status === "high" ? "bg-red-500/20 text-red-300" :
                                          item.risk_status === "medium" ? "bg-amber-500/20 text-amber-300" :
                                          "bg-emerald-500/20 text-emerald-300"
                                        }`}>
                                          {item.risk_label}
                                        </span>
                                      </TableCell>
                                      <TableCell className="text-xs text-slate-300">{formatNumber(item.volume?.delta, 2)} MT</TableCell>
                                      <TableCell className="text-xs text-slate-300">{item.timeliness?.direction_label}</TableCell>
                                      <TableCell className="text-xs text-slate-300">{formatNumber(item.quality_delta?.delta, 2)}</TableCell>
                                      <TableCell className="text-xs text-slate-300">{formatNumber(item.disputes?.delta, 0)}</TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-4">
                        <Card className="bg-slate-950/40 border-white/5 p-4">
                          <p className="text-slate-400 text-sm mb-3">Executive Summary</p>
                          <div className="space-y-2">
                            {(managementReport.executive_summary || []).map((item) => (
                              <p key={item} className="text-sm text-slate-300 leading-relaxed">{item}</p>
                            ))}
                          </div>
                        </Card>
                        <Card className="bg-slate-950/40 border-white/5 p-4">
                          <div className="flex flex-col gap-2 mb-3 sm:flex-row sm:items-start sm:justify-between">
                            <div className="flex items-center gap-2">
                              <Brain className="w-4 h-4 text-cyan-400" />
                              <p className="text-slate-300 text-sm font-semibold">AI Advisor</p>
                            </div>
                            {advisorReport?.confidence && (
                              <span className={`w-fit rounded border px-2 py-1 text-[10px] font-semibold uppercase ${advisorConfidenceTone(advisorConfidence.level)}`}>
                                Confidence {advisorConfidence.level || "low"} / {advisorConfidence.score ?? 0}
                              </span>
                            )}
                          </div>

                          {advisorLimitations.length > 0 && (
                            <div className="mb-3 rounded border border-amber-500/30 bg-amber-500/10 p-3">
                              <p className="text-xs font-semibold text-amber-200">Batasan advisor</p>
                              <div className="mt-2 space-y-1">
                                {advisorLimitations.slice(0, 4).map((item) => (
                                  <p key={item} className="text-[11px] text-amber-100/90">{item}</p>
                                ))}
                              </div>
                            </div>
                          )}

                          <div className="space-y-3 max-h-72 overflow-y-auto">
                            {advisorGroups.length > 0 ? advisorGroups.map((group) => (
                              <div key={group.urgency} className="rounded-lg border border-slate-800 bg-slate-900/60">
                                <div className="flex items-center justify-between gap-2 border-b border-slate-800 px-3 py-2">
                                  <p className="text-xs font-semibold text-slate-300">{group.label}</p>
                                  <span className={`rounded px-2 py-0.5 text-[10px] uppercase ${urgencyTone(group.urgency)}`}>
                                    {group.count} item
                                  </span>
                                </div>
                                <div className="divide-y divide-slate-800">
                                  {(group.items || []).map((item) => (
                                    <div key={item.id} className="p-3">
                                      <div className="flex items-start justify-between gap-2">
                                        <p className="text-sm font-semibold text-white">{item.title}</p>
                                        <span className={`shrink-0 rounded px-2 py-0.5 text-[10px] uppercase ${urgencyTone(item.urgency || item.severity)}`}>
                                          {item.urgency_label || item.severity}
                                        </span>
                                      </div>
                                      <p className="mt-2 text-xs text-slate-300 leading-relaxed">{item.recommendation}</p>
                                      <p className="mt-2 text-[11px] text-slate-400 leading-relaxed">{item.evidence}</p>
                                      <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
                                        <span className="rounded bg-slate-800 px-2 py-1 text-slate-300">Owner: {item.owner_role || "-"}</span>
                                        <span className="rounded bg-slate-800 px-2 py-1 text-slate-300">Source: {item.source_slice}</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )) : (advisorReport?.recommendations || []).map((item) => (
                              <div key={item.id} className="rounded-lg bg-slate-900/70 border border-slate-800 p-3">
                                <div className="flex items-start justify-between gap-2">
                                  <p className="text-sm font-semibold text-white">{item.title}</p>
                                  <span className={`rounded px-2 py-0.5 text-[10px] uppercase ${urgencyTone(item.urgency || item.severity)}`}>
                                    {item.urgency_label || item.severity}
                                  </span>
                                </div>
                                <p className="mt-2 text-xs text-slate-300">{item.recommendation}</p>
                                <p className="mt-2 text-[10px] text-slate-500">Owner: {item.owner_role || "-"} | Source: {item.source_slice}</p>
                              </div>
                            ))}
                          </div>
                          {advisorReport?.guardrails?.fallback_reason && (
                            <p className="mt-3 text-[10px] text-slate-500">{advisorReport.guardrails.fallback_reason}</p>
                          )}
                        </Card>
                      </div>

                      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-4">
                        <div className="rounded-lg border border-white/5 overflow-hidden">
                          <Table>
                            <TableHeader>
                              <TableRow className="border-white/5 hover:bg-transparent">
                                <TableHead className="text-slate-400 font-mono text-xs">Rank</TableHead>
                                <TableHead className="text-slate-400 font-mono text-xs">Supplier</TableHead>
                                <TableHead className="text-slate-400 font-mono text-xs">Risk</TableHead>
                                <TableHead className="text-slate-400 font-mono text-xs">Realisasi MT</TableHead>
                                <TableHead className="text-slate-400 font-mono text-xs">On-time</TableHead>
                                <TableHead className="text-slate-400 font-mono text-xs">Avg Delta</TableHead>
                                <TableHead className="text-slate-400 font-mono text-xs">Dispute</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {(managementReport.supplier_scorecard || []).map((item) => (
                                <TableRow key={item.supplier} className="border-white/5 hover:bg-slate-900/50">
                                  <TableCell className="text-slate-300">{item.rank}</TableCell>
                                  <TableCell className="text-slate-300">{item.supplier}</TableCell>
                                  <TableCell>
                                    <span className={`rounded px-2 py-1 text-[10px] uppercase ${
                                      item.risk_status === "high" ? "bg-red-500/20 text-red-300" :
                                      item.risk_status === "medium" ? "bg-amber-500/20 text-amber-300" :
                                      "bg-emerald-500/20 text-emerald-300"
                                    }`}>
                                      {item.risk_status}
                                    </span>
                                  </TableCell>
                                  <TableCell className="font-mono text-cyan-400">{formatNumber(item.realized_tonnage)}</TableCell>
                                  <TableCell className="font-mono text-green-400">{formatNumber(item.timeliness_rate, 1)}%</TableCell>
                                  <TableCell className="font-mono text-amber-400">{formatNumber(item.avg_coa_delta, 2)}</TableCell>
                                  <TableCell className="font-mono text-red-400">{item.active_disputes}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                        <Card className="bg-slate-950/40 border-white/5 p-4">
                          <p className="text-slate-400 text-sm mb-3">Traceability</p>
                          <div className="space-y-2">
                            {Object.entries(managementReport.source_counts || {}).map(([source, count]) => (
                              <div key={source} className="flex items-center justify-between text-sm">
                                <span className="text-slate-300">{source}</span>
                                <span className="font-mono text-white">{count}</span>
                              </div>
                            ))}
                          </div>
                          <div className="mt-4 border-t border-slate-800 pt-3 space-y-2">
                            {(managementReport.source_slices || []).map((slice) => (
                              <div key={slice.name} className="text-xs">
                                <div className="flex items-center justify-between gap-2">
                                  <span className="text-slate-300">{slice.name}</span>
                                  <span className="font-mono text-cyan-300">{slice.record_count}</span>
                                </div>
                                <p className="text-[10px] text-slate-500 truncate">{(slice.collections || []).join(", ")}</p>
                              </div>
                            ))}
                          </div>
                          <p className="text-slate-500 text-xs mt-4">Generated: {formatDateForExport(managementReport.generated_at)}</p>
                        </Card>
                      </div>

                      <Card className="bg-slate-950/40 border-white/5 p-4">
                        <p className="text-slate-400 text-sm mb-3">Draft Memo Manajemen</p>
                        <pre className="whitespace-pre-wrap text-sm text-slate-300 font-sans leading-relaxed">{advisorReport?.memo_draft || "Memo belum tersedia."}</pre>
                      </Card>
                    </>
                  )}
                </div>
              ) : (
              <>
              <div className="rounded-lg border border-white/5 overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/5 hover:bg-transparent">
                      <TableHead className="text-slate-400 font-mono text-xs w-[50px]">No</TableHead>
                      {columns.map(col => (
                        <TableHead key={col.key} className="text-slate-400 font-mono text-xs">{col.label}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={columns.length + 1} className="text-center py-8">
                          <Loader2 className="w-6 h-6 animate-spin text-purple-400 mx-auto" />
                        </TableCell>
                      </TableRow>
                    ) : data.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={columns.length + 1} className="text-center py-8 text-slate-500">
                          {dashboardEmptyText(drilldown, "Tidak ada data ditemukan")}
                        </TableCell>
                      </TableRow>
                    ) : (
                      data.map((item, index) => (
                        <TableRow key={item.id} className="border-white/5 hover:bg-slate-900/50" data-testid={`laporan-row-${item.id}`}>
                          <TableCell className="text-slate-500 text-sm">{(pagination.page - 1) * PAGE_SIZE + index + 1}</TableCell>
                          {columns.map(col => (
                            <TableCell key={col.key} className={`text-sm ${col.type === 'number' ? 'font-mono text-cyan-400' : 'text-slate-300'}`}>
                              {formatValue(item[col.key], col.type)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
              
              {/* Pagination Controls */}
              {pagination.totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 px-2">
                  <p className="text-sm text-slate-400">
                    Menampilkan {(pagination.page - 1) * PAGE_SIZE + 1} - {Math.min(pagination.page * PAGE_SIZE, pagination.total)} dari {pagination.total} data
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchData(pagination.page - 1)}
                      disabled={pagination.page <= 1 || loading}
                      className="border-slate-700 text-slate-300"
                    >
                      Sebelumnya
                    </Button>
                    <span className="text-sm text-slate-400 px-2">
                      Halaman {pagination.page} dari {pagination.totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchData(pagination.page + 1)}
                      disabled={pagination.page >= pagination.totalPages || loading}
                      className="border-slate-700 text-slate-300"
                    >
                      Selanjutnya
                    </Button>
                  </div>
                </div>
              )}
              </>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </Card>
    </div>
  );
};

export default LaporanPage;
