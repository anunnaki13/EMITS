import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  CheckCircle,
  Database,
  DatabaseBackup,
  HardDrive,
  Loader2,
  Radar,
  RefreshCw,
  Server,
  XCircle
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  healthy: { text: "Sistem operasional", className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30", icon: CheckCircle },
  pass: { text: "Lulus", className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30", icon: CheckCircle },
  warning: { text: "Perlu perhatian", className: "bg-amber-500/15 text-amber-300 border-amber-500/30", icon: AlertTriangle },
  disabled: { text: "Nonaktif", className: "bg-slate-500/15 text-slate-300 border-slate-500/30", icon: XCircle },
  unknown: { text: "Belum ada data", className: "bg-slate-500/15 text-slate-300 border-slate-500/30", icon: AlertTriangle },
  critical: { text: "Perlu tindakan", className: "bg-red-500/15 text-red-300 border-red-500/30", icon: XCircle },
  fail: { text: "Gagal", className: "bg-red-500/15 text-red-300 border-red-500/30", icon: XCircle }
};

const getStatusConfig = (status) => STATUS_CONFIG[status] || STATUS_CONFIG.unknown;

const StatusBadge = ({ status }) => {
  const config = getStatusConfig(status);
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${config.className}`}>
      <Icon className="h-3.5 w-3.5" />
      {config.text}
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
    minute: "2-digit"
  });
};

const formatBytes = (value) => {
  const bytes = Number(value || 0);
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
};

const formatBuildMetadata = (metadata, fallback) => {
  if (!metadata) return fallback;
  const release = metadata.release_tag || metadata.app_version;
  const build = metadata.build_id || metadata.git_sha;
  if (release && build) return `${release} / ${build}`;
  return release || build || fallback;
};

const HealthTile = ({ icon: Icon, label, status, detail, meta }) => (
  <div className="min-h-[132px] rounded-lg border border-white/5 bg-slate-950/35 p-4">
    <div className="flex items-start justify-between gap-3">
      <div className="flex min-w-0 items-center gap-2">
        <Icon className="h-4 w-4 shrink-0 text-slate-400" />
        <p className="truncate text-sm font-medium text-white">{label}</p>
      </div>
      <StatusBadge status={status} />
    </div>
    <p className="mt-3 text-sm text-slate-300">{detail || "Tidak tersedia"}</p>
    {meta ? <p className="mt-2 break-words text-xs text-slate-500">{meta}</p> : null}
  </div>
);

const RuntimeHealthPanel = ({ getAuthHeader }) => {
  const [runtime, setRuntime] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const fetchRuntimeStatus = useCallback(async () => {
    setError("");
    setRefreshing(true);
    try {
      const response = await axios.get(`${API_URL}/api/admin/runtime/status`, { headers: getAuthHeader() });
      setRuntime(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Runtime status belum bisa dibaca");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAuthHeader]);

  useEffect(() => {
    fetchRuntimeStatus();
  }, [fetchRuntimeStatus]);

  const diskPercent = Math.min(Math.max(Number(runtime?.disk?.used_percent || 0), 0), 100);
  const overallStatus = runtime?.status || "unknown";
  const backendVersion = runtime?.version?.backend || runtime?.backend?.version || runtime?.version;
  const frontendVersion = runtime?.version?.frontend || runtime?.frontend?.version;
  const backendVersionText = formatBuildMetadata(backendVersion, "backend build n/a");
  const frontendVersionText = formatBuildMetadata(frontendVersion, "frontend build n/a");

  return (
    <Card className="glass-card border-white/5 p-5" data-testid="runtime-health-panel">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-lg font-semibold text-white">Status Operasional</h2>
            <StatusBadge status={overallStatus} />
          </div>
          <p className="mt-2 text-sm text-slate-400">
            Update terakhir: {formatDateTime(runtime?.generated_at)}
          </p>
          <div className="mt-2 flex flex-wrap gap-2 font-mono text-[11px] text-slate-500">
            <span className="rounded-md border border-white/5 bg-slate-950/50 px-2 py-1">
              backend: {backendVersionText}
            </span>
            <span className="rounded-md border border-white/5 bg-slate-950/50 px-2 py-1">
              frontend: {frontendVersionText}
            </span>
            <span className="rounded-md border border-white/5 bg-slate-950/50 px-2 py-1">
              env: {runtime?.version?.environment || "unknown"}
            </span>
          </div>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={fetchRuntimeStatus}
          disabled={refreshing}
          className="border-slate-700 text-slate-300 hover:bg-white/5"
          data-testid="refresh-runtime-status-btn"
        >
          {refreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          Refresh status
        </Button>
      </div>

      {loading ? (
        <div className="mt-5 flex min-h-[220px] items-center justify-center rounded-lg border border-white/5 bg-slate-950/30">
          <Loader2 className="h-6 w-6 animate-spin text-cyan-300" />
        </div>
      ) : error ? (
        <div className="mt-5 rounded-lg border border-red-500/20 bg-red-500/10 p-4">
          <p className="text-sm font-medium text-red-200">Runtime status gagal dimuat</p>
          <p className="mt-1 text-sm text-red-100/80">{error}</p>
        </div>
      ) : (
        <>
          <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <HealthTile
              icon={Server}
              label="Backend/API"
              status={runtime?.backend?.status}
              detail={`Prefix ${runtime?.backend?.api_prefix || "/api"}`}
              meta={`Build ${backendVersionText}`}
            />
            <HealthTile
              icon={Database}
              label="MongoDB"
              status={runtime?.database?.status}
              detail={`${Number(runtime?.database?.collections || 0).toLocaleString("id-ID")} koleksi aktif`}
              meta={runtime?.database?.status === "critical" ? "Cek koneksi MongoDB di backend" : "Ping database berhasil"}
            />
            <HealthTile
              icon={DatabaseBackup}
              label="Backup"
              status={runtime?.backup?.status}
              detail={runtime?.backup?.reason || "Status backup belum tersedia"}
              meta={runtime?.backup?.latest_success?.finished_at ? `Backup terakhir ${formatDateTime(runtime.backup.latest_success.finished_at)}` : "Backup terakhir belum tercatat"}
            />
            <HealthTile
              icon={Radar}
              label="Smoke Check"
              status={runtime?.smoke?.status}
              detail={`${Number(runtime?.smoke?.passed || 0).toLocaleString("id-ID")} pass / ${Number(runtime?.smoke?.failed || 0).toLocaleString("id-ID")} fail`}
              meta={runtime?.smoke?.finished_at ? `Smoke terakhir ${formatDateTime(runtime.smoke.finished_at)}` : "Jalankan runtime_status.sh setelah deploy"}
            />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
            <div className="rounded-lg border border-white/5 bg-slate-950/35 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <HardDrive className="h-4 w-4 text-slate-400" />
                  <p className="text-sm font-medium text-white">Disk Server</p>
                </div>
                <StatusBadge status={runtime?.disk?.status} />
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
                <div className="h-full rounded-full bg-cyan-400" style={{ width: `${diskPercent}%` }} />
              </div>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
                <span>{diskPercent.toLocaleString("id-ID")}% terpakai</span>
                <span>{formatBytes(runtime?.disk?.free_bytes)} bebas</span>
              </div>
              <p className="mt-3 break-words font-mono text-[11px] text-slate-500">
                Static frontend: {frontendVersionText}
              </p>
            </div>

            <div className="rounded-lg border border-white/5 bg-slate-950/35 p-4">
              <p className="text-sm font-medium text-white">Smoke terakhir</p>
              <div className="mt-3 space-y-2">
                {(runtime?.smoke?.results || []).slice(0, 5).map((item) => (
                  <div key={`${item.name}-${item.detail}`} className="flex flex-col gap-1 rounded-md bg-slate-900/60 px-3 py-2 sm:flex-row sm:items-center sm:justify-between">
                    <span className="text-sm text-slate-200">{item.name}</span>
                    <span className={item.ok ? "text-xs text-emerald-300" : "text-xs text-red-300"}>{item.detail}</span>
                  </div>
                ))}
                {(!runtime?.smoke?.results || runtime.smoke.results.length === 0) ? (
                  <p className="text-sm text-slate-500">Belum ada smoke evidence yang tersimpan.</p>
                ) : null}
              </div>
            </div>
          </div>
        </>
      )}
    </Card>
  );
};

export default RuntimeHealthPanel;
