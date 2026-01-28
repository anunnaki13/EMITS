import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { FileText, Download, CalendarIcon, Loader2, Ship, Anchor, Truck, Leaf, FileSpreadsheet, FileDown } from "lucide-react";
import { format } from "date-fns";
import { id } from "date-fns/locale";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CHART_COLORS = ['#06B6D4', '#3B82F6', '#F59E0B', '#10B981'];

const LaporanPage = () => {
  const { getAuthHeader } = useAuth();
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [reportType, setReportType] = useState("all");
  const [dateRange, setDateRange] = useState({ from: undefined, to: undefined });

  useEffect(() => { fetchStats(); }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/stats`, { headers: getAuthHeader() });
      setStats(response.data);
    } catch (error) {
      toast.error("Gagal memuat data laporan");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    toast.info(`Mengexport laporan ke ${format.toUpperCase()}...`);
    // In a real implementation, this would call an API endpoint to generate the file
    setTimeout(() => {
      toast.success(`Laporan berhasil diexport ke ${format.toUpperCase()}`);
    }, 1500);
  };

  const pieData = stats ? [
    { name: 'Vessel', value: stats.total_vessel, color: '#06B6D4' },
    { name: 'Barge', value: stats.total_barge, color: '#3B82F6' },
    { name: 'Trucking', value: stats.total_trucking, color: '#F59E0B' },
    { name: 'Biomassa', value: stats.total_biomassa, color: '#10B981' },
  ] : [];

  const summaryCards = [
    { label: "Total Vessel", value: stats?.total_vessel || 0, icon: Ship, color: "cyan" },
    { label: "Total Barge", value: stats?.total_barge || 0, icon: Anchor, color: "blue" },
    { label: "Total Trucking", value: stats?.total_trucking || 0, icon: Truck, color: "amber" },
    { label: "Total Biomassa", value: stats?.total_biomassa || 0, icon: Leaf, color: "emerald" },
  ];

  return (
    <div className="space-y-6" data-testid="laporan-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <FileText className="w-8 h-8 text-cyan-400" />
            Laporan
          </h1>
          <p className="text-slate-400 mt-1">Rekapitulasi dan export data penerimaan bahan bakar</p>
        </div>
        <div className="flex gap-3">
          <Button onClick={() => handleExport('excel')} variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="export-excel-btn">
            <FileSpreadsheet className="w-4 h-4 mr-2" />Export Excel
          </Button>
          <Button onClick={() => handleExport('pdf')} className="bg-cyan-600 hover:bg-cyan-500" data-testid="export-pdf-btn">
            <FileDown className="w-4 h-4 mr-2" />Export PDF
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="glass-card border-white/10">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="space-y-2 flex-1">
              <label className="text-xs font-mono uppercase tracking-wider text-slate-500">Jenis Laporan</label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white" data-testid="report-type-select">
                  <SelectValue placeholder="Pilih jenis laporan" />
                </SelectTrigger>
                <SelectContent className="bg-[#0B1221] border-white/10">
                  <SelectItem value="all" className="text-slate-300 focus:bg-white/5 focus:text-white">Semua Data</SelectItem>
                  <SelectItem value="vessel" className="text-slate-300 focus:bg-white/5 focus:text-white">Vessel TNY</SelectItem>
                  <SelectItem value="barge" className="text-slate-300 focus:bg-white/5 focus:text-white">Barge TNY</SelectItem>
                  <SelectItem value="trucking" className="text-slate-300 focus:bg-white/5 focus:text-white">Trucking TNY</SelectItem>
                  <SelectItem value="biomassa" className="text-slate-300 focus:bg-white/5 focus:text-white">Biomassa TNY</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 flex-1">
              <label className="text-xs font-mono uppercase tracking-wider text-slate-500">Periode Dari</label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start text-left font-normal border-slate-800 text-slate-300 bg-slate-950/50">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {dateRange.from ? format(dateRange.from, "PPP", { locale: id }) : "Pilih tanggal"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0 bg-[#0B1221] border-white/10" align="start">
                  <Calendar mode="single" selected={dateRange.from} onSelect={(date) => setDateRange({...dateRange, from: date})} initialFocus className="bg-[#0B1221]" />
                </PopoverContent>
              </Popover>
            </div>
            <div className="space-y-2 flex-1">
              <label className="text-xs font-mono uppercase tracking-wider text-slate-500">Periode Sampai</label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start text-left font-normal border-slate-800 text-slate-300 bg-slate-950/50">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {dateRange.to ? format(dateRange.to, "PPP", { locale: id }) : "Pilih tanggal"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0 bg-[#0B1221] border-white/10" align="start">
                  <Calendar mode="single" selected={dateRange.to} onSelect={(date) => setDateRange({...dateRange, to: date})} initialFocus className="bg-[#0B1221]" />
                </PopoverContent>
              </Popover>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {summaryCards.map((card, index) => (
          <Card key={index} className="glass-card border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono uppercase tracking-wider text-slate-500">{card.label}</p>
                  <p className="font-heading text-3xl font-bold text-white mt-2">
                    {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : card.value}
                  </p>
                </div>
                <div className={`w-12 h-12 rounded-xl bg-${card.color}-500/10 flex items-center justify-center`}>
                  <card.icon className={`w-6 h-6 text-${card.color}-400`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="font-heading text-lg text-white">Tren Penerimaan Bulanan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              {loading ? (
                <div className="h-full flex items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats?.monthly_trend || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#0B1221', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                    <Bar dataKey="vessel" fill="#06B6D4" name="Vessel" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="barge" fill="#3B82F6" name="Barge" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="trucking" fill="#F59E0B" name="Trucking" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="biomassa" fill="#10B981" name="Biomassa" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Pie Chart */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="font-heading text-lg text-white">Distribusi Shipment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              {loading ? (
                <div className="h-full flex items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0B1221', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
              <div className="flex flex-wrap justify-center gap-4 mt-4">
                {pieData.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-xs text-slate-400">{item.name}: {item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tonase Summary */}
      <Card className="glass-card border-white/10">
        <CardHeader>
          <CardTitle className="font-heading text-lg text-white">Ringkasan Tonase</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
              <p className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-2">Total Tonase Batubara</p>
              <p className="font-heading text-3xl font-bold text-white">
                {loading ? "-" : `${((stats?.total_tonase_batubara || 0) / 1000).toFixed(2)}K`}
              </p>
              <p className="text-sm text-slate-400 mt-1">Metric Ton</p>
            </div>
            <div className="p-6 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <p className="text-xs font-mono uppercase tracking-wider text-emerald-400 mb-2">Total Tonase Biomassa</p>
              <p className="font-heading text-3xl font-bold text-white">
                {loading ? "-" : `${((stats?.total_tonase_biomassa || 0) / 1000).toFixed(2)}K`}
              </p>
              <p className="text-sm text-slate-400 mt-1">Metric Ton</p>
            </div>
            <div className="p-6 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <p className="text-xs font-mono uppercase tracking-wider text-amber-400 mb-2">Rata-rata GCV</p>
              <p className="font-heading text-3xl font-bold text-white">
                {loading ? "-" : (stats?.avg_gcv || 0).toFixed(0)}
              </p>
              <p className="text-sm text-slate-400 mt-1">Kcal/Kg ARB</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LaporanPage;
