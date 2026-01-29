import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Upload,
  PlusCircle,
  Download,
  Flame,
  TrendingUp,
  Calendar,
  ChevronDown,
  ChevronRight,
  Trash2,
  Award
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SUPPLIERS = [
  "RIAU_MITRA_BINA_ENERGI_JPC_LRC",
  "TIGA_DAYA_ENERGI_LRC",
  "KONS_KARYA_BUMI_BARATAMA_MANDIANGIN_BARA_ENERGI_LRC",
  "BARA_ENERGI_LRC",
  "KONSORSIUM_ESB_BSL_MRC",
  "KUTAI_ENERGI_LRC",
  "MANDIRI_INTIPERKASA_MRC",
  "BUKIT_ASAM_MRC",
  "TONGKANG_TIGA_DAYA_ENERGI_LRC"
];

const SumberPemakaianPage = () => {
  const { getAuthHeader } = useAuth();
  const [loading, setLoading] = useState(true);
  const [pemakaianData, setPemakaianData] = useState([]);
  const [stats, setStats] = useState({
    total_burn_today: 0,
    unit1_load: 0,
    unit2_load: 0,
    dominant_source: "N/A",
    latest_date: null
  });
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [inputDialogOpen, setInputDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});
  
  // Form states - 3 step input
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0]);
  const [formStockAwal, setFormStockAwal] = useState("");
  const [formUnit, setFormUnit] = useState("UNIT1");
  const [formSupplier, setFormSupplier] = useState("");
  const [formZone, setFormZone] = useState("A");
  const [formAmount, setFormAmount] = useState("");

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
      setStats(response.data.stats);
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
        [formUnit]: {
          [formZone]: parseFloat(formAmount) || 0,
          ...(formZone !== "A" && { A: 0 }),
          ...(formZone !== "B" && { B: 0 }),
          ...(formZone !== "C" && { C: 0 })
        },
        [formUnit === "UNIT1" ? "UNIT2" : "UNIT1"]: {
          A: 0,
          B: 0,
          C: 0
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
      setFormUnit("UNIT1");
      setFormSupplier("");
      setFormZone("A");
      setFormAmount("");
      
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

  const toggleRow = (index) => {
    setExpandedRows(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const calculateStockAkhir = (stockAwal, totalPemakaian) => {
    return stockAwal - totalPemakaian;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center">
              <Flame className="w-6 h-6 text-white" />
            </div>
            Total Pemakaian Batubara
          </h1>
          <p className="text-slate-400 mt-1">
            Power Plant Consumption Tracker - Unit 1 & Unit 2
            {stats.latest_date && (
              <span className="ml-2 text-cyan-400">
                | Latest Entry: {new Date(stats.latest_date).toLocaleDateString('id-ID')}
              </span>
            )}
          </p>
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
                Tambah Pemakaian
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-slate-800">
              <DialogHeader>
                <DialogTitle className="text-white">Input Pemakaian Baru (3 Langkah)</DialogTitle>
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

                {/* Step 1: Pilih Unit */}
                <div className="space-y-2">
                  <Label className="text-slate-300 font-semibold">Langkah 1: Pilih Unit</Label>
                  <RadioGroup value={formUnit} onValueChange={setFormUnit}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="UNIT1" id="unit1" className="border-white text-white" />
                      <Label htmlFor="unit1" className="text-slate-300 cursor-pointer">Unit 1</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="UNIT2" id="unit2" className="border-white text-white" />
                      <Label htmlFor="unit2" className="text-slate-300 cursor-pointer">Unit 2</Label>
                    </div>
                  </RadioGroup>
                </div>

                {/* Step 2: Pilih Supplier */}
                <div>
                  <Label className="text-slate-300 font-semibold">Langkah 2: Pilih Sumber</Label>
                  <select
                    value={formSupplier}
                    onChange={(e) => setFormSupplier(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-white rounded-md px-3 py-2 mt-2"
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

                {/* Step 3: Pilih Zonasi & Jumlah */}
                <div className="space-y-2">
                  <Label className="text-slate-300 font-semibold">Langkah 3: Zonasi & Jumlah</Label>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-slate-300 text-sm">Zonasi</Label>
                      <select
                        value={formZone}
                        onChange={(e) => setFormZone(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 text-white rounded-md px-3 py-2 mt-1"
                        required
                      >
                        <option value="A">Zona A</option>
                        <option value="B">Zona B</option>
                        <option value="C">Zona C</option>
                      </select>
                    </div>
                    <div>
                      <Label className="text-slate-300 text-sm">Jumlah (MT)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formAmount}
                        onChange={(e) => setFormAmount(e.target.value)}
                        placeholder="0.00"
                        className="bg-slate-800 border-slate-700 text-white mt-1"
                        required
                      />
                    </div>
                  </div>
                </div>

                <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-500">
                  Simpan Pemakaian
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

      {/* Dashboard Ringkasan - Top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-card border-red-500/30 bg-gradient-to-br from-red-500/10 to-orange-500/10">
          <CardContent className="p-6">
            {stats.total_burn_today === 0 && !stats.latest_date ? (
              <div className="text-center py-4">
                <Flame className="w-12 h-12 text-slate-600 mx-auto mb-2 opacity-30" />
                <p className="text-slate-500 text-sm">Silakan Upload Excel atau Input Manual</p>
                <p className="text-slate-600 text-xs mt-1">untuk melihat Statistik</p>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Total Burn</p>
                  <p className="text-3xl font-bold text-red-400 mt-2">
                    {(stats.total_burn_today / 1000).toFixed(1)}K
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Metric Tons</p>
                </div>
                <Flame className="w-12 h-12 text-red-400 opacity-50" />
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card border-blue-500/30 bg-gradient-to-br from-blue-500/10 to-cyan-500/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Unit 1 Load</p>
                <p className="text-3xl font-bold text-blue-400 mt-2">
                  {(stats.unit1_load / 1000).toFixed(1)}K
                </p>
                <p className="text-xs text-slate-500 mt-1">Metric Tons</p>
              </div>
              <TrendingUp className="w-12 h-12 text-blue-400 opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-pink-500/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Unit 2 Load</p>
                <p className="text-3xl font-bold text-purple-400 mt-2">
                  {(stats.unit2_load / 1000).toFixed(1)}K
                </p>
                <p className="text-xs text-slate-500 mt-1">Metric Tons</p>
              </div>
              <TrendingUp className="w-12 h-12 text-purple-400 opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 to-teal-500/10">
          <CardContent className="p-6">
            {stats.dominant_source === "N/A" && !stats.latest_date ? (
              <div className="text-center py-4">
                <Award className="w-12 h-12 text-slate-600 mx-auto mb-2 opacity-30" />
                <p className="text-slate-500 text-sm">Tidak ada data</p>
                <p className="text-slate-600 text-xs mt-1">Belum tersedia</p>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Dominant Source</p>
                  <p className="text-lg font-bold text-emerald-400 mt-2 truncate">
                    {stats.dominant_source}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Top Supplier</p>
                </div>
                <Award className="w-12 h-12 text-emerald-400 opacity-50" />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Compact Table with Expandable Rows */}
      <Card className="glass-card border-white/10">
        <CardHeader className="border-b border-slate-800">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Calendar className="w-5 h-5 text-orange-400" />
              Data Pemakaian Batubara
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
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/80 sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800 w-12">
                    
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800">
                    Tanggal
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800">
                    Stock Awal (MT)
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800">
                    Detail Pemakaian
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800">
                    Total Pakai
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-cyan-400 uppercase tracking-wider border-b border-slate-800">
                    Sisa Akhir
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
                  pemakaianData.map((item, idx) => {
                    const isExpanded = expandedRows[idx];
                    const stockAkhir = calculateStockAkhir(item.stock_awal, item.total_pemakaian);
                    
                    return (
                      <>
                        <tr key={idx} className="hover:bg-slate-800/50 cursor-pointer" onClick={() => toggleRow(idx)}>
                          <td className="px-4 py-3 text-slate-400">
                            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                          </td>
                          <td className="px-4 py-3 text-slate-300">
                            {new Date(item.date).toLocaleDateString('id-ID')}
                          </td>
                          <td className="px-4 py-3 text-right text-slate-300 font-mono">
                            {item.stock_awal.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-blue-400 text-xs">
                              {isExpanded ? "Tutup Detail" : "Lihat Detail"}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right text-red-400 font-mono font-semibold">
                            {item.total_pemakaian.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-right text-emerald-400 font-mono">
                            {stockAkhir.toLocaleString()}
                          </td>
                        </tr>
                        {isExpanded && (
                          <tr>
                            <td colSpan={6} className="bg-slate-900/50 px-4 py-4">
                              <div className="grid grid-cols-2 gap-4">
                                {/* Unit 1 */}
                                <div className="border border-blue-500/30 rounded-lg p-3 bg-blue-500/5">
                                  <h4 className="text-blue-400 font-semibold mb-2 flex items-center gap-2">
                                    <TrendingUp className="w-4 h-4" />
                                    Unit 1 Consumption
                                  </h4>
                                  <div className="space-y-1 text-xs">
                                    {Object.entries(item.suppliers || {}).map(([supplier, units]) => {
                                      const unit1 = units.UNIT1 || {};
                                      const total = (unit1.A || 0) + (unit1.B || 0) + (unit1.C || 0);
                                      if (total === 0) return null;
                                      return (
                                        <div key={supplier} className="flex justify-between text-slate-400">
                                          <span className="truncate mr-2">{supplier.replace(/_/g, ' ').substring(0, 20)}</span>
                                          <span className="font-mono text-blue-300">
                                            A:{unit1.A||0} | B:{unit1.B||0} | C:{unit1.C||0}
                                          </span>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                                
                                {/* Unit 2 */}
                                <div className="border border-purple-500/30 rounded-lg p-3 bg-purple-500/5">
                                  <h4 className="text-purple-400 font-semibold mb-2 flex items-center gap-2">
                                    <TrendingUp className="w-4 h-4" />
                                    Unit 2 Consumption
                                  </h4>
                                  <div className="space-y-1 text-xs">
                                    {Object.entries(item.suppliers || {}).map(([supplier, units]) => {
                                      const unit2 = units.UNIT2 || {};
                                      const total = (unit2.A || 0) + (unit2.B || 0) + (unit2.C || 0);
                                      if (total === 0) return null;
                                      return (
                                        <div key={supplier} className="flex justify-between text-slate-400">
                                          <span className="truncate mr-2">{supplier.replace(/_/g, ' ').substring(0, 20)}</span>
                                          <span className="font-mono text-purple-300">
                                            A:{unit2.A||0} | B:{unit2.B||0} | C:{unit2.C||0}
                                          </span>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    );
                  })
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
