import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Ship,
  Anchor,
  Truck,
  Leaf,
  TrendingUp,
  Flame,
  Activity,
  BarChart3,
  Target,
  AlertTriangle,
  Gauge,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
  Filter,
  Package,
  CalendarCheck,
  Scale,
  ShieldCheck,
  Clock3,
  ArrowRight,
  CircleAlert,
  TrendingDown,
  Minus
} from "lucide-react";
import { parseDashboardDrilldown } from "@/utils/dashboardDrilldown";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
  ReferenceLine,
  RadialBarChart,
  RadialBar
} from "recharts";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CHART_COLORS = ['#06B6D4', '#3B82F6', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6'];
const RISK_COLORS = {
  'SEVERE': '#EF4444',
  'HIGH': '#F59E0B',
  'MEDIUM': '#FBBF24',
  'LOW': '#10B981',
  'UNKNOWN': '#6B7280'
};

const STAT_CARD_TONES = {
  cyan: { iconBg: "bg-cyan-500/10", iconText: "text-cyan-400" },
  blue: { iconBg: "bg-blue-500/10", iconText: "text-blue-400" },
  amber: { iconBg: "bg-amber-500/10", iconText: "text-amber-400" },
  emerald: { iconBg: "bg-emerald-500/10", iconText: "text-emerald-400" },
};

const StatCard = ({ title, value, subtitle, icon: Icon, color = "cyan" }) => {
  const tone = STAT_CARD_TONES[color] || STAT_CARD_TONES.cyan;
  return (
    <Card className="glass-card border-white/10 hover:border-cyan-500/30">
      <CardContent className="p-4 sm:p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1 sm:space-y-2">
            <p className="text-[10px] sm:text-xs font-mono uppercase tracking-wider text-slate-500">{title}</p>
            <p className="font-heading text-xl sm:text-2xl lg:text-3xl font-bold text-white">{value}</p>
            {subtitle && <p className="text-xs sm:text-sm text-slate-400">{subtitle}</p>}
          </div>
          <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl ${tone.iconBg} flex items-center justify-center`}>
            <Icon className={`w-5 h-5 sm:w-6 sm:h-6 ${tone.iconText}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const trendTone = (metric = {}) => {
  if (metric.status === "improving") return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  if (metric.status === "worsening") return "border-red-500/40 bg-red-500/10 text-red-300";
  if (metric.status === "stable") return "border-blue-500/40 bg-blue-500/10 text-blue-300";
  return "border-slate-500/40 bg-slate-500/10 text-slate-300";
};

const TrendDirectionBadge = ({ metric }) => {
  const Icon = metric?.direction === "up" ? TrendingUp : metric?.direction === "down" ? TrendingDown : Minus;
  return (
    <span className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-semibold ${trendTone(metric)}`}>
      <Icon className="w-3 h-3" />
      {metric?.direction_label || "Belum cukup data"}
    </span>
  );
};

// Gauge Chart Component
const GaugeChart = ({ percentage, label }) => {
  const data = [{ name: 'Progress', value: percentage, fill: percentage >= 90 ? '#10B981' : percentage >= 70 ? '#F59E0B' : '#EF4444' }];
  
  return (
    <div className="relative h-48 sm:h-56">
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart 
          cx="50%" 
          cy="50%" 
          innerRadius="60%" 
          outerRadius="90%" 
          barSize={20} 
          data={data}
          startAngle={180}
          endAngle={0}
        >
          <RadialBar
            background={{ fill: '#1e293b' }}
            dataKey="value"
            cornerRadius={10}
          />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl sm:text-4xl font-bold text-white">{percentage.toFixed(1)}%</span>
        <span className="text-xs sm:text-sm text-slate-400">{label}</span>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { getAuthHeader } = useAuth();
  const initialDrilldown = parseDashboardDrilldown(window.location.search);
  const [stats, setStats] = useState(null);
  const [advancedStats, setAdvancedStats] = useState(null);
  const [operationalStats, setOperationalStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(initialDrilldown.period || "all");
  const [selectedSupplier, setSelectedSupplier] = useState(initialDrilldown.supplier || "all");
  const [selectedMode, setSelectedMode] = useState(initialDrilldown.mode || "all");

  const fetchData = useCallback(async () => {
    try {
      const advancedParams = {};
      if (selectedPeriod && selectedPeriod !== "all" && selectedPeriod.length === 7) {
        const [year, month] = selectedPeriod.split("-");
        advancedParams.year = Number(year);
        advancedParams.month = Number(month);
      }
      if (selectedMode && selectedMode !== "all") {
        advancedParams.moda = selectedMode;
      }

      const [statsRes, advancedRes, operationalRes] = await Promise.all([
        axios.get(`${API_URL}/api/dashboard/stats`, { headers: getAuthHeader() }),
        axios.get(`${API_URL}/api/dashboard/advanced`, { headers: getAuthHeader(), params: advancedParams }),
        axios.get(`${API_URL}/api/dashboard/operational`, {
          headers: getAuthHeader(),
          params: { period: selectedPeriod, supplier: selectedSupplier, mode: selectedMode }
        })
      ]);
      setStats(statsRes.data);
      setAdvancedStats(advancedRes.data);
      setOperationalStats(operationalRes.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
      toast.error("Gagal memuat statistik");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeader, selectedMode, selectedPeriod, selectedSupplier]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatNumber = (num) => {
    if (!num) return "0";
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toFixed(0);
  };

  const formatCurrency = (num) => {
    if (!num) return "Rp 0";
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(num);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 sm:h-32 bg-slate-900/50 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          <div className="lg:col-span-2 h-72 sm:h-80 bg-slate-900/50 rounded-xl" />
          <div className="h-72 sm:h-80 bg-slate-900/50 rounded-xl" />
        </div>
      </div>
    );
  }

  const sixMonthsData = advancedStats?.six_months_summary || [];
  const fuelComposition = advancedStats?.fuel_composition || [];
  const gcvTrend = advancedStats?.gcv_trend || [];
  const supplierEconomy = advancedStats?.supplier_economy || [];
  const slaggingMatrix = advancedStats?.slagging_matrix || [];
  const stock = operationalStats?.stock || {};
  const arrivals = operationalStats?.arrivals || {};
  const disputes = operationalStats?.disputes || {};
  const dataQuality = operationalStats?.data_quality || {};
  const trendAnalytics = operationalStats?.trend_analytics || {};
  const trendMetrics = trendAnalytics.metrics || {};
  const stockForecast = trendAnalytics.stock_forecast || {};
  const realizedByMode = arrivals.realized_by_mode || [];
  const supplierRisk = operationalStats?.supplier_risk || [];
  const upcomingSchedule = arrivals.upcoming_schedule || [];
  const atRiskSchedule = arrivals.at_risk_schedule || [];
  const recentDisputes = disputes.recent || [];
  const periodOptions = operationalStats?.available_periods || [
    { value: "all", label: "Semua Periode" },
    { value: "2026", label: "2026" },
    { value: "2025", label: "2025" },
    { value: "2024", label: "2024" }
  ];
  const supplierOptions = operationalStats?.available_suppliers || [{ value: "all", label: "Semua Supplier" }];
  const modeOptions = operationalStats?.available_modes || [
    { value: "all", label: "Semua Moda" },
    { value: "vessel", label: "Vessel" },
    { value: "barge", label: "Barge/Tongkang" },
    { value: "trucking", label: "Trucking" },
    { value: "biomassa", label: "Biomassa" }
  ];
  const stockStatusStyles = {
    critical: "border-red-500/50 bg-red-500/10 text-red-300",
    warning: "border-amber-500/50 bg-amber-500/10 text-amber-300",
    watch: "border-blue-500/50 bg-blue-500/10 text-blue-300",
    healthy: "border-emerald-500/50 bg-emerald-500/10 text-emerald-300",
    unknown: "border-slate-500/50 bg-slate-500/10 text-slate-300"
  };
  const stockTone = stockStatusStyles[stock.status] || stockStatusStyles.unknown;
  const fulfillmentRate = arrivals.fulfillment_rate ?? 0;
  const tonnageFulfillmentRate = arrivals.tonnage_fulfillment_rate ?? 0;
  const primaryRiskCount = (disputes.critical_count || 0) + (disputes.umpire?.active || 0) + (arrivals.at_risk_count || 0);
  const supplierRiskStyles = {
    high: "border-red-500/50 bg-red-500/10 text-red-300",
    medium: "border-amber-500/50 bg-amber-500/10 text-amber-300",
    low: "border-emerald-500/50 bg-emerald-500/10 text-emerald-300",
  };
  const drilldownParams = new URLSearchParams();
  drilldownParams.set("from", "dashboard");
  if (selectedPeriod && selectedPeriod !== "all") drilldownParams.set("period", selectedPeriod);
  if (selectedSupplier && selectedSupplier !== "all") drilldownParams.set("supplier", selectedSupplier);
  if (selectedMode && selectedMode !== "all") drilldownParams.set("mode", selectedMode);
  const drilldownHref = (path, extraParams = {}) => {
    const params = new URLSearchParams(drilldownParams);
    Object.entries(extraParams).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "all" && value !== "") {
        params.set(key, value);
      }
    });
    const query = params.toString();
    return query ? `${path}?${query}` : path;
  };
  const quickActions = [
    {
      label: "Stock Batubara",
      metric: `${formatNumber(stock.current_stock || 0)} MT`,
      href: drilldownHref("/smart-stock/sumber-penerimaan"),
      icon: Package,
      tone: "text-cyan-300",
    },
    {
      label: "Jadwal PO",
      metric: `${arrivals.at_risk_count || 0} at-risk`,
      href: drilldownHref("/po-batubara"),
      icon: CalendarCheck,
      tone: "text-blue-300",
    },
    {
      label: "Dispute / Umpire",
      metric: `${disputes.umpire?.active || 0} aktif`,
      href: drilldownHref("/dispute-monitor"),
      icon: Scale,
      tone: "text-red-300",
    },
    {
      label: "Report Manajemen",
      metric: `${trendAnalytics.confidence || "low"} confidence`,
      href: drilldownHref("/laporan", { tab: "management" }),
      icon: BarChart3,
      tone: "text-emerald-300",
    },
    {
      label: "Data Quality",
      metric: `${dataQuality.counts?.critical || 0} critical`,
      href: drilldownHref("/data-quality"),
      icon: AlertTriangle,
      tone: dataQuality.status === "critical" ? "text-red-300" : "text-amber-300",
    },
  ];

  return (
    <div className="space-y-6 sm:space-y-8" data-testid="dashboard-page">
      {/* Header with Filters */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-xl sm:text-2xl lg:text-3xl text-white">
            Dashboard Operasional Bahan Bakar
          </h1>
          <p className="text-slate-400 mt-1 text-sm sm:text-base">
            Monitoring stok, kedatangan, dan dispute kualitas - UP Tenayan
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-full sm:w-[170px] bg-slate-900/50 border-slate-700 text-white" data-testid="dashboard-period-filter">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Periode" />
            </SelectTrigger>
            <SelectContent className="bg-[#0B1221] border-slate-800">
              {periodOptions.map(period => (
                <SelectItem key={period.value} value={period.value} className="text-slate-300">{period.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedSupplier} onValueChange={setSelectedSupplier}>
            <SelectTrigger className="w-full sm:w-[230px] bg-slate-900/50 border-slate-700 text-white" data-testid="dashboard-supplier-filter">
              <ShieldCheck className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Supplier" />
            </SelectTrigger>
            <SelectContent className="max-h-80 bg-[#0B1221] border-slate-800">
              {supplierOptions.map(item => (
                <SelectItem key={item.value} value={item.value} className="text-slate-300">{item.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedMode} onValueChange={setSelectedMode}>
            <SelectTrigger className="w-full sm:w-[170px] bg-slate-900/50 border-slate-700 text-white" data-testid="dashboard-mode-filter">
              <Anchor className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Moda" />
            </SelectTrigger>
            <SelectContent className="bg-[#0B1221] border-slate-800">
              {modeOptions.map(item => (
                <SelectItem key={item.value} value={item.value} className="text-slate-300">{item.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
        {quickActions.map((item) => {
          const Icon = item.icon;
          return (
            <a
              key={item.label}
              href={item.href}
              className="rounded-lg border border-white/10 bg-slate-900/45 p-3 hover:border-cyan-500/30 hover:bg-slate-900/70"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[10px] font-mono uppercase text-slate-500">{item.label}</p>
                  <p className="mt-1 truncate text-sm font-semibold text-white">{item.metric}</p>
                </div>
                <Icon className={`h-5 w-5 shrink-0 ${item.tone}`} />
              </div>
            </a>
          );
        })}
      </div>

      {["critical", "warning"].includes(dataQuality.status) && (
        <div className={`rounded-lg border p-4 ${
          dataQuality.status === "critical"
            ? "border-red-500/30 bg-red-500/10"
            : "border-amber-500/30 bg-amber-500/10"
        }`}>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-start gap-3">
              <AlertTriangle className={`mt-0.5 h-5 w-5 ${dataQuality.status === "critical" ? "text-red-300" : "text-amber-300"}`} />
              <div>
                <p className={`text-sm font-semibold ${dataQuality.status === "critical" ? "text-red-200" : "text-amber-200"}`}>
                  Data perlu dicek sebelum keputusan final
                </p>
                <div className="mt-2 space-y-1">
                  {(dataQuality.caveats || []).slice(0, 3).map((item) => (
                    <p key={item} className="text-xs text-slate-200/85">{item}</p>
                  ))}
                </div>
              </div>
            </div>
            <a href="/data-quality" className="shrink-0 rounded bg-slate-950/60 px-3 py-2 text-xs font-semibold text-cyan-200 hover:bg-slate-900">
              Buka Data Quality
            </a>
          </div>
        </div>
      )}

      {/* Operational First Viewport */}
      <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-4 gap-4 sm:gap-6">
        <Card className="glass-card border-white/10 min-h-[360px]">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <CardTitle className="font-heading text-base text-white flex items-center gap-2">
                <Package className="w-5 h-5 text-cyan-400" />
                Monitoring Stock Batubara
              </CardTitle>
              <span className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${stockTone}`}>
                {stock.label || "Belum ada status"}
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-[1.2fr_0.8fr] gap-4">
              <div>
                <p className="text-[10px] font-mono uppercase text-slate-500">Stok Saat Ini</p>
                <p className="font-heading text-4xl font-bold text-white">{formatNumber(stock.current_stock || 0)} MT</p>
                <p className="text-xs text-slate-500">Update stok: {stock.latest_stock_date || "-"}</p>
              </div>
              <div className="rounded-lg border border-white/10 bg-slate-900/50 p-3">
                <div className="flex items-center gap-2 text-slate-400">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs">Projected supply</span>
                </div>
                <p className="mt-2 font-heading text-3xl font-bold text-white">{stock.days_of_supply ?? "-"} hari</p>
                <p className="text-xs text-slate-500">Threshold reorder {stock.reorder_threshold_days || 14} hari</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-emerald-500/10 p-3">
                <p className="text-xs text-emerald-300">Penerimaan</p>
                <p className="text-base font-bold text-white">{formatNumber(stock.total_penerimaan || 0)} MT</p>
              </div>
              <div className="rounded-lg bg-amber-500/10 p-3">
                <p className="text-xs text-amber-300">Pemakaian</p>
                <p className="text-base font-bold text-white">{formatNumber(stock.total_pemakaian || 0)} MT</p>
              </div>
              <div className="rounded-lg bg-blue-500/10 p-3">
                <p className="text-xs text-blue-300">Burn rate</p>
                <p className="text-base font-bold text-white">{formatNumber(stock.avg_daily_usage || 0)} MT/hari</p>
              </div>
              <a href={drilldownHref("/smart-stock/sumber-penerimaan")} className="rounded-lg bg-slate-900/50 p-3 hover:bg-slate-800/80">
                <p className="text-xs text-slate-400">Drilldown</p>
                <p className="mt-1 flex items-center gap-1 text-sm font-semibold text-cyan-300">Smart Stock <ArrowRight className="w-3 h-3" /></p>
              </a>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-white/10 min-h-[360px]">
          <CardHeader className="pb-3">
            <CardTitle className="font-heading text-base text-white flex items-center gap-2">
              <CalendarCheck className="w-5 h-5 text-blue-400" />
              Jadwal vs Realisasi
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-lg bg-blue-500/10 p-3">
                <p className="text-xs text-blue-300">Jadwal</p>
                <p className="text-2xl font-bold text-white">{arrivals.scheduled_count || 0}</p>
                <p className="text-xs text-slate-500">{formatNumber(arrivals.scheduled_tonnage || 0)} MT</p>
              </div>
              <div className="rounded-lg bg-emerald-500/10 p-3">
                <p className="text-xs text-emerald-300">Realisasi</p>
                <p className="text-2xl font-bold text-white">{arrivals.realized_count || 0}</p>
                <p className="text-xs text-slate-500">{formatNumber(arrivals.realized_tonnage || 0)} MT</p>
              </div>
              <div className="rounded-lg bg-red-500/10 p-3">
                <p className="text-xs text-red-300">At-risk</p>
                <p className="text-2xl font-bold text-white">{arrivals.at_risk_count || 0}</p>
                <p className="text-xs text-slate-500">jadwal</p>
              </div>
            </div>
            <div className="space-y-2">
              <div>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-slate-400">Fulfilment jumlah</span>
                  <span className="font-mono text-white">{fulfillmentRate.toFixed(0)}%</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800">
                  <div className="h-2 rounded-full bg-blue-400" style={{ width: `${Math.min(fulfillmentRate, 100)}%` }} />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-slate-400">Fulfilment tonase</span>
                  <span className="font-mono text-white">{tonnageFulfillmentRate.toFixed(0)}%</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800">
                  <div className="h-2 rounded-full bg-emerald-400" style={{ width: `${Math.min(tonnageFulfillmentRate, 100)}%` }} />
                </div>
              </div>
            </div>
            {realizedByMode.length > 0 && (
              <div className="grid grid-cols-2 gap-2">
                {realizedByMode.slice(0, 4).map(item => (
                  <div key={item.mode} className="rounded-lg bg-slate-900/50 px-3 py-2">
                    <p className="text-[10px] uppercase text-slate-500">{item.mode}</p>
                    <p className="text-sm font-semibold text-white">{item.count || 0} / {formatNumber(item.tonnage || 0)} MT</p>
                  </div>
                ))}
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              <a href={drilldownHref("/po-batubara")} className="rounded-lg bg-slate-900/50 p-3 text-sm font-semibold text-blue-300 hover:bg-slate-800/80">
                Jadwal PO <ArrowRight className="inline w-3 h-3" />
              </a>
              <a href={drilldownHref("/laporan", { tab: "management" })} className="rounded-lg bg-slate-900/50 p-3 text-sm font-semibold text-emerald-300 hover:bg-slate-800/80">
                Realisasi <ArrowRight className="inline w-3 h-3" />
              </a>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-white/10 min-h-[360px]">
          <CardHeader className="pb-3">
            <CardTitle className="font-heading text-base text-white flex items-center gap-2">
              <Scale className="w-5 h-5 text-red-400" />
              Dispute / Umpire
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3">
              <div className="flex items-center justify-between">
                <p className="flex items-center gap-2 text-sm text-red-200"><CircleAlert className="w-4 h-4" /> Prioritas</p>
                <p className="font-heading text-3xl font-bold text-white">{primaryRiskCount}</p>
              </div>
              <p className="text-xs text-slate-400">Critical, umpire aktif, dan jadwal at-risk</p>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded-lg bg-red-500/10 p-2">
                <p className="text-xs text-red-300">Critical</p>
                <p className="text-xl font-bold text-white">{disputes.critical_count || 0}</p>
              </div>
              <div className="rounded-lg bg-amber-500/10 p-2">
                <p className="text-xs text-amber-300">Warning</p>
                <p className="text-xl font-bold text-white">{disputes.warning_count || 0}</p>
              </div>
              <div className="rounded-lg bg-blue-500/10 p-2">
                <p className="text-xs text-blue-300">Umpire</p>
                <p className="text-xl font-bold text-white">{disputes.umpire?.active || 0}</p>
              </div>
            </div>
            <div className="space-y-2 max-h-36 overflow-y-auto">
              {recentDisputes.length > 0 ? recentDisputes.slice(0, 4).map(item => (
                <div key={item.id || item.shipment} className="rounded-lg bg-slate-900/50 p-2">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-white truncate">{item.shipment || "-"}</p>
                    <span className="text-[10px] uppercase text-slate-400">{item.umpire_status || item.status || "-"}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs text-slate-500 truncate">{item.suppliers || "-"}</p>
                    <span className="text-[10px] text-slate-500">{item.aging_days ?? "-"} hari</span>
                  </div>
                </div>
              )) : (
                <p className="text-sm text-slate-500 py-4 text-center">Tidak ada dispute aktif</p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <a href={drilldownHref("/dispute-monitor")} className="rounded-lg bg-slate-900/50 p-3 text-sm font-semibold text-red-300 hover:bg-slate-800/80">
                Dispute <ArrowRight className="inline w-3 h-3" />
              </a>
              <a href={drilldownHref("/coa-reconciliation")} className="rounded-lg bg-slate-900/50 p-3 text-sm font-semibold text-amber-300 hover:bg-slate-800/80">
                COA <ArrowRight className="inline w-3 h-3" />
              </a>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-white/10 min-h-[360px]">
          <CardHeader className="pb-3">
            <CardTitle className="font-heading text-base text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-amber-400" />
              Risiko Supplier
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {supplierRisk.length > 0 ? supplierRisk.slice(0, 5).map(item => {
                const riskTone = supplierRiskStyles[item.risk_level] || supplierRiskStyles.low;
                return (
                  <div key={item.supplier} className="rounded-lg bg-slate-900/50 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-semibold text-white truncate">{item.supplier}</p>
                      <span className={`rounded border px-2 py-0.5 text-[10px] font-semibold uppercase ${riskTone}`}>
                        {item.risk_level}
                      </span>
                    </div>
                    <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <p className="text-slate-500">Score</p>
                        <p className="font-semibold text-white">{Number(item.risk_score || 0).toFixed(0)}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Delta</p>
                        <p className="font-semibold text-white">{item.avg_delta != null ? Number(item.avg_delta).toFixed(0) : "-"}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Dispute</p>
                        <p className="font-semibold text-white">{item.active_disputes || 0}</p>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                      <span>{item.realized_count || 0}/{item.scheduled_count || 0} realisasi</span>
                      <span>{item.timeliness_rate != null ? `${Number(item.timeliness_rate).toFixed(0)}% on-time` : "jadwal belum ada"}</span>
                    </div>
                  </div>
                );
              }) : (
                <p className="text-sm text-slate-500 py-6 text-center">Belum ada sinyal risiko supplier</p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <a href={drilldownHref("/coa-reconciliation")} className="rounded-lg bg-slate-900/50 p-3 text-sm font-semibold text-amber-300 hover:bg-slate-800/80">
                COA Reconcile <ArrowRight className="inline w-3 h-3" />
              </a>
              <a href={drilldownHref("/laporan", { tab: "management" })} className="rounded-lg bg-slate-900/50 p-3 text-sm font-semibold text-cyan-300 hover:bg-slate-800/80">
                Report <ArrowRight className="inline w-3 h-3" />
              </a>
            </div>
          </CardContent>
        </Card>
      </div>

      {operationalStats?.trend_analytics && (
        <Card className="glass-card border-white/10">
          <CardHeader>
            <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <CardTitle className="font-heading text-sm sm:text-base text-white flex items-center gap-2">
                  <LineChartIcon className="w-5 h-5 text-cyan-400" />
                  Trend & Forecast
                </CardTitle>
                <p className="text-xs text-slate-500 mt-1">
                  {trendAnalytics.period_comparison?.current?.label || "-"} dibanding {trendAnalytics.period_comparison?.previous?.label || "-"}
                </p>
              </div>
              <span className={`w-fit rounded border px-2.5 py-1 text-[10px] font-semibold uppercase ${
                trendAnalytics.confidence === "high" ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300" :
                trendAnalytics.confidence === "medium" ? "border-amber-500/40 bg-amber-500/10 text-amber-300" :
                "border-red-500/40 bg-red-500/10 text-red-300"
              }`}>
                Confidence: {trendAnalytics.confidence || "low"}
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {trendAnalytics.sparse_data && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
                {(trendAnalytics.caveats || []).slice(0, 3).map((item) => (
                  <p key={item} className="text-xs text-amber-100/90">{item}</p>
                ))}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
              {[
                trendMetrics.stock_coverage,
                trendMetrics.arrivals,
                trendMetrics.supplier_performance,
                trendMetrics.quality_delta,
                trendMetrics.disputes
              ].filter(Boolean).map((metric) => (
                <div key={metric.label} className="rounded-lg border border-white/5 bg-slate-900/50 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-[11px] text-slate-400">{metric.label}</p>
                    <TrendDirectionBadge metric={metric} />
                  </div>
                  <p className="mt-2 text-xl font-bold text-white">
                    {formatNumber(Number(metric.current || 0))} {metric.unit}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Sebelumnya {formatNumber(Number(metric.previous || 0))} | delta {formatNumber(Number(metric.delta || 0))}
                  </p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-4">
              <div className="rounded-lg border border-white/5 bg-slate-900/50 p-4">
                <p className="text-xs text-slate-400">Forecast stok</p>
                <p className="mt-1 font-heading text-3xl font-bold text-white">{stockForecast.projected_coverage_days ?? "-"} hari</p>
                <p className="text-xs text-slate-500">
                  Burn {formatNumber(stockForecast.avg_daily_usage || 0)} MT/hari | arrivals 30 hari {formatNumber(stockForecast.expected_arrivals_30d || 0)} MT
                </p>
                <div className="mt-3 grid grid-cols-3 gap-2">
                  {(stockForecast.horizons || []).map((item) => (
                    <div key={item.days} className="rounded-lg bg-slate-950/70 p-2">
                      <p className="text-[10px] text-slate-500">{item.days} hari</p>
                      <p className="text-sm font-semibold text-white">{formatNumber(item.projected_stock || 0)} MT</p>
                      <p className="text-[10px] text-slate-500">{item.projected_coverage_days} hari</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-white/5 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-800">
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Supplier</th>
                      <th className="text-left py-2 px-3 text-slate-500 font-medium">Risk</th>
                      <th className="text-right py-2 px-3 text-slate-500 font-medium">Volume</th>
                      <th className="text-right py-2 px-3 text-slate-500 font-medium">On-time</th>
                      <th className="text-right py-2 px-3 text-slate-500 font-medium">Delta COA</th>
                      <th className="text-right py-2 px-3 text-slate-500 font-medium">Dispute</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(trendAnalytics.supplier_trends || []).slice(0, 6).map((item) => (
                      <tr key={item.supplier} className="border-b border-slate-800/50">
                        <td className="py-2 px-3 text-white max-w-[240px] whitespace-normal">{item.supplier}</td>
                        <td className="py-2 px-3">
                          <span className={`rounded px-2 py-1 text-[10px] font-semibold ${
                            item.risk_status === "high" ? "bg-red-500/20 text-red-300" :
                            item.risk_status === "medium" ? "bg-amber-500/20 text-amber-300" :
                            "bg-emerald-500/20 text-emerald-300"
                          }`}>
                            {item.risk_label}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right text-slate-300">{formatNumber(item.volume?.delta || 0)} MT</td>
                        <td className="py-2 px-3 text-right text-slate-300">{item.timeliness?.direction_label || "-"}</td>
                        <td className="py-2 px-3 text-right text-slate-300">{formatNumber(item.quality_delta?.delta || 0)}</td>
                        <td className="py-2 px-3 text-right text-slate-300">{formatNumber(item.disputes?.delta || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(trendAnalytics.supplier_trends || []).length === 0 && (
                  <p className="text-center text-slate-500 py-6">Belum ada tren supplier pada filter ini</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {(atRiskSchedule.length > 0 || upcomingSchedule.length > 0) && (
        <Card className="glass-card border-white/10">
          <CardHeader>
            <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="font-heading text-sm sm:text-base text-white flex items-center gap-2">
                <Clock3 className="w-5 h-5 text-blue-400" />
                Monitoring Jadwal Kedatangan
              </CardTitle>
              <span className="text-xs text-slate-500">At-risk ditampilkan lebih dulu</span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="text-left py-2 text-slate-500 font-medium">Status</th>
                    <th className="text-left py-2 text-slate-500 font-medium">No Jadwal</th>
                    <th className="text-left py-2 text-slate-500 font-medium">Supplier</th>
                    <th className="text-left py-2 text-slate-500 font-medium">Moda</th>
                    <th className="text-right py-2 text-slate-500 font-medium">ETA</th>
                    <th className="text-right py-2 text-slate-500 font-medium">Tonase</th>
                  </tr>
                </thead>
                <tbody>
                  {[...atRiskSchedule.map(item => ({ ...item, _status: "At-risk" })), ...upcomingSchedule.map(item => ({ ...item, _status: "Terjadwal" }))].slice(0, 10).map((row, idx) => (
                    <tr key={`${row._status}-${row.no_jadwal || idx}-${idx}`} className="border-b border-slate-800/50">
                      <td className="py-2">
                        <span className={`rounded px-2 py-1 text-[10px] font-semibold ${row._status === "At-risk" ? "bg-red-500/10 text-red-300" : "bg-blue-500/10 text-blue-300"}`}>
                          {row._status}
                        </span>
                      </td>
                      <td className="py-2 text-white">{row.no_jadwal || "-"}</td>
                      <td className="py-2 text-slate-300 max-w-[220px] truncate">{row.supplier_name || "-"}</td>
                      <td className="py-2 text-slate-300">{row.moda || "-"}</td>
                      <td className="py-2 text-right text-slate-400">{row.time_arrival || "-"}</td>
                      <td className="py-2 text-right text-white font-mono">{formatNumber(row.tonase_po || 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Row 1: Contract Monitoring Gauge + Summary Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Contract Monitoring Gauge */}
        <Card className="glass-card border-white/10 lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="font-heading text-sm sm:text-base text-white flex items-center gap-2">
              <Gauge className="w-5 h-5 text-cyan-400" />
              Monitoring Kontrak
            </CardTitle>
          </CardHeader>
          <CardContent>
            <GaugeChart 
              percentage={advancedStats?.contract_percentage || 0} 
              label="Realisasi PO"
            />
            <div className="grid grid-cols-2 gap-2 mt-4 text-center">
              <div className="p-2 bg-slate-900/50 rounded-lg">
                <p className="text-xs text-slate-500">DS MT Total</p>
                <p className="text-sm font-bold text-cyan-400">{formatNumber(advancedStats?.total_ds_mt)}</p>
              </div>
              <div className="p-2 bg-slate-900/50 rounded-lg">
                <p className="text-xs text-slate-500">Tonase PO</p>
                <p className="text-sm font-bold text-emerald-400">{formatNumber(advancedStats?.total_tonase_po)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Summary Stats - 6 Months */}
        <div className="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          <StatCard
            title="Total Vessel (6 bln)"
            value={sixMonthsData.reduce((a, b) => a + (b.vessel || 0), 0)}
            subtitle="Shipment kapal"
            icon={Ship}
          />
          <StatCard
            title="Total Barge (6 bln)"
            value={sixMonthsData.reduce((a, b) => a + (b.barge || 0), 0)}
            subtitle="Shipment tongkang"
            icon={Anchor}
            color="blue"
          />
          <StatCard
            title="Total Trucking (6 bln)"
            value={sixMonthsData.reduce((a, b) => a + (b.trucking || 0), 0)}
            subtitle="Pengiriman truk"
            icon={Truck}
            color="amber"
          />
          <StatCard
            title="Total Biomassa (6 bln)"
            value={sixMonthsData.reduce((a, b) => a + (b.biomassa || 0), 0)}
            subtitle="Penerimaan biomassa"
            icon={Leaf}
            color="emerald"
          />
        </div>
      </div>

      {/* Row 2: 6 Months Trend + Fuel Composition */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* 6 Months Trend Chart */}
        <Card className="glass-card border-white/10 lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-heading text-sm sm:text-base text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              Tren Penerimaan 6 Bulan Terakhir
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 sm:h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sixMonthsData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0B1221',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px'
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="vessel" fill="#06B6D4" name="Vessel" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="barge" fill="#3B82F6" name="Barge" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="trucking" fill="#F59E0B" name="Trucking" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="biomassa" fill="#10B981" name="Biomassa" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* Monthly Details Table */}
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="text-left py-2 text-slate-500 font-medium">Bulan</th>
                    <th className="text-right py-2 text-slate-500 font-medium">Vessel</th>
                    <th className="text-right py-2 text-slate-500 font-medium">Barge</th>
                    <th className="text-right py-2 text-slate-500 font-medium">Trucking</th>
                    <th className="text-right py-2 text-slate-500 font-medium">Biomassa</th>
                    <th className="text-right py-2 text-slate-500 font-medium">Tonase (MT)</th>
                  </tr>
                </thead>
                <tbody>
                  {sixMonthsData.map((row, idx) => (
                    <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-900/30">
                      <td className="py-2 text-white font-medium">{row.month}</td>
                      <td className="py-2 text-right text-cyan-400">{row.vessel}</td>
                      <td className="py-2 text-right text-blue-400">{row.barge}</td>
                      <td className="py-2 text-right text-amber-400">{row.trucking}</td>
                      <td className="py-2 text-right text-emerald-400">{row.biomassa}</td>
                      <td className="py-2 text-right text-white font-mono">{formatNumber(row.total_tonase)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Fuel Composition Donut */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="font-heading text-sm sm:text-base text-white flex items-center gap-2">
              <PieChartIcon className="w-5 h-5 text-cyan-400" />
              Komposisi Bahan Bakar
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-52 sm:h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={fuelComposition.slice(0, 8)}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }) => `${name.substring(0, 10)} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {fuelComposition.slice(0, 8).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0B1221',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px'
                    }}
                    formatter={(value) => [`${formatNumber(value)} MT`, 'Tonase']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Legend */}
            <div className="grid grid-cols-2 gap-2 mt-4">
              {fuelComposition.slice(0, 6).map((item, index) => (
                <div key={item.name} className="flex items-center gap-2 p-2 bg-slate-900/50 rounded">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: CHART_COLORS[index] }}
                  />
                  <div className="min-w-0">
                    <p className="text-xs text-white truncate">{item.name}</p>
                    <p className="text-[10px] text-slate-500">{formatNumber(item.value)} MT</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 3: GCV Trend Line Chart */}
      <Card className="glass-card border-white/10">
        <CardHeader>
          <CardTitle className="font-heading text-sm sm:text-base text-white flex items-center gap-2">
            <LineChartIcon className="w-5 h-5 text-amber-400" />
            Tren Kualitas GCV (Gross Calorific Value)
            <span className="ml-auto text-xs font-normal text-slate-500">Target: 4000 Kcal/Kg</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 sm:h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={gcvTrend} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickFormatter={(val) => val?.substring(5) || ''} />
                <YAxis stroke="#64748b" fontSize={10} domain={[3000, 5000]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1221',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '12px'
                  }}
                  formatter={(value, name) => [
                    name === 'gcv_avg' ? `${value?.toFixed(0)} Kcal/Kg` : value,
                    name === 'gcv_avg' ? 'GCV Rata-rata' : name
                  ]}
                />
                <ReferenceLine y={4000} stroke="#EF4444" strokeDasharray="5 5" label={{ value: 'Target 4000', fill: '#EF4444', fontSize: 10 }} />
                <Line 
                  type="monotone" 
                  dataKey="gcv_avg" 
                  stroke="#F59E0B" 
                  strokeWidth={2}
                  dot={{ fill: '#F59E0B', strokeWidth: 0, r: 3 }}
                  activeDot={{ r: 6, fill: '#F59E0B' }}
                  name="GCV Rata-rata"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          {gcvTrend.length === 0 && (
            <p className="text-center text-slate-500 py-8">Belum ada data GCV</p>
          )}
        </CardContent>
      </Card>

      {/* Row 4: Supplier Economy + Slagging Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Supplier Economy Analysis */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="font-heading text-sm sm:text-base text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Analisis Ekonomi Supplier
              <span className="ml-auto text-[10px] font-normal text-slate-500">RP/Kcal terendah = paling efisien</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {supplierEconomy.length > 0 ? (
              <div className="h-64 sm:h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={supplierEconomy} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis type="number" stroke="#64748b" fontSize={10} tickFormatter={(v) => v.toFixed(4)} />
                    <YAxis type="category" dataKey="supplier" stroke="#64748b" fontSize={9} width={100} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0B1221',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '12px'
                      }}
                      formatter={(value) => [`${value.toFixed(6)} RP/Kcal`, 'Harga']}
                      labelFormatter={(label, payload) => payload?.[0]?.payload?.full_name || label}
                    />
                    <Bar dataKey="rp_kcal" fill="#10B981" radius={[0, 4, 4, 0]} name="RP/Kcal">
                      {supplierEconomy.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={index === 0 ? '#10B981' : index < 3 ? '#3B82F6' : '#64748b'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-center text-slate-500 py-16">Belum ada data supplier economy</p>
            )}
          </CardContent>
        </Card>

        {/* Slagging Risk Matrix */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="font-heading text-sm sm:text-base text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              Matriks Risiko Slagging & Fouling
              <span className="ml-auto text-[10px] font-normal text-slate-500">Vessel, Barge, Trucking</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {slaggingMatrix.length > 0 ? (
              <div className="overflow-x-auto max-h-80">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-[#0B1221]">
                    <tr className="border-b border-slate-800">
                      <th className="text-left py-2 px-2 text-slate-500 font-medium">Nama/Supplier</th>
                      <th className="text-center py-2 px-2 text-slate-500 font-medium">Moda</th>
                      <th className="text-center py-2 px-2 text-slate-500 font-medium">Slagging</th>
                      <th className="text-center py-2 px-2 text-slate-500 font-medium">Fouling</th>
                      <th className="text-right py-2 px-2 text-slate-500 font-medium">Tanggal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {slaggingMatrix.map((row, idx) => (
                      <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-900/30">
                        <td className="py-2 px-2">
                          <p className="text-white font-medium truncate max-w-[100px]">{row.name}</p>
                          <p className="text-[10px] text-slate-500 truncate max-w-[100px]">{row.supplier}</p>
                        </td>
                        <td className="py-2 px-2 text-center">
                          <span className={`px-2 py-1 rounded text-[10px] font-medium ${
                            row.moda === 'Vessel' ? 'bg-cyan-500/20 text-cyan-400' :
                            row.moda === 'Barge' ? 'bg-blue-500/20 text-blue-400' :
                            'bg-amber-500/20 text-amber-400'
                          }`}>
                            {row.moda}
                          </span>
                        </td>
                        <td className="py-2 px-2 text-center">
                          <span 
                            className="px-2 py-1 rounded text-[10px] font-medium"
                            style={{ 
                              backgroundColor: `${RISK_COLORS[row.slagging_risk]}20`,
                              color: RISK_COLORS[row.slagging_risk]
                            }}
                          >
                            {row.slagging_risk}
                          </span>
                        </td>
                        <td className="py-2 px-2 text-center">
                          <span 
                            className="px-2 py-1 rounded text-[10px] font-medium"
                            style={{ 
                              backgroundColor: `${RISK_COLORS[row.fouling_risk]}20`,
                              color: RISK_COLORS[row.fouling_risk]
                            }}
                          >
                            {row.fouling_risk}
                          </span>
                        </td>
                        <td className="py-2 px-2 text-right text-slate-400">{row.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center text-slate-500 py-16">Belum ada data slagging/fouling</p>
            )}
            {/* Risk Legend */}
            <div className="flex flex-wrap gap-3 mt-4 justify-center">
              {Object.entries(RISK_COLORS).filter(([k]) => k !== 'UNKNOWN').map(([label, color]) => (
                <div key={label} className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                  <span className="text-[10px] text-slate-400">{label}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 5: Quick Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          title="Total Tonase Batubara"
          value={`${formatNumber(stats?.total_tonase_batubara || 0)}`}
          subtitle="Metric Ton"
          icon={TrendingUp}
          color="blue"
        />
        <StatCard
          title="Total Tonase Biomassa"
          value={`${formatNumber(stats?.total_tonase_biomassa || 0)}`}
          subtitle="Metric Ton"
          icon={Leaf}
          color="emerald"
        />
        <StatCard
          title="Rata-rata GCV"
          value={`${(stats?.avg_gcv || 0).toFixed(0)}`}
          subtitle="Kcal/Kg ARB"
          icon={Flame}
          color="amber"
        />
        <StatCard
          title="Pencapaian Target"
          value={`${(advancedStats?.contract_percentage || 0).toFixed(1)}%`}
          subtitle="Realisasi vs PO"
          icon={Target}
          color="cyan"
        />
      </div>
    </div>
  );
};

export default Dashboard;
