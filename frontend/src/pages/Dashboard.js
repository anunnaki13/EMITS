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
  Filter
} from "lucide-react";
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

const StatCard = ({ title, value, subtitle, icon: Icon, color = "cyan" }) => (
  <Card className="glass-card border-white/10 hover:border-cyan-500/30">
    <CardContent className="p-4 sm:p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-1 sm:space-y-2">
          <p className="text-[10px] sm:text-xs font-mono uppercase tracking-wider text-slate-500">{title}</p>
          <p className="font-heading text-xl sm:text-2xl lg:text-3xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-xs sm:text-sm text-slate-400">{subtitle}</p>}
        </div>
        <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-${color}-500/10 flex items-center justify-center`}>
          <Icon className={`w-5 h-5 sm:w-6 sm:h-6 text-${color}-400`} />
        </div>
      </div>
    </CardContent>
  </Card>
);

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
  const [stats, setStats] = useState(null);
  const [advancedStats, setAdvancedStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState("all");
  const [selectedModa, setSelectedModa] = useState("all");

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, advancedRes] = await Promise.all([
        axios.get(`${API_URL}/api/dashboard/stats`, { headers: getAuthHeader() }),
        axios.get(`${API_URL}/api/dashboard/advanced`, { headers: getAuthHeader() })
      ]);
      setStats(statsRes.data);
      setAdvancedStats(advancedRes.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
      toast.error("Gagal memuat statistik");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeader]);

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

  return (
    <div className="space-y-6 sm:space-y-8" data-testid="dashboard-page">
      {/* Header with Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-xl sm:text-2xl lg:text-3xl text-white">
            Dashboard Ringkasan Penerimaan Bahan Bakar
          </h1>
          <p className="text-slate-400 mt-1 text-sm sm:text-base">
            Data 6 bulan terakhir - UP Tenayan
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Select value={selectedModa} onValueChange={setSelectedModa}>
            <SelectTrigger className="w-[140px] bg-slate-900/50 border-slate-700 text-white" data-testid="filter-moda">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Moda" />
            </SelectTrigger>
            <SelectContent className="bg-[#0B1221] border-slate-800">
              <SelectItem value="all" className="text-slate-300">Semua Moda</SelectItem>
              {advancedStats?.available_moda?.map(m => (
                <SelectItem key={m} value={m} className="text-slate-300">{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

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
            )}}
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
