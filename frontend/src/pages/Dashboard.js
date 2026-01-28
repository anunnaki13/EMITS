import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Ship,
  Anchor,
  Truck,
  Leaf,
  TrendingUp,
  Flame,
  Activity,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight
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
  Line
} from "recharts";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const StatCard = ({ title, value, subtitle, icon: Icon, trend, trendUp, color = "cyan" }) => (
  <Card className="glass-card border-white/10 hover:border-cyan-500/30">
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-xs font-mono uppercase tracking-wider text-slate-500">{title}</p>
          <p className="font-heading text-3xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
          {trend && (
            <div className={`flex items-center gap-1 text-sm ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
              {trendUp ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
              <span>{trend}</span>
            </div>
          )}
        </div>
        <div className={`w-12 h-12 rounded-xl bg-${color}-500/10 flex items-center justify-center`}>
          <Icon className={`w-6 h-6 text-${color}-400`} />
        </div>
      </div>
    </CardContent>
  </Card>
);

const CHART_COLORS = ['#06B6D4', '#3B82F6', '#F59E0B', '#10B981', '#EF4444'];

const Dashboard = () => {
  const { getAuthHeader } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/stats`, {
        headers: getAuthHeader()
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
      toast.error("Gagal memuat statistik");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-900/50 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-80 bg-slate-900/50 rounded-xl" />
          <div className="h-80 bg-slate-900/50 rounded-xl" />
        </div>
      </div>
    );
  }

  const pieData = [
    { name: 'Vessel', value: stats?.total_vessel || 0 },
    { name: 'Barge', value: stats?.total_barge || 0 },
    { name: 'Trucking', value: stats?.total_trucking || 0 },
    { name: 'Biomassa', value: stats?.total_biomassa || 0 },
  ];

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      {/* Header */}
      <div>
        <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1">Ringkasan penerimaan bahan bakar UP Tenayan</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Vessel"
          value={stats?.total_vessel || 0}
          subtitle="Shipment kapal"
          icon={Ship}
          trend="+12% bulan ini"
          trendUp={true}
        />
        <StatCard
          title="Total Barge"
          value={stats?.total_barge || 0}
          subtitle="Shipment tongkang"
          icon={Anchor}
          trend="+8% bulan ini"
          trendUp={true}
        />
        <StatCard
          title="Total Trucking"
          value={stats?.total_trucking || 0}
          subtitle="Pengiriman truk"
          icon={Truck}
          trend="+5% bulan ini"
          trendUp={true}
        />
        <StatCard
          title="Total Biomassa"
          value={stats?.total_biomassa || 0}
          subtitle="Penerimaan biomassa"
          icon={Leaf}
          trend="+15% bulan ini"
          trendUp={true}
        />
      </div>

      {/* Second Row Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Total Tonase Batubara"
          value={`${((stats?.total_tonase_batubara || 0) / 1000).toFixed(1)}K`}
          subtitle="Metric Ton"
          icon={TrendingUp}
          color="blue"
        />
        <StatCard
          title="Total Tonase Biomassa"
          value={`${((stats?.total_tonase_biomassa || 0) / 1000).toFixed(1)}K`}
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
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Trend Chart */}
        <Card className="glass-card border-white/10 lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-heading text-lg text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              Tren Penerimaan Bulanan
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.monthly_trend || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0B1221',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                  />
                  <Bar dataKey="vessel" fill="#06B6D4" name="Vessel" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="barge" fill="#3B82F6" name="Barge" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="trucking" fill="#F59E0B" name="Trucking" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="biomassa" fill="#10B981" name="Biomassa" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Distribution Pie Chart */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="font-heading text-lg text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              Distribusi Shipment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0B1221',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              {/* Legend */}
              <div className="flex flex-wrap justify-center gap-4 mt-4">
                {pieData.map((item, index) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: CHART_COLORS[index] }}
                    />
                    <span className="text-xs text-slate-400">{item.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Shipments & Supplier Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Shipments */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="font-heading text-lg text-white">Shipment Terbaru</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats?.recent_shipments?.length > 0 ? (
                stats.recent_shipments.map((shipment, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        shipment.type === 'vessel' ? 'bg-cyan-500/20' : 'bg-blue-500/20'
                      }`}>
                        {shipment.type === 'vessel' ? (
                          <Ship className="w-5 h-5 text-cyan-400" />
                        ) : (
                          <Anchor className="w-5 h-5 text-blue-400" />
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{shipment.name || 'N/A'}</p>
                        <p className="text-xs text-slate-500">{shipment.code}</p>
                      </div>
                    </div>
                    <span className="text-xs text-slate-500">
                      {new Date(shipment.date).toLocaleDateString('id-ID')}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-center text-slate-500 py-8">Belum ada data shipment</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Top Suppliers */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="font-heading text-lg text-white">Top Supplier</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats?.supplier_stats?.length > 0 ? (
                stats.supplier_stats.slice(0, 5).map((supplier, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-white truncate max-w-[200px]">
                        {supplier.supplier}
                      </span>
                      <span className="text-sm font-mono text-cyan-400">
                        {supplier.count} shipment
                      </span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                        style={{
                          width: `${Math.min((supplier.tonase / (stats.total_tonase_batubara || 1)) * 100, 100)}%`
                        }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-slate-500 py-8">Belum ada data supplier</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
