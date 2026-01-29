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
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import Pagination from "@/components/Pagination";
import {
  Scale,
  Loader2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Play,
  FileCheck,
  AlertTriangle,
  Building2,
  Calendar,
  Send
} from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
  Tooltip
} from "recharts";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DisputeMonitorPage = () => {
  const { getAuthHeader } = useAuth();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [summary, setSummary] = useState({ proposed: 0, in_progress: 0, completed: 0, total: 0 });
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [radarData, setRadarData] = useState([]);
  const [showResultDialog, setShowResultDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [resultForm, setResultForm] = useState({
    umpire_gcv_arb: "",
    umpire_tm_arb: "",
    umpire_ash_arb: "",
    umpire_ts_arb: "",
    umpire_lab_name: "",
    umpire_result_date: "",
    notes: ""
  });
  const PAGE_SIZE = 50;

  const fetchData = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = { page, page_size: PAGE_SIZE };
      if (statusFilter !== "all") params.umpire_status = statusFilter;

      const response = await axios.get(`${API_URL}/api/coa-reconciliation/dispute-monitor`, {
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
        setSummary(response.data.summary || { proposed: 0, in_progress: 0, completed: 0, total: 0 });
      }
    } catch (error) {
      toast.error("Gagal memuat data dispute");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeader, statusFilter]);

  useEffect(() => {
    fetchData(1);
  }, [statusFilter]);

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

  const handleStartProcess = async (record) => {
    try {
      await axios.post(
        `${API_URL}/api/coa-reconciliation/update-umpire-status/${record.id}?status=in_progress`,
        {},
        { headers: getAuthHeader() }
      );
      toast.success("Status diubah ke 'Sedang Diproses'");
      fetchData(pagination.page);
    } catch (error) {
      toast.error("Gagal mengubah status");
    }
  };

  const handleInputResult = (record) => {
    setSelectedRecord(record);
    setResultForm({
      umpire_gcv_arb: "",
      umpire_tm_arb: "",
      umpire_ash_arb: "",
      umpire_ts_arb: "",
      umpire_lab_name: "",
      umpire_result_date: new Date().toISOString().split('T')[0],
      notes: ""
    });
    setShowResultDialog(true);
  };

  const submitUmpireResult = async () => {
    if (!resultForm.umpire_gcv_arb || !resultForm.umpire_lab_name || !resultForm.umpire_result_date) {
      toast.error("GCV, Nama Lab, dan Tanggal Hasil wajib diisi");
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(
        `${API_URL}/api/coa-reconciliation/submit-umpire-result`,
        {
          reconciliation_id: selectedRecord.id,
          umpire_gcv_arb: parseFloat(resultForm.umpire_gcv_arb),
          umpire_tm_arb: resultForm.umpire_tm_arb ? parseFloat(resultForm.umpire_tm_arb) : null,
          umpire_ash_arb: resultForm.umpire_ash_arb ? parseFloat(resultForm.umpire_ash_arb) : null,
          umpire_ts_arb: resultForm.umpire_ts_arb ? parseFloat(resultForm.umpire_ts_arb) : null,
          umpire_lab_name: resultForm.umpire_lab_name,
          umpire_result_date: resultForm.umpire_result_date,
          notes: resultForm.notes
        },
        { headers: getAuthHeader() }
      );
      toast.success("Hasil umpire berhasil disimpan");
      setShowResultDialog(false);
      fetchData(pagination.page);
    } catch (error) {
      toast.error("Gagal menyimpan hasil umpire");
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      proposed: { icon: Clock, color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", label: "Diajukan" },
      in_progress: { icon: Play, color: "bg-blue-500/20 text-blue-400 border-blue-500/30", label: "Proses" },
      completed: { icon: CheckCircle, color: "bg-green-500/20 text-green-400 border-green-500/30", label: "Selesai" }
    };
    const cfg = config[status] || config.proposed;
    const Icon = cfg.icon;
    return (
      <Badge className={`${cfg.color} border flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {cfg.label}
      </Badge>
    );
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return "-";
    return num.toLocaleString("id-ID");
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    try {
      return new Date(dateStr).toLocaleDateString("id-ID", {
        day: "2-digit",
        month: "short",
        year: "numeric"
      });
    } catch {
      return dateStr;
    }
  };

  // Check if record has umpire data for 4-way comparison
  const hasUmpireData = (record) => record?.umpire_gcv_arb !== null && record?.umpire_gcv_arb !== undefined;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Scale className="w-7 h-7 text-purple-400" />
            Dispute Monitor
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Monitoring pengujian Umpire dan input hasil
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => fetchData(1)}
          className="border-slate-700 text-slate-300 hover:bg-slate-800"
          data-testid="refresh-btn"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-[#0B1221] border-yellow-500/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase">Diajukan</p>
              <p className="text-2xl font-bold text-yellow-400">{summary.proposed}</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-400/30" />
          </div>
        </Card>
        <Card className="bg-[#0B1221] border-blue-500/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase">Sedang Proses</p>
              <p className="text-2xl font-bold text-blue-400">{summary.in_progress}</p>
            </div>
            <Play className="w-8 h-8 text-blue-400/30" />
          </div>
        </Card>
        <Card className="bg-[#0B1221] border-green-500/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase">Selesai</p>
              <p className="text-2xl font-bold text-green-400">{summary.completed}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-400/30" />
          </div>
        </Card>
        <Card className="bg-[#0B1221] border-purple-500/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 uppercase">Total Dispute</p>
              <p className="text-2xl font-bold text-purple-400">{summary.total}</p>
            </div>
            <Scale className="w-8 h-8 text-purple-400/30" />
          </div>
        </Card>
      </div>

      {/* Filter */}
      <Card className="bg-[#0B1221] border-white/5 p-4">
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-400">Filter Status:</span>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-700 text-white" data-testid="status-filter">
              <SelectValue placeholder="Filter Status" />
            </SelectTrigger>
            <SelectContent className="bg-[#0B1221] border-slate-700">
              <SelectItem value="all">Semua Status</SelectItem>
              <SelectItem value="proposed">Diajukan</SelectItem>
              <SelectItem value="in_progress">Sedang Proses</SelectItem>
              <SelectItem value="completed">Selesai</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Dispute Table */}
      <Card className="bg-[#0B1221] border-white/5 overflow-hidden">
        <div className="p-4 border-b border-white/5">
          <h3 className="text-sm font-medium text-white">
            Daftar Pengujian Umpire ({pagination.total} data)
          </h3>
        </div>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400 text-xs">Shipment</TableHead>
                <TableHead className="text-slate-400 text-xs">Supplier</TableHead>
                <TableHead className="text-slate-400 text-xs">No. Sampel</TableHead>
                <TableHead className="text-slate-400 text-xs">Delta GCV</TableHead>
                <TableHead className="text-slate-400 text-xs text-center">Status</TableHead>
                <TableHead className="text-slate-400 text-xs">Tgl Diajukan</TableHead>
                <TableHead className="text-slate-400 text-xs">Lab Umpire</TableHead>
                <TableHead className="text-slate-400 text-xs text-center">Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-purple-400" />
                  </TableCell>
                </TableRow>
              ) : data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-slate-500">
                    Tidak ada data dispute. Ajukan umpire dari halaman COA Reconciliation.
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row) => (
                  <TableRow
                    key={row.id}
                    className={`border-white/5 ${row.umpire_status === "completed" ? "bg-green-500/5" : ""} hover:bg-white/5`}
                    data-testid={`row-${row.shipment}`}
                  >
                    <TableCell className="font-mono text-white text-sm">{row.shipment}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[120px] truncate">{row.suppliers}</TableCell>
                    <TableCell className="text-cyan-400 text-sm font-mono">{row.umpire_sample_number || "-"}</TableCell>
                    <TableCell className={`text-sm font-medium ${
                      row.delta_loading_internal > 150 ? "text-red-400" : 
                      row.delta_loading_internal > 100 ? "text-yellow-400" : "text-slate-300"
                    }`}>
                      {row.delta_loading_internal !== null ? `${row.delta_loading_internal > 0 ? "+" : ""}${Math.round(row.delta_loading_internal)}` : "-"}
                    </TableCell>
                    <TableCell className="text-center">{getStatusBadge(row.umpire_status)}</TableCell>
                    <TableCell className="text-slate-400 text-sm">{formatDate(row.umpire_proposed_at)}</TableCell>
                    <TableCell className="text-slate-300 text-sm">{row.umpire_lab_name || "-"}</TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(row)}
                          className="h-7 px-2 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10"
                          data-testid={`view-${row.shipment}`}
                        >
                          <FileCheck className="w-3 h-3" />
                        </Button>
                        {row.umpire_status === "proposed" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStartProcess(row)}
                            className="h-7 px-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                            title="Mulai Proses"
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                        )}
                        {(row.umpire_status === "proposed" || row.umpire_status === "in_progress") && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleInputResult(row)}
                            className="h-7 px-2 text-green-400 hover:text-green-300 hover:bg-green-500/10"
                            title="Input Hasil"
                            data-testid={`input-result-${row.shipment}`}
                          >
                            <Send className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
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

      {/* Detail Dialog with Radar Chart (4 sources if umpire data exists) */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="bg-[#0B1221] border-white/10 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>Detail Shipment {selectedRecord?.shipment}</DialogTitle>
            <DialogDescription className="text-slate-400">
              {hasUmpireData(selectedRecord) ? "Perbandingan 4 Sumber (Triple Check + Umpire)" : "Perbandingan 3 Sumber (Triple Check)"}
            </DialogDescription>
          </DialogHeader>
          {selectedRecord && (
            <div className="space-y-4">
              {/* Status Info */}
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-xs text-slate-500">Status Umpire</p>
                  {getStatusBadge(selectedRecord.umpire_status)}
                </div>
                {selectedRecord.umpire_lab_name && (
                  <div>
                    <p className="text-xs text-slate-500">Lab Umpire</p>
                    <p className="text-sm text-white">{selectedRecord.umpire_lab_name}</p>
                  </div>
                )}
              </div>

              {/* Radar Chart */}
              <div className="bg-slate-900/50 rounded-lg p-4">
                <h4 className="text-sm font-medium mb-4">
                  Grafik Radar - Profil Kualitas {hasUmpireData(selectedRecord) && "(Quad Check)"}
                </h4>
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="parameter" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 9 }} />
                    <Radar name="Loading" dataKey="loading" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} />
                    <Radar name="Unloading" dataKey="unloading" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                    <Radar name="Internal" dataKey="internal" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
                    {hasUmpireData(selectedRecord) && (
                      <Radar name="Umpire" dataKey="umpire" stroke="#a855f7" fill="#a855f7" fillOpacity={0.3} />
                    )}
                    <Legend />
                    <Tooltip contentStyle={{ backgroundColor: "#0B1221", border: "1px solid #1e293b" }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Values Comparison */}
              <div className={`grid ${hasUmpireData(selectedRecord) ? "grid-cols-4" : "grid-cols-3"} gap-3 text-sm`}>
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
                {hasUmpireData(selectedRecord) && (
                  <div className="bg-purple-500/10 rounded-lg p-3">
                    <p className="text-purple-400 font-medium text-xs mb-2">Umpire</p>
                    <p>GCV: {formatNumber(selectedRecord.umpire_gcv_arb)}</p>
                    <p>TM: {selectedRecord.umpire_tm_arb || "-"}%</p>
                    <p>Ash: {selectedRecord.umpire_ash_arb || "-"}%</p>
                    <p>S: {selectedRecord.umpire_ts_arb || "-"}%</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Input Umpire Result Dialog */}
      <Dialog open={showResultDialog} onOpenChange={setShowResultDialog}>
        <DialogContent className="bg-[#0B1221] border-white/10 text-white max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-green-400" />
              Input Hasil Umpire
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Shipment {selectedRecord?.shipment} - {selectedRecord?.suppliers}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Info */}
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3 text-sm">
              <p className="text-purple-300">
                <Building2 className="w-4 h-4 inline mr-1" />
                No. Sampel: <span className="font-mono">{selectedRecord?.umpire_sample_number}</span>
              </p>
            </div>

            {/* Lab Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nama Lab Umpire *</Label>
                <Input
                  value={resultForm.umpire_lab_name}
                  onChange={(e) => setResultForm({ ...resultForm, umpire_lab_name: e.target.value })}
                  placeholder="Contoh: PT Sucofindo"
                  className="bg-slate-900/50 border-slate-700"
                  data-testid="umpire-lab-name"
                />
              </div>
              <div className="space-y-2">
                <Label>Tanggal Hasil *</Label>
                <Input
                  type="date"
                  value={resultForm.umpire_result_date}
                  onChange={(e) => setResultForm({ ...resultForm, umpire_result_date: e.target.value })}
                  className="bg-slate-900/50 border-slate-700"
                  data-testid="umpire-result-date"
                />
              </div>
            </div>

            {/* Quality Parameters */}
            <div className="space-y-3">
              <p className="text-sm font-medium text-purple-400">Parameter Kualitas Hasil Umpire</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs">GCV ARB (kCal/kg) *</Label>
                  <Input
                    type="number"
                    value={resultForm.umpire_gcv_arb}
                    onChange={(e) => setResultForm({ ...resultForm, umpire_gcv_arb: e.target.value })}
                    placeholder="4400"
                    className="bg-slate-900/50 border-slate-700"
                    data-testid="umpire-gcv"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">TM ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={resultForm.umpire_tm_arb}
                    onChange={(e) => setResultForm({ ...resultForm, umpire_tm_arb: e.target.value })}
                    placeholder="32"
                    className="bg-slate-900/50 border-slate-700"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Ash ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={resultForm.umpire_ash_arb}
                    onChange={(e) => setResultForm({ ...resultForm, umpire_ash_arb: e.target.value })}
                    placeholder="5"
                    className="bg-slate-900/50 border-slate-700"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Sulphur ARB (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={resultForm.umpire_ts_arb}
                    onChange={(e) => setResultForm({ ...resultForm, umpire_ts_arb: e.target.value })}
                    placeholder="0.4"
                    className="bg-slate-900/50 border-slate-700"
                  />
                </div>
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <Label>Catatan (Opsional)</Label>
              <Textarea
                value={resultForm.notes}
                onChange={(e) => setResultForm({ ...resultForm, notes: e.target.value })}
                placeholder="Catatan tambahan..."
                className="bg-slate-900/50 border-slate-700"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowResultDialog(false)} disabled={submitting}>Batal</Button>
            <Button 
              onClick={submitUmpireResult} 
              className="bg-green-600 hover:bg-green-700"
              disabled={submitting}
              data-testid="submit-result"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Simpan Hasil
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DisputeMonitorPage;
