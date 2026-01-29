import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from "recharts";
import {
  Upload,
  PlusCircle,
  Download,
  Package,
  TrendingUp,
  Calendar,
  AlertCircle,
  Trash2
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Supplier list based on the NEW Excel file
const SUPPLIERS = [
  "BUMI_BERDIKARI_SENTOSA_LRC",
  "GLOBAL_ENERGI_LESTARI_LRC",
  "GLOBAL_ENERGI_LESTARI_MRC",
  "RIAU_MITRA_BINA_ENERGI_TEBO_LRC",
  "RIAU_MITRA_BINA_ENERGI_JPC_LRC",
  "TIGA_DAYA_ENERGI_LRC",
  "KONS_KARYA_BUMI_BARATAMA_MANDIANGIN",
  "BARA_ENERGI_LRC",
  "KONSORSIUM_ESB_BSL_MRC",
  "KUTAI_ENERGI_LRC",
  "MANDIRI_INTIPERKASA_MRC",
  "BUKIT_ASAM_MRC",
  "TONGKANG_SUMBER_PANCA_ENERGI_LRC",
  "TRIDAYA_COAL_RESOURCES_LRC"
];

const SUPPLIER_COLORS = {
  "BUMI_BERDIKARI_SENTOSA_LRC": "#06b6d4",
  "GLOBAL_ENERGI_LESTARI_LRC": "#3b82f6",
  "GLOBAL_ENERGI_LESTARI_MRC": "#8b5cf6",
  "RIAU_MITRA_BINA_ENERGI_TEBO_LRC": "#ec4899",
  "RIAU_MITRA_BINA_ENERGI_JPC_LRC": "#f59e0b",
  "TIGA_DAYA_ENERGI_LRC": "#10b981",
  "KONS_KARYA_BUMI_BARATAMA_MANDIANGIN": "#ef4444",
  "BARA_ENERGI_LRC": "#6366f1",
  "KONSORSIUM_ESB_BSL_MRC": "#14b8a6",
  "KUTAI_ENERGI_LRC": "#f97316",
  "MANDIRI_INTIPERKASA_MRC": "#84cc16",
  "BUKIT_ASAM_MRC": "#a855f7",
  "TONGKANG_SUMBER_PANCA_ENERGI_LRC": "#eab308",
  "TRIDAYA_COAL_RESOURCES_LRC": "#22d3ee"
};

const SumberPemakaianPage = () => {
  const { getAuthHeader } = useAuth();
  const [loading, setLoading] = useState(true);
  const [pemakaianData, setPemakaianData] = useState([]);
  const [recent30Days, setRecent30Days] = useState([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [inputDialogOpen, setInputDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  
  // Form states for manual input
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0]);
  const [formStockAwal, setFormStockAwal] = useState("");
  const [formSupplier, setFormSupplier] = useState("");
  const [formUnit1A, setFormUnit1A] = useState("");
  const [formUnit1B, setFormUnit1B] = useState("");
  const [formUnit1C, setFormUnit1C] = useState("");
  const [formUnit2A, setFormUnit2A] = useState("");
  const [formUnit2B, setFormUnit2B] = useState("");
  const [formUnit2C, setFormUnit2C] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (filterStartDate = null, filterEndDate = null) => {
    setLoading(true);
    try {
      const params = {};
      if (filterStartDate) params.start_date = filterStartDate;
      if (filterEndDate) params.end_date = filterEndDate;

      const response = await axios.get(`${API_URL}/api/sumber-pemakaian`, {
        headers: getAuthHeader(),
        params
      });

      setPemakaianData(response.data.data);
      setRecent30Days(response.data.recent_30_days);
    } catch (error) {
      toast.error("Gagal mengambil data pemakaian");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = () => {
    if (startDate && endDate && startDate > endDate) {
      toast.error("Tanggal mulai tidak boleh lebih besar dari tanggal akhir");
      return;
    }
    fetchData(startDate, endDate);
  };

  const handleResetFilter = () => {
    setStartDate("");
    setEndDate("");
    fetchData();
  };

  const handleManualInput = async (e) => {
    e.preventDefault();

    if (!formSupplier) {
      toast.error("Pilih supplier terlebih dahulu");
      return;
    }

    const suppliers = {
      [formSupplier]: {
        UNIT1: {
          A: parseFloat(formUnit1A) || 0,
          B: parseFloat(formUnit1B) || 0,
          C: parseFloat(formUnit1C) || 0
        },
        UNIT2: {
          A: parseFloat(formUnit2A) || 0,
          B: parseFloat(formUnit2B) || 0,
          C: parseFloat(formUnit2C) || 0
        }
      }
    };

    try {
      await axios.post(`${API_URL}/api/sumber-pemakaian/entry`, {
        date: formDate,
        stock_awal: parseFloat(formStockAwal) || 0,
        suppliers
      }, { headers: getAuthHeader() });

      toast.success("Data berhasil disimpan");
      setInputDialogOpen(false);
      
      // Reset form
      setFormDate(new Date().toISOString().split('T')[0]);
      setFormStockAwal("");
      setFormSupplier("");
      setFormUnit1A("");
      setFormUnit1B("");
      setFormUnit1C("");
      setFormUnit2A("");
      setFormUnit2B("");
      setFormUnit2C("");
      
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menyimpan data");
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      toast.error("Pilih file Excel terlebih dahulu");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(
        `${API_URL}/api/sumber-pemakaian/upload`,
        formData,
        {
          headers: {
            ...getAuthHeader(),
            "Content-Type": "multipart/form-data"
          }
        }
      );

      toast.success(response.data.message);
      setUploadDialogOpen(false);
      setSelectedFile(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal mengupload file");
    }
  };

  const handleExportPDF = () => {
    toast.info("Fitur Export PDF sedang dalam pengembangan");
  };

  const handleDeleteAll = async () => {
    if (!window.confirm("⚠️ PERINGATAN!\n\nAnda yakin ingin menghapus SEMUA data Sumber Pemakaian?\nTindakan ini tidak dapat dibatalkan!")) {
      return;
    }

    if (!window.confirm("Konfirmasi sekali lagi: Hapus SEMUA data?")) {
      return;
    }

    try {
      const response = await axios.delete(`${API_URL}/api/sumber-pemakaian`, {
        headers: getAuthHeader()
      });

      toast.success(response.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menghapus data");
    }
  };

  // Prepare data for Area Chart (Stock Awal trend - last 30 days ONLY)
  const areaChartData = recent30Days.map(item => ({
    date: new Date(item.date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }),
    stock: item.stock_awal
  }));

  // Get today's pemakaian - SINGLE VALUE
  const todayDate = new Date().toISOString().split('T')[0];
  let todayData = pemakaianData.find(d => d.date === todayDate);
  
  // If today's data doesn't exist or has no pemakaian, find the most recent date with pemakaian
  if (!todayData || todayData.total_pemakaian === 0) {
    for (let item of pemakaianData) {
      if (item.total_pemakaian > 0) {
        todayData = item;
        break;
      }
    }
  }
  
  if (!todayData) {
    todayData = pemakaianData[0];
  }
  
  const totalPemakaianToday = todayData ? todayData.total_pemakaian : 0;
  const displayDate = todayData ? todayData.date : todayDate;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <Package className="w-6 h-6 text-white" />
            </div>
            Sumber Pemakaian
          </h1>
          <p className="text-slate-400 mt-1">Monitoring pemakaian batubara harian per unit</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-cyan-600 hover:bg-cyan-500">
                <Upload className="w-4 h-4 mr-2" />
                Upload Excel
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-slate-800">
              <DialogHeader>
                <DialogTitle className="text-white">Upload File Excel</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label className="text-slate-300">Pilih File Excel</Label>
                  <Input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setSelectedFile(e.target.files[0])}
                    className="bg-slate-800 border-slate-700 text-white mt-2"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Format: Sumber Pemakaian.xlsx
                  </p>
                </div>
                <Button
                  onClick={handleFileUpload}
                  className="w-full bg-cyan-600 hover:bg-cyan-500"
                >
                  Upload & Proses
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={inputDialogOpen} onOpenChange={setInputDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-emerald-600 hover:bg-emerald-500">
                <PlusCircle className="w-4 h-4 mr-2" />
                Input Harian
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-slate-800">
              <DialogHeader>
                <DialogTitle className="text-white">Input Data Harian</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleManualInput} className="space-y-4">
                <div>
                  <Label className="text-slate-300">Tanggal</Label>
                  <Input
                    type="date"
                    value={formDate}
                    onChange={(e) => setFormDate(e.target.value)}
                    className="bg-slate-800 border-slate-700 text-white"
                    required
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Stock Awal (MT)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formStockAwal}
                    onChange={(e) => setFormStockAwal(e.target.value)}
                    placeholder="0.00"
                    className="bg-slate-800 border-slate-700 text-white"
                    required
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Pilih Supplier</Label>
                  <select
                    value={formSupplier}
                    onChange={(e) => setFormSupplier(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-white rounded-md px-3 py-2"
                    required
                  >
                    <option value="">-- Pilih Supplier --</option>
                    {SUPPLIERS.map(supplier => (
                      <option key={supplier} value={supplier}>
                        {supplier.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-300 mb-2 block">Unit 1</Label>
                    <div className="space-y-2">
                      <Input
                        type="number"
                        step="0.01"
                        value={formUnit1A}
                        onChange={(e) => setFormUnit1A(e.target.value)}
                        placeholder="Zone A (MT)"
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                      <Input
                        type="number"
                        step="0.01"
                        value={formUnit1B}
                        onChange={(e) => setFormUnit1B(e.target.value)}
                        placeholder="Zone B (MT)"
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                      <Input
                        type="number"
                        step="0.01"
                        value={formUnit1C}
                        onChange={(e) => setFormUnit1C(e.target.value)}
                        placeholder="Zone C (MT)"
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300 mb-2 block">Unit 2</Label>
                    <div className="space-y-2">
                      <Input
                        type="number"
                        step="0.01"
                        value={formUnit2A}
                        onChange={(e) => setFormUnit2A(e.target.value)}
                        placeholder="Zone A (MT)"
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                      <Input
                        type="number"
                        step="0.01"
                        value={formUnit2B}
                        onChange={(e) => setFormUnit2B(e.target.value)}
                        placeholder="Zone B (MT)"
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                      <Input
                        type="number"
                        step="0.01"
                        value={formUnit2C}
                        onChange={(e) => setFormUnit2C(e.target.value)}
                        placeholder="Zone C (MT)"
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                    </div>
                  </div>
                </div>
                <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-500">
                  Simpan Data
                </Button>
              </form>
            </DialogContent>
          </Dialog>

          <Button
            onClick={handleExportPDF}
            variant="outline"
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
          >
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>

          {pemakaianData.length > 0 && (
            <Button
              onClick={handleDeleteAll}
              variant="outline"
              className="border-red-500/50 text-red-400 hover:bg-red-500/10"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Hapus Semua
            </Button>
          )}
        </div>
      </div>

      {/* No Delivery Alert */}
      {noDeliveryToday && (
        <Card className="glass-card border-red-500/30 bg-red-500/10">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div>
              <p className="text-red-400 font-semibold">No Delivery</p>
              <p className="text-slate-400 text-sm">Tidak ada penerimaan batubara hari ini</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Area Chart - Stock Awal Trend */}
        <Card className="glass-card border-white/10 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Tren Stock Awal (30 Hari Terakhir)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-64 flex items-center justify-center">
                <p className="text-slate-500">Loading...</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={areaChartData}>
                  <defs>
                    <linearGradient id="stockGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#94a3b8"
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    style={{ fontSize: '12px' }}
                    tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    formatter={(value) => [`${value.toLocaleString()} MT`, 'Stock Awal']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="stock" 
                    stroke="#10b981" 
                    fillOpacity={1} 
                    fill="url(#stockGradient)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Total Stock Today - Single Value Card */}
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Package className="w-5 h-5 text-red-400" />
              Total Pemakaian Hari Ini
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-64 flex items-center justify-center">
                <p className="text-slate-500">Loading...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64">
                <p className="text-6xl font-bold text-red-400 mb-4">
                  {(totalPemakaianToday / 1000000).toFixed(2)}M
                </p>
                <p className="text-slate-400 text-sm">Metric Tons (MT) - Pemakaian</p>
                <p className="text-slate-500 text-xs mt-2">
                  {new Date(displayDate).toLocaleDateString('id-ID', { 
                    day: 'numeric', 
                    month: 'long', 
                    year: 'numeric' 
                  })}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Zonation Bar Chart - TODAY ONLY with Gradient */}
        <Card className="glass-card border-white/10 lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Package className="w-5 h-5 text-amber-400" />
              Zonasi Penerimaan Harian (Coalyard A, B, C)
            </CardTitle>
            <p className="text-xs text-slate-500 mt-1">
              Total penerimaan dari semua supplier berdasarkan zona peletakan di coalyard - Data terakhir: {new Date(displayDate).toLocaleDateString('id-ID')}
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-80 flex items-center justify-center">
                <p className="text-slate-500">Loading...</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={zonationChartData}>
                  <defs>
                    {/* Gradient Zona A - Green to Yellow to Red */}
                    <linearGradient id="colorA" x1="0" y1="1" x2="0" y2="0">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={1}/>
                      <stop offset="50%" stopColor="#eab308" stopOpacity={1}/>
                      <stop offset="100%" stopColor="#ef4444" stopOpacity={1}/>
                    </linearGradient>
                    {/* Gradient Zona B */}
                    <linearGradient id="colorB" x1="0" y1="1" x2="0" y2="0">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={1}/>
                      <stop offset="50%" stopColor="#eab308" stopOpacity={1}/>
                      <stop offset="100%" stopColor="#ef4444" stopOpacity={1}/>
                    </linearGradient>
                    {/* Gradient Zona C */}
                    <linearGradient id="colorC" x1="0" y1="1" x2="0" y2="0">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={1}/>
                      <stop offset="50%" stopColor="#eab308" stopOpacity={1}/>
                      <stop offset="100%" stopColor="#ef4444" stopOpacity={1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="zone" 
                    stroke="#94a3b8"
                    style={{ fontSize: '14px', fontWeight: 600 }}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    style={{ fontSize: '12px' }}
                    tickFormatter={(value) => `${(value / 1000).toFixed(0)}K MT`}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    formatter={(value) => [`${value.toLocaleString()} MT`, 'Total']}
                  />
                  <Bar 
                    dataKey="value" 
                    radius={[12, 12, 0, 0]}
                    maxBarSize={150}
                  >
                    {zonationChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Data Table with Freeze Header */}
      <Card className="glass-card border-white/10">
        <CardHeader className="border-b border-slate-800">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-400" />
              Data Stock & Penerimaan
            </CardTitle>
            <div className="flex gap-2 items-center">
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white w-40"
                placeholder="Dari"
              />
              <span className="text-slate-500">-</span>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white w-40"
                placeholder="Sampai"
              />
              <Button onClick={handleFilter} size="sm" className="bg-blue-600 hover:bg-blue-500">
                Filter
              </Button>
              <Button onClick={handleResetFilter} size="sm" variant="outline" className="border-slate-700">
                Reset
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/80 sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800">
                    Tanggal
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800">
                    Stock Awal (MT)
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800" colSpan={3}>
                    Suppliers (A / B / C)
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800">
                    Total Penerimaan
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                      Loading data...
                    </td>
                  </tr>
                ) : pemakaianData.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                      Tidak ada data
                    </td>
                  </tr>
                ) : (
                  pemakaianData.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-slate-300">
                        {new Date(item.date).toLocaleDateString('id-ID')}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-300 font-mono">
                        {item.stock_awal.toLocaleString()}
                      </td>
                      <td colSpan={3} className="px-4 py-3">
                        <div className="space-y-1 text-xs">
                          {Object.entries(item.suppliers || {}).map(([supplier, zones]) => {
                            const total = zones.A + zones.B + zones.C;
                            if (total === 0) return null;
                            return (
                              <div key={supplier} className="flex justify-between text-slate-400">
                                <span className="truncate mr-2">{supplier.replace(/_/g, ' ').substring(0, 25)}</span>
                                <span className="font-mono">{zones.A} / {zones.B} / {zones.C}</span>
                              </div>
                            );
                          })}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-emerald-400 font-mono font-semibold">
                        {item.total_penerimaan.toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SumberPemakaianPage;
