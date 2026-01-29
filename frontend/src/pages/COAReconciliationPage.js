import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Pagination from "@/components/Pagination";
import {
  AlertTriangle,
  TrendingDown,
  Scale,
  Search,
  Upload,
  Loader2,
  RefreshCw,
  FileWarning,
  DollarSign,
  AlertCircle,
  BarChart3,
  Eye,
  Gavel,
  CheckCircle,
  XCircle,
  Clock,
  ChevronDown,
  Plus,
  Trash2,
  FileSpreadsheet,
  ArrowRight
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const COAReconciliationPage = () => {
  const { getAuthHeader, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [data, setData] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [supplierData, setSupplierData] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [radarData, setRadarData] = useState([]);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showUmpireDialog, setShowUmpireDialog] = useState(false);
  const [umpireForm, setUmpireForm] = useState({ sample_number: "", notes: "" });
  const [showManualDialog, setShowManualDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [fileMapping, setFileMapping] = useState({
    loading: "",
    unloading: "",
    internal: ""
  });
  const [manualForm, setManualForm] = useState({
    shipment: "",
    suppliers: "",
    periode: "",
    completed_unloading: "",
    tb: "",
    bg: "",
    ds_mt: "",
    loading_gcv_arb: "",
    loading_tm_arb: "",
    loading_ash_arb: "",
    loading_ts_arb: "",
    unloading_gcv_arb: "",
    unloading_tm_arb: "",
    unloading_ash_arb: "",
    unloading_ts_arb: "",
    internal_gcv_arb: "",
    internal_tm_arb: "",
    internal_ash_arb: "",
    internal_ts_arb: ""
  });
  const PAGE_SIZE = 50;

  const fetchData = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = { page, page_size: PAGE_SIZE };
      if (search) params.search = search;
      if (statusFilter !== "all") params.status = statusFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const response = await axios.get(`${API_URL}/api/coa-reconciliation`, {
        headers: getAuthHeader(),
        params
      });

      if (response.data.items) {
        setData(response.data.items);
        setPagination({
          page: response.data.page,
          total: response.data.total,
          totalPages: response.data.total_pages
        });
      }
    } catch (error) {
      toast.error("Gagal memuat data rekonsiliasi");
    } finally {
      setLoading(false));
    }
  }, [getAuthHeader, search, statusFilter]);

  const fetchKPIs = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/coa-reconciliation/kpis`, {
        headers: getAuthHeader()
      });
      setKpis(response.data);
    } catch (error) {
      console.error("Failed to fetch KPIs:", error);
    }
  }, [getAuthHeader]);

  const fetchTrendData = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/coa-reconciliation/trend`, {
        headers: getAuthHeader(),
        params: { months: 6 }
      });
      setTrendData(response.data);
    } catch (error) {
      console.error("Failed to fetch trend data:", error);
    }
  }, [getAuthHeader]);

  const fetchSupplierData = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/coa-reconciliation/supplier-consistency`, {
        headers: getAuthHeader()
      });
      setSupplierData(response.data.slice(0, 10));
    } catch (error) {
      console.error("Failed to fetch supplier data:", error);
    }
  }, [getAuthHeader]);

  useEffect(() => {
    fetchData(1);
    fetchKPIs();
    fetchTrendData();
    fetchSupplierData();
  }, []);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchData(1);
    }, 500);
    return () => clearTimeout(debounceTimer);
  }, [search, statusFilter, dateFrom, dateTo, fetchData]);

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length !== 3) {
      toast.error("Harap upload tepat 3 file Excel");
      e.target.value = "";
      return;
    }

    // Check all files are Excel
    const validExtensions = ['.xlsx', '.xls'];
    const invalidFiles = files.filter(f => !validExtensions.some(ext => f.name.toLowerCase().endsWith(ext)));
    if (invalidFiles.length > 0) {
      toast.error("Semua file harus berformat Excel (.xlsx atau .xls)");
      e.target.value = "";
      return;
    }

    // Store files and show mapping dialog
    setUploadedFiles(files);
    
    // Try auto-detect based on filename
    const newMapping = { loading: "", unloading: "", internal: "" };
    files.forEach((file, index) => {
      const name = file.name.toLowerCase();
      if (name.includes("loading") && !newMapping.loading) {
        newMapping.loading = index.toString();
      } else if (name.includes("unloading") && !newMapping.unloading) {
        newMapping.unloading = index.toString();
      } else if ((name.includes("internal") || name.includes("lab")) && !newMapping.internal) {
        newMapping.internal = index.toString();
      }
    });
    
    setFileMapping(newMapping);
    setShowUploadDialog(true);
    e.target.value = "";
  };

  const processUploadedFiles = async () => {
    // Validate all mappings are set and unique
    if (!fileMapping.loading || !fileMapping.unloading || !fileMapping.internal) {
      toast.error("Harap petakan semua file ke kategori yang sesuai");
      return;
    }

    const mappingValues = [fileMapping.loading, fileMapping.unloading, fileMapping.internal];
    if (new Set(mappingValues).size !== 3) {
      toast.error("Setiap file harus dipetakan ke kategori berbeda");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("loading_file", uploadedFiles[parseInt(fileMapping.loading)]);
    formData.append("unloading_file", uploadedFiles[parseInt(fileMapping.unloading)]);
    formData.append("internal_file", uploadedFiles[parseInt(fileMapping.internal)]);

    try {
      const response = await axios.post(
        `${API_URL}/api/coa-reconciliation/upload`,
        formData,
        {
          headers: {
            ...getAuthHeader(),
            "Content-Type": "multipart/form-data",
          },
        }
      );
      toast.success(response.data.message);
      setShowUploadDialog(false);
      setUploadedFiles([]);
      setFileMapping({ loading: "", unloading: "", internal: "" });
      fetchData(1);
      fetchKPIs();
      fetchTrendData();
      fetchSupplierData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal upload file");
    } finally {
      setUploading(false);
    }
  };

  const handleViewDetail = async (record) => {
    try {
      const response = await axios.get(`${API_URL}/api/coa-reconciliation/${record.id}`, {
        headers: getAuthHeader()
      });
      setSelectedRecord(response.data.record);
      setRadarData(response.data.radar_chart);
      setShowDetailDialog(true);
    } catch (error) {
      toast.error("Gagal memuat detail");
    }
  };

  const handleProposeUmpire = (record) => {
    setSelectedRecord(record);
    setUmpireForm({ sample_number: "", notes: "" });
    setShowUmpireDialog(true);
  };

  const submitUmpireProposal = async () => {
    if (!umpireForm.sample_number) {
      toast.error("Nomor sampel wajib diisi");
      return;
    }

    try {
      await axios.post(
        `${API_URL}/api/coa-reconciliation/propose-umpire`,
        {
          reconciliation_id: selectedRecord.id,
          sample_number: umpireForm.sample_number,
          notes: umpireForm.notes
        },
        { headers: getAuthHeader() }
      );
      toast.success("Pengajuan Umpire berhasil disimpan");
      setShowUmpireDialog(false);
      fetchData(pagination.page);
      fetchKPIs();
    } catch (error) {
      toast.error("Gagal mengajukan Umpire");
    }
  };

  const resetManualForm = () => {
    setManualForm({
      shipment: "",
      suppliers: "",
      periode: "",
      completed_unloading: "",
      tb: "",
      bg: "",
      ds_mt: "",
      loading_gcv_arb: "",
      loading_tm_arb: "",
      loading_ash_arb: "",
      loading_ts_arb: "",
      unloading_gcv_arb: "",
      unloading_tm_arb: "",
      unloading_ash_arb: "",
      unloading_ts_arb: "",
      internal_gcv_arb: "",
      internal_tm_arb: "",
      internal_ash_arb: "",
      internal_ts_arb: ""
    });
  };

  const submitManualInput = async () => {
    if (!manualForm.shipment || !manualForm.suppliers) {
      toast.error("Shipment dan Supplier wajib diisi");
      return;
    }

    try {
      const payload = {
        shipment: manualForm.shipment,  // Now string, supports "Lot XX"
        suppliers: manualForm.suppliers,
        periode: manualForm.periode || null,
        completed_unloading: manualForm.completed_unloading || null,
        tb: manualForm.tb || null,
        bg: manualForm.bg || null,
        ds_mt: manualForm.ds_mt ? parseFloat(manualForm.ds_mt) : null,
        loading_gcv_arb: manualForm.loading_gcv_arb ? parseFloat(manualForm.loading_gcv_arb) : null,
        loading_tm_arb: manualForm.loading_tm_arb ? parseFloat(manualForm.loading_tm_arb) : null,
        loading_ash_arb: manualForm.loading_ash_arb ? parseFloat(manualForm.loading_ash_arb) : null,
        loading_ts_arb: manualForm.loading_ts_arb ? parseFloat(manualForm.loading_ts_arb) : null,
        unloading_gcv_arb: manualForm.unloading_gcv_arb ? parseFloat(manualForm.unloading_gcv_arb) : null,
        unloading_tm_arb: manualForm.unloading_tm_arb ? parseFloat(manualForm.unloading_tm_arb) : null,
        unloading_ash_arb: manualForm.unloading_ash_arb ? parseFloat(manualForm.unloading_ash_arb) : null,
        unloading_ts_arb: manualForm.unloading_ts_arb ? parseFloat(manualForm.unloading_ts_arb) : null,
        internal_gcv_arb: manualForm.internal_gcv_arb ? parseFloat(manualForm.internal_gcv_arb) : null,
        internal_tm_arb: manualForm.internal_tm_arb ? parseFloat(manualForm.internal_tm_arb) : null,
        internal_ash_arb: manualForm.internal_ash_arb ? parseFloat(manualForm.internal_ash_arb) : null,
        internal_ts_arb: manualForm.internal_ts_arb ? parseFloat(manualForm.internal_ts_arb) : null
      };

      await axios.post(`${API_URL}/api/coa-reconciliation/manual`, payload, {
        headers: getAuthHeader()
      });
      toast.success(`Berhasil menambahkan data COA Shipment ${manualForm.shipment}`);
      setShowManualDialog(false);
      resetManualForm();
      fetchData(1);
      fetchKPIs();
      fetchTrendData();
      fetchSupplierData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menambahkan data");
    }
  };

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      const response = await axios.delete(`${API_URL}/api/coa-reconciliation`, {
        headers: getAuthHeader()
      });
      toast.success(response.data.message);
      setShowDeleteDialog(false);
      fetchData(1);
      fetchKPIs();
      fetchTrendData();
      fetchSupplierData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menghapus data");
    } finally {
      setDeleting(false);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      critical: "bg-red-500/20 text-red-400 border-red-500/30",
      warning: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      normal: "bg-green-500/20 text-green-400 border-green-500/30"
    };
    const labels = { critical: "Kritis", warning: "Peringatan", normal: "Normal" };
    return (
      <Badge className={`${styles[status]} border`}>
        {labels[status] || status}
      </Badge>
    );
  };

  const getUmpireStatusBadge = (status) => {
    const config = {
      none: { icon: XCircle, color: "text-slate-500", label: "Belum Ada" },
      proposed: { icon: Clock, color: "text-yellow-400", label: "Diajukan" },
      in_progress: { icon: Scale, color: "text-blue-400", label: "Proses" },
      completed: { icon: CheckCircle, color: "text-green-400", label: "Selesai" }
    };
    const cfg = config[status] || config.none;
    const Icon = cfg.icon;
    return (
      <span className={`flex items-center gap-1 ${cfg.color} text-xs`}>
        <Icon className="w-3 h-3" />
        {cfg.label}
      </span>
    );
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return "-";
    return num.toLocaleString("id-ID");
  };

  const formatCurrency = (num) => {
    if (num === null || num === undefined) return "-";
    if (num >= 1000000000) return `Rp ${(num / 1000000000).toFixed(1)}M`;
    if (num >= 1000000) return `Rp ${(num / 1000000).toFixed(1)}jt`;
    return `Rp ${num.toLocaleString("id-ID")}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Scale className="w-7 h-7 text-amber-400" />
            COA Reconciliation & Dispute Monitor
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Rekonsiliasi data kualitas batubara dari Loading, Unloading, dan Lab Internal
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={() => { fetchData(1); fetchKPIs(); fetchTrendData(); fetchSupplierData(); }}
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            onClick={() => { resetManualForm(); setShowManualDialog(true); }}
            className="bg-cyan-600 hover:bg-cyan-700"
            data-testid="manual-input-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            Input Manual
          </Button>
          <label className="cursor-pointer">
            <input
              type="file"
              multiple
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              className="hidden"
              data-testid="upload-input"
            />
            <Button
              asChild
              className="bg-amber-600 hover:bg-amber-700"
              disabled={uploading}
            >
              <span>
                {uploading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4 mr-2" />
                )}
                Upload 3 File COA
              </span>
            </Button>
          </label>
          {user?.role === "admin" && (
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(true)}
              className="border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300"
              data-testid="delete-all-btn"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Hapus Semua
            </Button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-[#0B1221] border-red-500/20 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">High Deviation Alert</p>
                <p className="text-3xl font-bold text-red-400 mt-1">{kpis.high_deviation_count}</p>
                <p className="text-xs text-slate-500 mt-1">Lot dengan selisih GCV &gt; 100 kCal/kg</p>
              </div>
              <div className="p-2 bg-red-500/10 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
            </div>
          </Card>

          <Card className="bg-[#0B1221] border-amber-500/20 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Potential Loss</p>
                <p className="text-3xl font-bold text-amber-400 mt-1">{formatCurrency(kpis.potential_loss_rp)}</p>
                <p className="text-xs text-slate-500 mt-1">{formatNumber(kpis.total_tonnage_problem)} MT bermasalah</p>
              </div>
              <div className="p-2 bg-amber-500/10 rounded-lg">
                <DollarSign className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </Card>

          <Card className="bg-[#0B1221] border-blue-500/20 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Umpire Status</p>
                <p className="text-3xl font-bold text-blue-400 mt-1">{kpis.umpire_status?.total || 0}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {kpis.umpire_status?.proposed || 0} diajukan, {kpis.umpire_status?.in_progress || 0} proses
                </p>
              </div>
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Gavel className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </Card>

          <Card className="bg-[#0B1221] border-green-500/20 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Rata-rata Akurasi</p>
                <p className="text-3xl font-bold text-green-400 mt-1">{kpis.avg_accuracy}%</p>
                <p className="text-xs text-slate-500 mt-1">
                  {kpis.normal_count} normal, {kpis.warning_count} warning
                </p>
              </div>
              <div className="p-2 bg-green-500/10 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-400" />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Insight Card */}
      {kpis?.worst_supplier && (
        <Card className="bg-gradient-to-r from-red-500/10 to-amber-500/10 border-red-500/20 p-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div>
              <p className="text-sm text-white font-medium">
                Supplier dengan Deviasi Tertinggi: <span className="text-amber-400">{kpis.worst_supplier.supplier}</span>
              </p>
              <p className="text-xs text-slate-400">
                Rata-rata deviasi {kpis.worst_supplier.avg_deviation} kCal/kg dari {kpis.worst_supplier.count} shipment
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GCV Trend Chart */}
        <Card className="bg-[#0B1221] border-white/5 p-4">
          <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-cyan-400" />
            Tren GCV - Triple Comparison
          </h3>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="periode" tick={{ fill: "#64748b", fontSize: 10 }} />
                <YAxis domain={['auto', 'auto']} tick={{ fill: "#64748b", fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0B1221", border: "1px solid #1e293b" }}
                  labelStyle={{ color: "#fff" }}
                />
                <Legend />
                <Line type="monotone" dataKey="loading" stroke="#22c55e" name="Loading" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="unloading" stroke="#3b82f6" name="Unloading" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="internal" stroke="#f59e0b" name="Internal" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-slate-500">
              Tidak ada data trend
            </div>
          )}
        </Card>

        {/* Supplier Consistency Chart */}
        <Card className="bg-[#0B1221] border-white/5 p-4">
          <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-amber-400" />
            Supplier dengan Deviasi Tertinggi
          </h3>
          {supplierData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={supplierData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" tick={{ fill: "#64748b", fontSize: 10 }} />
                <YAxis dataKey="supplier" type="category" width={100} tick={{ fill: "#64748b", fontSize: 9 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0B1221", border: "1px solid #1e293b" }}
                  labelStyle={{ color: "#fff" }}
                  formatter={(value) => [`${value} kCal/kg`, "Avg Deviasi"]}
                />
                <Bar dataKey="avg_deviation" fill="#f59e0b" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-slate-500">
              Tidak ada data supplier
            </div>
          )}
        </Card>
      </div>

      {/* Filter & Search */}
      <Card className="bg-[#0B1221] border-white/5 p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-500" />
            <Input
              placeholder="Cari shipment atau supplier..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-slate-900/50 border-slate-700 text-white"
              data-testid="search-input"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-500">Tanggal:</span>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-[140px] bg-slate-900/50 border-slate-700 text-white text-sm"
              data-testid="date-from"
            />
            <span className="text-slate-500">-</span>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-[140px] bg-slate-900/50 border-slate-700 text-white text-sm"
              data-testid="date-to"
            />
            {(dateFrom || dateTo) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => { setDateFrom(""); setDateTo(""); }}
                className="text-slate-400 hover:text-white h-8 px-2"
              >
                <XCircle className="w-4 h-4" />
              </Button>
            )}
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px] bg-slate-900/50 border-slate-700 text-white" data-testid="status-filter">
              <SelectValue placeholder="Filter Status" />
            </SelectTrigger>
            <SelectContent className="bg-[#0B1221] border-slate-700">
              <SelectItem value="all">Semua Status</SelectItem>
              <SelectItem value="critical">Kritis</SelectItem>
              <SelectItem value="warning">Peringatan</SelectItem>
              <SelectItem value="normal">Normal</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Triple Check Table */}
      <Card className="bg-[#0B1221] border-white/5 overflow-hidden">
        <div className="p-4 border-b border-white/5">
          <h3 className="text-sm font-medium text-white">
            Tabel Perbandingan "Triple Check" ({pagination.total} data)
          </h3>
        </div>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400 text-xs">Shipment</TableHead>
                <TableHead className="text-slate-400 text-xs">Supplier</TableHead>
                <TableHead className="text-slate-400 text-xs text-center bg-green-500/10">Loading GCV</TableHead>
                <TableHead className="text-slate-400 text-xs text-center bg-blue-500/10">Unloading GCV</TableHead>
                <TableHead className="text-slate-400 text-xs text-center bg-amber-500/10">Internal GCV</TableHead>
                <TableHead className="text-slate-400 text-xs text-center">Delta (L-I)</TableHead>
                <TableHead className="text-slate-400 text-xs text-center">Status</TableHead>
                <TableHead className="text-slate-400 text-xs text-center">Umpire</TableHead>
                <TableHead className="text-slate-400 text-xs text-center">Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-cyan-400" />
                  </TableCell>
                </TableRow>
              ) : data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-slate-500">
                    Tidak ada data. Upload file COA untuk memulai.
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row) => {
                  const isCritical = row.delta_loading_internal && Math.abs(row.delta_loading_internal) > 150;
                  return (
                    <TableRow
                      key={row.id}
                      className={`border-white/5 ${isCritical ? "bg-red-500/10 hover:bg-red-500/15" : "hover:bg-white/5"}`}
                      data-testid={`row-${row.shipment}`}
                    >
                      <TableCell className="font-mono text-white text-sm">{row.shipment}</TableCell>
                      <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{row.suppliers}</TableCell>
                      <TableCell className="text-center text-green-400 text-sm font-medium bg-green-500/5">
                        {row.loading_gcv_arb ? formatNumber(row.loading_gcv_arb) : "-"}
                      </TableCell>
                      <TableCell className="text-center text-blue-400 text-sm font-medium bg-blue-500/5">
                        {row.unloading_gcv_arb ? formatNumber(row.unloading_gcv_arb) : "-"}
                      </TableCell>
                      <TableCell className="text-center text-amber-400 text-sm font-medium bg-amber-500/5">
                        {row.internal_gcv_arb ? formatNumber(row.internal_gcv_arb) : "-"}
                      </TableCell>
                      <TableCell className={`text-center font-bold text-sm ${
                        row.delta_loading_internal > 150 ? "text-red-400" :
                        row.delta_loading_internal > 100 ? "text-yellow-400" :
                        row.delta_loading_internal !== null ? "text-green-400" : "text-slate-500"
                      }`}>
                        {row.delta_loading_internal !== null ? (
                          <>
                            {row.delta_loading_internal > 0 ? "+" : ""}{Math.round(row.delta_loading_internal)}
                          </>
                        ) : "-"}
                      </TableCell>
                      <TableCell className="text-center">{getStatusBadge(row.status)}</TableCell>
                      <TableCell className="text-center">{getUmpireStatusBadge(row.umpire_status)}</TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(row)}
                            className="h-7 px-2 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10"
                            data-testid={`view-${row.shipment}`}
                          >
                            <Eye className="w-3 h-3" />
                          </Button>
                          {(row.status === "critical" || row.status === "warning") && row.umpire_status === "none" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleProposeUmpire(row)}
                              className="h-7 px-2 text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                              data-testid={`umpire-${row.shipment}`}
                            >
                              <Gavel className="w-3 h-3" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
        {pagination.totalPages > 1 && (
          <div className="p-4 border-t border-white/5">
            <Pagination
              currentPage={pagination.page}
              totalPages={pagination.totalPages}
              onPageChange={(page) => fetchData(page)}
            />
          </div>
        )}
      </Card>

      {/* Detail Dialog with Radar Chart */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="bg-[#0B1221] border-white/10 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>Detail Shipment #{selectedRecord?.shipment}</DialogTitle>
            <DialogDescription className="text-slate-400">
              Perbandingan profil kualitas dari 3 sumber pengujian
            </DialogDescription>
          </DialogHeader>
          {selectedRecord && (
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500">Supplier</p>
                  <p className="text-white font-medium">{selectedRecord.suppliers || "-"}</p>
                </div>
                <div>
                  <p className="text-slate-500">Tonase (DS MT)</p>
                  <p className="text-white font-medium">{formatNumber(selectedRecord.ds_mt)} MT</p>
                </div>
              </div>

              {/* Radar Chart */}
              <div className="bg-slate-900/50 rounded-lg p-4">
                <h4 className="text-sm font-medium mb-4">Grafik Radar - Profil Kualitas</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="parameter" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 9 }} />
                    <Radar name="Loading" dataKey="loading" stroke="#22c55e" fill="#22c55e" fillOpacity={0.3} />
                    <Radar name="Unloading" dataKey="unloading" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                    <Radar name="Internal" dataKey="internal" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
                    <Legend />
                    <Tooltip contentStyle={{ backgroundColor: "#0B1221", border: "1px solid #1e293b" }} />
                  </RadarChart>
                </ResponsiveContainer>
                <p className="text-xs text-slate-500 text-center mt-2">
                  Grafik tidak berhimpit menunjukkan adanya anomali antar sumber data
                </p>
              </div>

              {/* Detailed Values */}
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="bg-green-500/10 rounded-lg p-3">
                  <p className="text-green-400 font-medium text-xs mb-2">Loading</p>
                  <p>GCV: {formatNumber(selectedRecord.loading_gcv_arb)}</p>
                  <p>TM: {selectedRecord.loading_tm_arb || "-"}%</p>
                  <p>Ash: {selectedRecord.loading_ash_arb || "-"}%</p>
                  <p>S: {selectedRecord.loading_ts_arb || "-"}%</p>
                </div>
                <div className="bg-blue-500/10 rounded-lg p-3">
                  <p className="text-blue-400 font-medium text-xs mb-2">Unloading</p>
                  <p>GCV: {formatNumber(selectedRecord.unloading_gcv_arb)}</p>
                  <p>TM: {selectedRecord.unloading_tm_arb || "-"}%</p>
                  <p>Ash: {selectedRecord.unloading_ash_arb || "-"}%</p>
                  <p>S: {selectedRecord.unloading_ts_arb || "-"}%</p>
                </div>
                <div className="bg-amber-500/10 rounded-lg p-3">
                  <p className="text-amber-400 font-medium text-xs mb-2">Internal</p>
                  <p>GCV: {formatNumber(selectedRecord.internal_gcv_arb)}</p>
                  <p>TM: {selectedRecord.internal_tm_arb || "-"}%</p>
                  <p>Ash: {selectedRecord.internal_ash_arb || "-"}%</p>
                  <p>S: {selectedRecord.internal_ts_arb || "-"}%</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Umpire Proposal Dialog */}
      <Dialog open={showUmpireDialog} onOpenChange={setShowUmpireDialog}>
        <DialogContent className="bg-[#0B1221] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Gavel className="w-5 h-5 text-amber-400" />
              Ajukan Pengujian Umpire
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Shipment #{selectedRecord?.shipment} - {selectedRecord?.suppliers}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-amber-500/10 rounded-lg p-3 text-sm">
              <p className="text-amber-400 font-medium">Delta GCV: {Math.round(selectedRecord?.delta_loading_internal || 0)} kCal/kg</p>
              <p className="text-slate-400 text-xs mt-1">
                Selisih melebihi toleransi. Pengujian pihak ketiga (Umpire) direkomendasikan.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Nomor Sampel Umpire *</Label>
              <Input
                value={umpireForm.sample_number}
                onChange={(e) => setUmpireForm({ ...umpireForm, sample_number: e.target.value })}
                placeholder="Masukkan nomor sampel"
                className="bg-slate-900/50 border-slate-700"
                data-testid="umpire-sample-input"
              />
            </div>
            <div className="space-y-2">
              <Label>Catatan (Opsional)</Label>
              <Textarea
                value={umpireForm.notes}
                onChange={(e) => setUmpireForm({ ...umpireForm, notes: e.target.value })}
                placeholder="Catatan tambahan..."
                className="bg-slate-900/50 border-slate-700"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowUmpireDialog(false)}>Batal</Button>
            <Button onClick={submitUmpireProposal} className="bg-amber-600 hover:bg-amber-700" data-testid="submit-umpire">
              <Gavel className="w-4 h-4 mr-2" />
              Ajukan Umpire
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manual Input Dialog */}
      <Dialog open={showManualDialog} onOpenChange={setShowManualDialog}>
        <DialogContent className="bg-[#0B1221] border-white/10 text-white max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-cyan-400" />
              Input Data COA Manual
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Masukkan data kualitas batubara dari Loading, Unloading, dan Lab Internal
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-white border-b border-white/10 pb-2">Informasi Dasar</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nomor Shipment *</Label>
                  <Input
                    type="number"
                    value={manualForm.shipment}
                    onChange={(e) => setManualForm({ ...manualForm, shipment: e.target.value })}
                    placeholder="Contoh: 1145"
                    className="bg-slate-900/50 border-slate-700"
                    data-testid="manual-shipment"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Supplier *</Label>
                  <Input
                    value={manualForm.suppliers}
                    onChange={(e) => setManualForm({ ...manualForm, suppliers: e.target.value })}
                    placeholder="Contoh: PT BA"
                    className="bg-slate-900/50 border-slate-700"
                    data-testid="manual-supplier"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Periode</Label>
                  <Input
                    type="date"
                    value={manualForm.periode}
                    onChange={(e) => setManualForm({ ...manualForm, periode: e.target.value })}
                    className="bg-slate-900/50 border-slate-700"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tonase (DS MT)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.ds_mt}
                    onChange={(e) => setManualForm({ ...manualForm, ds_mt: e.target.value })}
                    placeholder="Contoh: 5000"
                    className="bg-slate-900/50 border-slate-700"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tongkang (TB)</Label>
                  <Input
                    value={manualForm.tb}
                    onChange={(e) => setManualForm({ ...manualForm, tb: e.target.value })}
                    placeholder="Nama Tongkang"
                    className="bg-slate-900/50 border-slate-700"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Barge (BG)</Label>
                  <Input
                    value={manualForm.bg}
                    onChange={(e) => setManualForm({ ...manualForm, bg: e.target.value })}
                    placeholder="Nama Barge"
                    className="bg-slate-900/50 border-slate-700"
                  />
                </div>
              </div>
            </div>

            {/* Loading Data */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-green-400 border-b border-green-500/20 pb-2">Data Loading (Surveyor Loading)</h4>
              <div className="grid grid-cols-4 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs">GCV ARB (kCal/kg)</Label>
                  <Input
                    type="number"
                    value={manualForm.loading_gcv_arb}
                    onChange={(e) => setManualForm({ ...manualForm, loading_gcv_arb: e.target.value })}
                    placeholder="4500"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                    data-testid="manual-loading-gcv"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">TM ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.loading_tm_arb}
                    onChange={(e) => setManualForm({ ...manualForm, loading_tm_arb: e.target.value })}
                    placeholder="30"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Ash ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.loading_ash_arb}
                    onChange={(e) => setManualForm({ ...manualForm, loading_ash_arb: e.target.value })}
                    placeholder="5"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Sulphur ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.loading_ts_arb}
                    onChange={(e) => setManualForm({ ...manualForm, loading_ts_arb: e.target.value })}
                    placeholder="0.5"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Unloading Data */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-blue-400 border-b border-blue-500/20 pb-2">Data Unloading (Surveyor Unloading)</h4>
              <div className="grid grid-cols-4 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs">GCV ARB (kCal/kg)</Label>
                  <Input
                    type="number"
                    value={manualForm.unloading_gcv_arb}
                    onChange={(e) => setManualForm({ ...manualForm, unloading_gcv_arb: e.target.value })}
                    placeholder="4400"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                    data-testid="manual-unloading-gcv"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">TM ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.unloading_tm_arb}
                    onChange={(e) => setManualForm({ ...manualForm, unloading_tm_arb: e.target.value })}
                    placeholder="32"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Ash ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.unloading_ash_arb}
                    onChange={(e) => setManualForm({ ...manualForm, unloading_ash_arb: e.target.value })}
                    placeholder="4.5"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Sulphur ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.unloading_ts_arb}
                    onChange={(e) => setManualForm({ ...manualForm, unloading_ts_arb: e.target.value })}
                    placeholder="0.4"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Internal Lab Data */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-amber-400 border-b border-amber-500/20 pb-2">Data Lab Internal</h4>
              <div className="grid grid-cols-4 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs">GCV ARB (kCal/kg)</Label>
                  <Input
                    type="number"
                    value={manualForm.internal_gcv_arb}
                    onChange={(e) => setManualForm({ ...manualForm, internal_gcv_arb: e.target.value })}
                    placeholder="4350"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                    data-testid="manual-internal-gcv"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">TM ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.internal_tm_arb}
                    onChange={(e) => setManualForm({ ...manualForm, internal_tm_arb: e.target.value })}
                    placeholder="33"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Ash ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.internal_ash_arb}
                    onChange={(e) => setManualForm({ ...manualForm, internal_ash_arb: e.target.value })}
                    placeholder="4.8"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Sulphur ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={manualForm.internal_ts_arb}
                    onChange={(e) => setManualForm({ ...manualForm, internal_ts_arb: e.target.value })}
                    placeholder="0.45"
                    className="bg-slate-900/50 border-slate-700 text-sm"
                  />
                </div>
              </div>
            </div>
          </div>
          <DialogFooter className="mt-6">
            <Button variant="ghost" onClick={() => setShowManualDialog(false)}>Batal</Button>
            <Button onClick={submitManualInput} className="bg-cyan-600 hover:bg-cyan-700" data-testid="submit-manual">
              <Plus className="w-4 h-4 mr-2" />
              Simpan Data
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete All Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="bg-[#0B1221] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-400">
              <Trash2 className="w-5 h-5" />
              Hapus Semua Data COA
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Tindakan ini akan menghapus semua data rekonsiliasi COA dan tidak dapat dibatalkan.
            </DialogDescription>
          </DialogHeader>
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            <p className="text-red-300 text-sm">
              <AlertTriangle className="w-4 h-4 inline mr-2" />
              Peringatan: Anda akan menghapus <strong>{pagination.total}</strong> data rekonsiliasi COA.
            </p>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowDeleteDialog(false)} disabled={deleting}>Batal</Button>
            <Button 
              onClick={handleDeleteAll} 
              className="bg-red-600 hover:bg-red-700"
              disabled={deleting}
              data-testid="confirm-delete"
            >
              {deleting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Ya, Hapus Semua
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload File Mapping Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={(open) => {
        if (!open && !uploading) {
          setShowUploadDialog(false);
          setUploadedFiles([]);
          setFileMapping({ loading: "", unloading: "", internal: "" });
        }
      }}>
        <DialogContent className="bg-[#0B1221] border-white/10 text-white max-w-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-amber-400" />
              Petakan File COA
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Cocokkan setiap file dengan kategori sumber data yang sesuai
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* File List */}
            <div className="bg-slate-900/50 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-2">File yang diupload:</p>
              <div className="space-y-1">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm text-slate-300">
                    <FileSpreadsheet className="w-4 h-4 text-green-400" />
                    <span className="font-mono">{file.name}</span>
                    <span className="text-slate-500 text-xs">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Mapping Section */}
            <div className="space-y-3">
              <p className="text-sm text-white font-medium">Petakan ke kategori:</p>
              
              {/* Loading */}
              <div className="flex items-center gap-3">
                <div className="w-32 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-sm text-green-400 font-medium">Loading</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <Select value={fileMapping.loading} onValueChange={(val) => setFileMapping({ ...fileMapping, loading: val })}>
                  <SelectTrigger className="flex-1 bg-slate-900/50 border-slate-700 text-white" data-testid="map-loading">
                    <SelectValue placeholder="Pilih file Loading..." />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0B1221] border-slate-700">
                    {uploadedFiles.map((file, index) => (
                      <SelectItem key={index} value={index.toString()}>
                        {file.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Unloading */}
              <div className="flex items-center gap-3">
                <div className="w-32 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm text-blue-400 font-medium">Unloading</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <Select value={fileMapping.unloading} onValueChange={(val) => setFileMapping({ ...fileMapping, unloading: val })}>
                  <SelectTrigger className="flex-1 bg-slate-900/50 border-slate-700 text-white" data-testid="map-unloading">
                    <SelectValue placeholder="Pilih file Unloading..." />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0B1221] border-slate-700">
                    {uploadedFiles.map((file, index) => (
                      <SelectItem key={index} value={index.toString()}>
                        {file.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Internal */}
              <div className="flex items-center gap-3">
                <div className="w-32 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                  <span className="text-sm text-amber-400 font-medium">Lab Internal</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <Select value={fileMapping.internal} onValueChange={(val) => setFileMapping({ ...fileMapping, internal: val })}>
                  <SelectTrigger className="flex-1 bg-slate-900/50 border-slate-700 text-white" data-testid="map-internal">
                    <SelectValue placeholder="Pilih file Lab Internal..." />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0B1221] border-slate-700">
                    {uploadedFiles.map((file, index) => (
                      <SelectItem key={index} value={index.toString()}>
                        {file.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Info */}
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs text-amber-300">
              <AlertCircle className="w-4 h-4 inline mr-1" />
              Data yang ada akan diganti dengan data baru dari file yang diupload.
            </div>
          </div>

          <DialogFooter>
            <Button 
              variant="ghost" 
              onClick={() => {
                setShowUploadDialog(false);
                setUploadedFiles([]);
                setFileMapping({ loading: "", unloading: "", internal: "" });
              }}
              disabled={uploading}
            >
              Batal
            </Button>
            <Button 
              onClick={processUploadedFiles} 
              className="bg-amber-600 hover:bg-amber-700"
              disabled={uploading || !fileMapping.loading || !fileMapping.unloading || !fileMapping.internal}
              data-testid="process-upload"
            >
              {uploading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Upload className="w-4 h-4 mr-2" />
              )}
              Proses & Upload
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default COAReconciliationPage;
