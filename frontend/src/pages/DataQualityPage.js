import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertTriangle,
  CheckCircle,
  Download,
  Loader2,
  RefreshCw,
  ShieldAlert,
  XCircle,
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MODULE_OPTIONS = [
  { value: "all", label: "Semua Modul" },
  { value: "smartstock", label: "Smart Stock Penerimaan" },
  { value: "sumberpemakaian", label: "Smart Stock Pemakaian" },
  { value: "po_batubara", label: "PO Batubara" },
  { value: "vessels", label: "Vessel" },
  { value: "barges", label: "Barge" },
  { value: "trucking", label: "Trucking" },
  { value: "biomassa", label: "Biomassa" },
  { value: "coa_reconciliation", label: "COA Reconciliation" },
];

const SEVERITY_OPTIONS = [
  { value: "all", label: "Semua Severity" },
  { value: "critical", label: "Kritis" },
  { value: "warning", label: "Perlu Perhatian" },
  { value: "info", label: "Info" },
];

const STATUS_STYLE = {
  healthy: { label: "Sehat", icon: CheckCircle, className: "border-emerald-500/30 bg-emerald-500/15 text-emerald-300" },
  info: { label: "Info", icon: AlertTriangle, className: "border-slate-500/30 bg-slate-500/15 text-slate-300" },
  warning: { label: "Perlu perhatian", icon: AlertTriangle, className: "border-amber-500/30 bg-amber-500/15 text-amber-300" },
  critical: { label: "Kritis", icon: XCircle, className: "border-red-500/30 bg-red-500/15 text-red-300" },
};

const getSeverityStyle = (severity) => STATUS_STYLE[severity] || STATUS_STYLE.info;

const StatusBadge = ({ status }) => {
  const item = getSeverityStyle(status);
  const Icon = item.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${item.className}`}>
      <Icon className="h-3.5 w-3.5" />
      {item.label}
    </span>
  );
};

const formatDateTime = (value) => {
  if (!value) return "Belum ada data";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const SummaryTile = ({ label, value, status }) => {
  const item = getSeverityStyle(status);
  const Icon = item.icon;
  return (
    <Card className="glass-card min-h-[112px] border-white/5 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-semibold text-white">{Number(value || 0).toLocaleString("id-ID")}</p>
        </div>
        <div className={`rounded-lg border p-2 ${item.className}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Card>
  );
};

