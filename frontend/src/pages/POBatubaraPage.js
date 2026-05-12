import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  ShoppingCart,
  Plus,
  Upload,
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
  FileSpreadsheet,
  AlertTriangle,
  Eye,
  ChevronDown,
  ChevronRight,
  Calendar,
  DollarSign,
  Package
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MONTHS = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember"
];

const POBatubaraPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [yearsData, setYearsData] = useState([]);
  const [poData, setPoData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editingPO, setEditingPO] = useState(null);
  const [viewingPO, setViewingPO] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [importPreview, setImportPreview] = useState(null);
  const [importMode, setImportMode] = useState("append");
  const [expandedYears, setExpandedYears] = useState({});
  const [expandedMonths, setExpandedMonths] = useState({});
  const [selectedYear, setSelectedYear] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(null);
  const fileInputRef = useRef(null);

  const initialFormData = {
    district_code: "",
    district_name: "",
    periode: "",
    stock_code: "",
    warehouse: "",
    po_number: "",
    supplier_code: "",
    supplier_name: "",
    spec: "",
    vessel_tugboat: "",
    barge: "",
    no_jadwal: "",
    id_bbo_no_pengiriman: "",
    id_bbo_trans: "",
    no_shipment: "",
    time_arrival: "",
    completed: "",
    tonase_po: "",
    tonase_po_1000: "",
    inventory_price: "",
    freight_inventory_fob: "",
    total: ""
  };

  const [formData, setFormData] = useState(initialFormData);

  useEffect(() => { fetchYearsData(); }, []);

  const fetchYearsData = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/po-batubara/years`, { headers: getAuthHeader() });
      setYearsData(response.data.sort((a, b) => b.year - a.year));
      
      // Auto expand first year
      if (response.data.length > 0) {
        const firstYear = response.data.sort((a, b) => b.year - a.year)[0].year;
        setExpandedYears({ [firstYear]: true });
      }
    } catch (error) {
      toast.error("Gagal memuat data tahun");
    } finally {
      setLoading(false);
    }
  };

  const fetchMonthData = async (year, month) => {
    try {
      const response = await axios.get(`${API_URL}/api/po-batubara`, { 
        headers: getAuthHeader(),
        params: { year, month, page: 1, page_size: 10000 }
      });
      const data = response.data.items || response.data;
      return Array.isArray(data) ? data : [];
    } catch (error) {
      toast.error("Gagal memuat data bulan");
      return [];
    }
  };

  const toggleYear = (year) => {
    setExpandedYears(prev => ({ ...prev, [year]: !prev[year] }));
  };

  const toggleMonth = async (year, month) => {
    const key = `${year}-${month}`;
    if (!expandedMonths[key]) {
      const data = await fetchMonthData(year, month);
      setPoData(prev => ({ ...prev, [key]: data }));
    }
    setExpandedMonths(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const parseFloat2 = (val) => val ? parseFloat(val) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      // Parse completed date to extract year and month
      let completed_year = null;
      let completed_month = null;
      if (formData.completed) {
        const date = new Date(formData.completed);
        if (!isNaN(date)) {
          completed_year = date.getFullYear();
          completed_month = date.getMonth() + 1;
        }
      }

      const dataToSend = {
        ...formData,
        stock_code: parseFloat2(formData.stock_code),
        warehouse: parseFloat2(formData.warehouse),
        tonase_po: parseFloat2(formData.tonase_po),
        tonase_po_1000: parseFloat2(formData.tonase_po_1000),
        inventory_price: parseFloat2(formData.inventory_price),
        freight_inventory_fob: parseFloat2(formData.freight_inventory_fob),
        total: parseFloat2(formData.total),
        completed_year,
        completed_month
      };

      if (editingPO) {
        await axios.put(`${API_URL}/api/po-batubara/${editingPO.id}`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data PO berhasil diperbarui");
      } else {
        await axios.post(`${API_URL}/api/po-batubara`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data PO berhasil ditambahkan");
      }
      setDialogOpen(false);
      resetForm();
      fetchYearsData();
      setExpandedMonths({});
      setPoData({});
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menyimpan data");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (po) => {
    setEditingPO(po);
    const newFormData = {};
    Object.keys(initialFormData).forEach(key => {
      const val = po[key];
      newFormData[key] = val !== null && val !== undefined ? String(val) : "";
    });
    setFormData(newFormData);
    setDialogOpen(true);
  };

  const handleView = (po) => {
    setViewingPO(po);
    setViewDialogOpen(true);
  };

  const handleDelete = async (poId) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;
    try {
      await axios.delete(`${API_URL}/api/po-batubara/${poId}`, { headers: getAuthHeader() });
      toast.success("Data PO berhasil dihapus");
      fetchYearsData();
      setExpandedMonths({});
      setPoData({});
    } catch (error) {
      toast.error("Gagal menghapus data");
    }
  };

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      const response = await axios.delete(`${API_URL}/api/po-batubara`, { headers: getAuthHeader() });
      toast.success(response.data.message);
      fetchYearsData();
      setExpandedMonths({});
      setPoData({});
    } catch (error) {
      toast.error("Gagal menghapus semua data");
    } finally {
      setDeleting(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formDataUpload = new FormData();
    formDataUpload.append("file", file);
    setSubmitting(true);
    try {
      const response = await axios.post(`${API_URL}/api/import-preview/po-batubara`, formDataUpload, {
        headers: { ...getAuthHeader(), "Content-Type": "multipart/form-data" }
      });
      setImportPreview(response.data);
      toast.success(`Preview selesai: ${response.data.row_count} baris`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal preview file");
    } finally {
      setSubmitting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const commitImportPreview = async () => {
    if (!importPreview?.preview_id) return;
    setSubmitting(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/import-preview/${importPreview.preview_id}/commit`,
        { mode: importMode },
        { headers: getAuthHeader() }
      );
      toast.success(`Import selesai: ${response.data.inserted || 0} tambah, ${response.data.updated || 0} update`);
      setUploadDialogOpen(false);
      setImportPreview(null);
      setImportMode("append");
      fetchYearsData();
      setExpandedMonths({});
      setPoData({});
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal commit import");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingPO(null);
  };

  const canEdit = user?.role === "admin" || user?.role === "operator";
  const isAdmin = user?.role === "admin";

  const FormField = ({ label, name, type = "text", placeholder = "" }) => (
    <div className="space-y-2">
      <Label className="text-slate-300 text-xs">{label}</Label>
      <Input
        type={type}
        step={type === "number" ? "0.001" : undefined}
        value={formData[name]}
        onChange={(e) => setFormData({...formData, [name]: e.target.value})}
        className="bg-slate-950/50 border-slate-800 text-white h-9 text-sm"
        placeholder={placeholder}
        data-testid={`input-${name}`}
      />
    </div>
  );

  const formatCurrency = (val) => {
    if (!val) return "-";
    return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(val);
  };

  const formatNumber = (val) => {
    if (!val) return "-";
    return new Intl.NumberFormat("id-ID").format(val);
  };

  const totalCount = yearsData.reduce((sum, y) => sum + y.total_count, 0);

  return (
    <div className="space-y-6" data-testid="po-batubara-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <ShoppingCart className="w-8 h-8 text-amber-400" />
            Purchase Order Batubara
          </h1>
          <p className="text-slate-400 mt-1">Data PO Batubara PLTU Tenayan ({totalCount} data)</p>
        </div>
        {canEdit && (
          <div className="flex flex-wrap gap-3">
            {isAdmin && totalCount > 0 && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10" data-testid="delete-all-po-btn">
                    <Trash2 className="w-4 h-4 mr-2" />Hapus Semua
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="bg-[#0B1221] border-white/10">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-white flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                      Hapus Semua Data PO?
                    </AlertDialogTitle>
                    <AlertDialogDescription className="text-slate-400">
                      Tindakan ini akan menghapus <span className="text-red-400 font-bold">{totalCount}</span> data PO secara permanen.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel className="border-slate-700 text-slate-300">Batal</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDeleteAll} disabled={deleting} className="bg-red-600 hover:bg-red-500">
                      {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Ya, Hapus Semua
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
            <Dialog open={uploadDialogOpen} onOpenChange={(open) => { setUploadDialogOpen(open); if (!open) { setImportPreview(null); setImportMode("append"); } }}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="upload-excel-po-btn">
                  <Upload className="w-4 h-4 mr-2" />Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-3xl">
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel PO Batubara</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-amber-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-2">Format kolom Excel harus sesuai template</p>
                    <p className="text-slate-500 text-xs mb-4">Kolom "Completed" menentukan bulan/tahun data</p>
                    <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileUpload} className="hidden" />
                    <Button onClick={() => fileInputRef.current?.click()} disabled={submitting} className="bg-amber-600 hover:bg-amber-500">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Preview File
                    </Button>
                  </div>
                  {importPreview && (
                    <div className="space-y-4 rounded-xl border border-white/10 bg-slate-950/40 p-4">
                      <div className="grid grid-cols-3 gap-3">
                        <div className="rounded-lg bg-amber-500/10 p-3">
                          <p className="text-xs text-amber-300">Rows</p>
                          <p className="text-2xl font-bold text-white">{importPreview.row_count}</p>
                        </div>
                        <div className="rounded-lg bg-red-500/10 p-3">
                          <p className="text-xs text-red-300">Issues</p>
                          <p className="text-2xl font-bold text-white">{importPreview.issue_count}</p>
                        </div>
                        <div className="rounded-lg bg-blue-500/10 p-3">
                          <p className="text-xs text-blue-300">Mode</p>
                          <Select value={importMode} onValueChange={setImportMode}>
                            <SelectTrigger className="mt-1 h-8 bg-slate-900/70 border-slate-700 text-white">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-[#0B1221] border-slate-700">
                              <SelectItem value="append">Append</SelectItem>
                              <SelectItem value="merge">Merge</SelectItem>
                              <SelectItem value="replace">Replace</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      {importPreview.issues?.length > 0 && (
                        <div className="max-h-28 overflow-y-auto rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                          {importPreview.issues.slice(0, 5).map((issue, idx) => (
                            <p key={idx} className="text-xs text-red-200">{issue.type}: {issue.message}</p>
                          ))}
                        </div>
                      )}
                      <div className="max-h-44 overflow-auto rounded-lg border border-white/10">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-white/10">
                              <TableHead className="text-slate-400">PO</TableHead>
                              <TableHead className="text-slate-400">Supplier</TableHead>
                              <TableHead className="text-slate-400 text-right">Tonase</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {importPreview.preview_rows?.map((row, idx) => (
                              <TableRow key={idx} className="border-white/5">
                                <TableCell className="text-white">{row.po_number || "-"}</TableCell>
                                <TableCell className="text-slate-300">{row.supplier_name || "-"}</TableCell>
                                <TableCell className="text-right text-white">{formatNumber(row.tonase_po)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                      <div className="flex justify-end">
                        <Button onClick={commitImportPreview} disabled={submitting || importPreview.issue_count > 0} className="bg-amber-600 hover:bg-amber-500">
                          {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Commit Import
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-amber-600 hover:bg-amber-500 neon-glow" data-testid="add-po-btn">
                  <Plus className="w-4 h-4 mr-2" />Tambah Data
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-4xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingPO ? "Edit Data PO" : "Tambah Data PO"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[75vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4" data-testid="po-form">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="District Code" name="district_code" />
                      <FormField label="District Name" name="district_name" />
                      <FormField label="Periode" name="periode" placeholder="2023-01-01" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="PO Number" name="po_number" />
                      <FormField label="Supplier Code" name="supplier_code" />
                      <FormField label="Supplier Name" name="supplier_name" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="Spec" name="spec" />
                      <FormField label="Vessel / Tugboat" name="vessel_tugboat" />
                      <FormField label="Barge" name="barge" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="No Jadwal" name="no_jadwal" />
                      <FormField label="No Shipment" name="no_shipment" />
                      <FormField label="Time Arrival" name="time_arrival" placeholder="2023-01-01 10:00:00" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="Completed" name="completed" placeholder="2023-01-15 14:00:00" />
                      <FormField label="Tonase PO" name="tonase_po" type="number" />
                      <FormField label="Total" name="total" type="number" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField label="Inventory Price" name="inventory_price" type="number" />
                      <FormField label="Freight Inventory (FOB)" name="freight_inventory_fob" type="number" />
                    </div>
                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">
                        Batal
                      </Button>
                      <Button type="submit" disabled={submitting} className="bg-amber-600 hover:bg-amber-500" data-testid="submit-po-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {editingPO ? "Perbarui" : "Simpan"}
                      </Button>
                    </div>
                  </form>
                </ScrollArea>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>

      {/* Years View */}
      {loading ? (
        <Card className="glass-card border-white/5 p-8 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-amber-400 mx-auto" />
          <p className="text-slate-400 mt-4">Memuat data...</p>
        </Card>
      ) : yearsData.length === 0 ? (
        <Card className="glass-card border-white/5 p-8 text-center">
          <ShoppingCart className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">Belum ada data PO Batubara</p>
          <p className="text-slate-500 text-sm mt-2">Upload file Excel atau tambahkan data manual</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {yearsData.map((yearData) => (
            <Card key={yearData.year} className="glass-card border-white/5 overflow-hidden">
              <Collapsible open={expandedYears[yearData.year]} onOpenChange={() => toggleYear(yearData.year)}>
                <CollapsibleTrigger className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
                      <Calendar className="w-6 h-6 text-amber-400" />
                    </div>
                    <div className="text-left">
                      <h3 className="text-xl font-bold text-white">{yearData.year}</h3>
                      <p className="text-slate-400 text-sm">{yearData.total_count} data PO</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right hidden sm:block">
                      <p className="text-slate-500 text-xs">Total Tonase</p>
                      <p className="text-cyan-400 font-mono font-bold">{formatNumber(yearData.total_tonase)} MT</p>
                    </div>
                    <div className="text-right hidden md:block">
                      <p className="text-slate-500 text-xs">Total Nilai</p>
                      <p className="text-green-400 font-mono font-bold">{formatCurrency(yearData.total_value)}</p>
                    </div>
                    <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform duration-200 ${expandedYears[yearData.year] ? "rotate-180" : ""}`} />
                  </div>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="border-t border-white/5 p-4 space-y-2">
                    {MONTHS.map((monthName, index) => {
                      const monthNum = index + 1;
                      const monthData = yearData.months[monthNum];
                      const monthKey = `${yearData.year}-${monthNum}`;
                      const isExpanded = expandedMonths[monthKey];
                      const monthPOData = poData[monthKey] || [];

                      if (!monthData) {
                        return (
                          <div key={monthKey} className="p-3 rounded-lg bg-slate-900/30 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-slate-800/50 flex items-center justify-center">
                                <span className="text-slate-600 text-xs font-mono">{monthNum}</span>
                              </div>
                              <span className="text-slate-600 text-sm">{monthName}</span>
                            </div>
                            <span className="text-slate-700 text-xs">Tidak ada data</span>
                          </div>
                        );
                      }

                      return (
                        <Collapsible key={monthKey} open={isExpanded} onOpenChange={() => toggleMonth(yearData.year, monthNum)}>
                          <CollapsibleTrigger className="w-full p-3 rounded-lg bg-slate-900/50 hover:bg-slate-900/70 flex items-center justify-between transition-colors">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                                <span className="text-amber-400 text-xs font-mono font-bold">{monthNum}</span>
                              </div>
                              <span className="text-white text-sm font-medium">{monthName}</span>
                              <span className="text-slate-500 text-xs">({monthData.count} data)</span>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="text-right hidden sm:block">
                                <p className="text-cyan-400 font-mono text-sm">{formatNumber(monthData.total_tonase)} MT</p>
                              </div>
                              <div className="text-right hidden md:block">
                                <p className="text-green-400 font-mono text-sm">{formatCurrency(monthData.total_value)}</p>
                              </div>
                              <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isExpanded ? "rotate-90" : ""}`} />
                            </div>
                          </CollapsibleTrigger>
                          <CollapsibleContent>
                            <div className="mt-2 rounded-lg border border-white/5 overflow-hidden">
                              <Table>
                                <TableHeader>
                                  <TableRow className="border-white/5 hover:bg-transparent">
                                    <TableHead className="text-slate-400 font-mono text-xs">PO Number</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Supplier</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Vessel/Barge</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Completed</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Tonase PO</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs">Total</TableHead>
                                    <TableHead className="text-slate-400 font-mono text-xs w-[50px]"></TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {monthPOData.map((po) => (
                                    <TableRow key={po.id} className="border-white/5 hover:bg-slate-900/50">
                                      <TableCell className="text-white text-sm font-medium">{po.po_number}</TableCell>
                                      <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{po.supplier_name}</TableCell>
                                      <TableCell className="text-slate-400 text-sm">{po.vessel_tugboat || po.barge || "-"}</TableCell>
                                      <TableCell className="text-slate-400 text-xs font-mono">{po.completed?.split(" ")[0] || "-"}</TableCell>
                                      <TableCell className="text-cyan-400 text-sm font-mono">{formatNumber(po.tonase_po)}</TableCell>
                                      <TableCell className="text-green-400 text-sm font-mono">{formatCurrency(po.total)}</TableCell>
                                      <TableCell>
                                        <DropdownMenu>
                                          <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                              <MoreHorizontal className="h-4 w-4 text-slate-400" />
                                            </Button>
                                          </DropdownMenuTrigger>
                                          <DropdownMenuContent align="end" className="bg-[#0B1221] border-slate-800">
                                            <DropdownMenuItem onClick={() => handleView(po)} className="text-slate-300 hover:bg-slate-800 cursor-pointer">
                                              <Eye className="w-4 h-4 mr-2" />Lihat
                                            </DropdownMenuItem>
                                            {canEdit && <DropdownMenuItem onClick={() => handleEdit(po)} className="text-slate-300 hover:bg-slate-800 cursor-pointer">
                                              <Edit className="w-4 h-4 mr-2" />Edit
                                            </DropdownMenuItem>}
                                            {isAdmin && <DropdownMenuItem onClick={() => handleDelete(po.id)} className="text-red-400 hover:bg-slate-800 cursor-pointer">
                                              <Trash2 className="w-4 h-4 mr-2" />Hapus
                                            </DropdownMenuItem>}
                                          </DropdownMenuContent>
                                        </DropdownMenu>
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                              {/* Monthly Total */}
                              <div className="p-3 bg-amber-500/10 border-t border-white/5 flex justify-between items-center">
                                <span className="text-amber-400 text-sm font-medium">Total Bulanan ({monthName})</span>
                                <div className="flex gap-6">
                                  <span className="text-cyan-400 font-mono font-bold">{formatNumber(monthData.total_tonase)} MT</span>
                                  <span className="text-green-400 font-mono font-bold">{formatCurrency(monthData.total_value)}</span>
                                </div>
                              </div>
                            </div>
                          </CollapsibleContent>
                        </Collapsible>
                      );
                    })}
                    {/* Yearly Total */}
                    <div className="p-4 bg-amber-500/20 rounded-lg flex justify-between items-center mt-4">
                      <span className="text-amber-400 text-sm font-bold">Total Tahunan {yearData.year}</span>
                      <div className="flex gap-6">
                        <span className="text-cyan-400 font-mono font-bold text-lg">{formatNumber(yearData.total_tonase)} MT</span>
                        <span className="text-green-400 font-mono font-bold text-lg">{formatCurrency(yearData.total_value)}</span>
                      </div>
                    </div>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </Card>
          ))}
        </div>
      )}

      {/* View Detail Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="bg-[#0B1221] border-white/10 max-w-3xl max-h-[90vh]">
          <DialogHeader><DialogTitle className="text-white font-heading">Detail Data PO Batubara</DialogTitle></DialogHeader>
          <ScrollArea className="max-h-[75vh] pr-4">
            {viewingPO && (
              <div className="space-y-6 pt-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                  <div><p className="text-slate-500 text-xs">PO Number</p><p className="text-white text-sm font-medium">{viewingPO.po_number || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Supplier</p><p className="text-white text-sm">{viewingPO.supplier_name || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Spec</p><p className="text-white text-sm">{viewingPO.spec || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Vessel / Tugboat</p><p className="text-white text-sm">{viewingPO.vessel_tugboat || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Barge</p><p className="text-white text-sm">{viewingPO.barge || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">No Shipment</p><p className="text-white text-sm">{viewingPO.no_shipment || "-"}</p></div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                  <div><p className="text-slate-500 text-xs">Time Arrival</p><p className="text-white text-sm">{viewingPO.time_arrival || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Completed</p><p className="text-white text-sm">{viewingPO.completed || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Periode</p><p className="text-white text-sm">{viewingPO.periode || "-"}</p></div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                  <div><p className="text-slate-500 text-xs">Tonase PO</p><p className="text-cyan-400 text-sm font-mono font-bold">{formatNumber(viewingPO.tonase_po)}</p></div>
                  <div><p className="text-slate-500 text-xs">Inventory Price</p><p className="text-white text-sm font-mono">{formatNumber(viewingPO.inventory_price)}</p></div>
                  <div><p className="text-slate-500 text-xs">Total</p><p className="text-green-400 text-sm font-mono font-bold">{formatCurrency(viewingPO.total)}</p></div>
                </div>
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default POBatubaraPage;