const DataQualityPage = () => {
  const { getAuthHeader } = useAuth();
  const [report, setReport] = useState(null);
  const [module, setModule] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const fetchReport = useCallback(async () => {
    setError("");
    setRefreshing(true);
    try {
      const response = await axios.get(`${API_URL}/api/data-quality/summary`, {
        headers: getAuthHeader(),
        params: { module, severity, limit: 100 },
      });
      setReport(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Data quality monitor belum bisa dimuat");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAuthHeader, module, severity]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const handleExport = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/data-quality/export`, {
        headers: getAuthHeader(),
        params: { module, severity },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: "text/csv" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "emits-data-quality.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Export data quality dibuat");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Export data quality gagal");
    }
  };

  const resetFilters = () => {
    setModule("all");
    setSeverity("all");
  };

  const counts = report?.counts || {};
  const issues = report?.issues || [];

  return (
    <div className="space-y-6" data-testid="data-quality-page">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-2xl font-bold text-white lg:text-3xl">
            <ShieldAlert className="h-8 w-8 text-amber-300" />
            Data Quality Monitor
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Update terakhir: {formatDateTime(report?.generated_at)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={fetchReport}
            disabled={refreshing}
            className="border-slate-700 text-slate-300 hover:bg-white/5"
          >
            {refreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            Refresh
          </Button>
          <Button
            type="button"
            onClick={handleExport}
            className="bg-cyan-600 text-white hover:bg-cyan-500"
          >
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SummaryTile label="Kritis" value={counts.critical} status="critical" />
        <SummaryTile label="Perlu perhatian" value={counts.warning} status="warning" />
        <SummaryTile label="Info" value={counts.info} status="info" />
        <SummaryTile label="Total issue" value={counts.total} status={report?.status || "healthy"} />
      </div>

      <Card className="glass-card border-white/5 p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-col gap-3 sm:flex-row">
            <Select value={module} onValueChange={setModule}>
              <SelectTrigger className="w-full border-slate-700 bg-slate-950/70 text-slate-200 sm:w-[250px]">
                <SelectValue placeholder="Pilih modul" />
              </SelectTrigger>
              <SelectContent className="border-slate-700 bg-slate-900 text-slate-200">
                {MODULE_OPTIONS.map((item) => (
                  <SelectItem key={item.value} value={item.value}>{item.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={severity} onValueChange={setSeverity}>
              <SelectTrigger className="w-full border-slate-700 bg-slate-950/70 text-slate-200 sm:w-[210px]">
                <SelectValue placeholder="Pilih severity" />
              </SelectTrigger>
              <SelectContent className="border-slate-700 bg-slate-900 text-slate-200">
                {SEVERITY_OPTIONS.map((item) => (
                  <SelectItem key={item.value} value={item.value}>{item.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button type="button" variant="ghost" onClick={resetFilters} className="text-slate-300 hover:bg-white/5">
            Reset filter
          </Button>
        </div>

        {loading ? (
          <div className="mt-5 flex min-h-[260px] items-center justify-center rounded-lg border border-white/5 bg-slate-950/30">
            <Loader2 className="h-6 w-6 animate-spin text-cyan-300" />
          </div>
        ) : error ? (
          <div className="mt-5 rounded-lg border border-red-500/20 bg-red-500/10 p-4">
            <p className="text-sm font-medium text-red-200">Data quality gagal dimuat</p>
            <p className="mt-1 text-sm text-red-100/80">{error}</p>
          </div>
        ) : issues.length === 0 ? (
          <div className="mt-5 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-6">
            <div className="flex items-start gap-3">
              <CheckCircle className="mt-0.5 h-5 w-5 text-emerald-300" />
              <div>
                <p className="font-medium text-emerald-100">Tidak ada issue kualitas data pada filter ini.</p>
                <p className="mt-1 text-sm text-emerald-100/75">Tetap lakukan refresh setelah upload atau perubahan data besar.</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="mt-5 overflow-hidden rounded-lg border border-white/5">
            <div className="grid grid-cols-[120px_150px_minmax(180px,1fr)_minmax(220px,1.2fr)_minmax(220px,1.2fr)] gap-3 border-b border-white/5 bg-slate-950/60 px-4 py-3 text-xs font-medium uppercase text-slate-500 max-xl:hidden">
              <span>Severity</span>
              <span>Modul</span>
              <span>Sumber</span>
              <span>Issue</span>
              <span>Saran</span>
            </div>
            <div className="divide-y divide-white/5">
              {issues.map((issue) => (
                <div
                  key={issue.key}
                  className="grid gap-3 px-4 py-4 text-sm max-xl:grid-cols-1 xl:grid-cols-[120px_150px_minmax(180px,1fr)_minmax(220px,1.2fr)_minmax(220px,1.2fr)]"
                >
                  <div><StatusBadge status={issue.severity} /></div>
                  <div className="min-w-0">
                    <p className="break-words font-medium text-slate-200">{issue.module}</p>
                    <p className="mt-1 break-words text-xs text-slate-500">{issue.type}</p>
                  </div>
                  <div className="min-w-0">
                    <p className="break-words text-slate-200">{issue.source_label || "-"}</p>
                    <p className="mt-1 break-words text-xs text-slate-500">{issue.field || issue.source_record_id || "-"}</p>
                  </div>
                  <p className="min-w-0 break-words text-slate-300">{issue.message}</p>
                  <p className="min-w-0 break-words text-slate-400">{issue.suggested_fix}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default DataQualityPage;
