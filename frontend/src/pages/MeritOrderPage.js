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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Award,
  Plus,
  Upload,
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
  FileSpreadsheet,
  AlertTriangle,
  Eye,
  TrendingUp,
  Ship,
  Truck,
  Anchor
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MODA_OPTIONS = ["Tongkang", "Trucking", "Vessel"];
const KONTRAK_OPTIONS = ["CIF", "CFR", "FOB"];

const MeritOrderPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [viewingItem, setViewingItem] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [importPreview, setImportPreview] = useState(null);
  const [importMode, setImportMode] = useState("append");
  const fileInputRef = useRef(null);

  const initialFormData = {
    periode: "",
    pemasok: "",
    moda: "",
    tipikal_kcal_kg: "",
    jenis_kontrak: "",
    harga_batubara: "",
    harga_freight: "",
    harga_cif: "",
    rp_kg: "",
    rp_kcal: ""
  };

  const [formData, setFormData] = useState(initialFormData);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/merit-order`, { headers: getAuthHeader(), params: { page: 1, page_size: 10000 } });
      const data = response.data.items || response.data;
      setData(Array.isArray(data) ? data : []);
    } catch (error) {
      toast.error("Gagal memuat data Merit Order");
    } finally {
      setLoading(false);
    }
  };

  const parseFloat2 = (val) => val ? parseFloat(val) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      let periode_year = null;
      let periode_month = null;
      if (formData.periode) {
        const date = new Date(formData.periode);
        if (!isNaN(date)) {
          periode_year = date.getFullYear();
          periode_month = date.getMonth() + 1;
        }
      }

      const dataToSend = {
        ...formData,
        periode_year,
        periode_month,
        tipikal_kcal_kg: parseFloat2(formData.tipikal_kcal_kg),
        harga_batubara: parseFloat2(formData.harga_batubara),
        harga_freight: parseFloat2(formData.harga_freight),
        harga_cif: parseFloat2(formData.harga_cif),
        rp_kg: parseFloat2(formData.rp_kg),
        rp_kcal: parseFloat2(formData.rp_kcal)
      };

      if (editingItem) {
        await axios.put(`${API_URL}/api/merit-order/${editingItem.id}`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data Merit Order berhasil diperbarui");
      } else {
        await axios.post(`${API_URL}/api/merit-order`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data Merit Order berhasil ditambahkan");
      }
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menyimpan data");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    const newFormData = {};
    Object.keys(initialFormData).forEach(key => {
      const val = item[key];
      newFormData[key] = val !== null && val !== undefined ? String(val) : "";
    });
    setFormData(newFormData);
    setDialogOpen(true);
  };

  const handleView = (item) => {
    setViewingItem(item);
    setViewDialogOpen(true);
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;
    try {
      await axios.delete(`${API_URL}/api/merit-order/${itemId}`, { headers: getAuthHeader() });
      toast.success("Data Merit Order berhasil dihapus");
      fetchData();
    } catch (error) {
      toast.error("Gagal menghapus data");
    }
  };

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      const response = await axios.delete(`${API_URL}/api/merit-order`, { headers: getAuthHeader() });
      toast.success(response.data.message);
      fetchData();
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
      const response = await axios.post(`${API_URL}/api/import-preview/merit-order`, formDataUpload, {
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
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal commit import");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingItem(null);
  };

  const canEdit = user?.role === "admin" || user?.role === "operator";
  const isAdmin = user?.role === "admin";

  const FormField = ({ label, name, type = "text", placeholder = "" }) => (
    <div className="space-y-2">
      <Label className="text-slate-300 text-xs">{label}</Label>
      <Input
        type={type}
        step={type === "number" ? "0.000001" : undefined}
        value={formData[name]}
        onChange={(e) => setFormData({...formData, [name]: e.target.value})}
        className="bg-slate-950/50 border-slate-800 text-white h-9 text-sm"
        placeholder={placeholder}
        data-testid={`input-${name}`}
      />
    </div>
  );

  const formatCurrency = (val) => {
    if (!val && val !== 0) return "-";
    return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(val);
  };

  const formatNumber = (val, decimals = 2) => {
    if (!val && val !== 0) return "-";
    return new Intl.NumberFormat("id-ID", { maximumFractionDigits: decimals }).format(val);
  };

  const getModaIcon = (moda) => {
    switch(moda?.toLowerCase()) {
      case 'vessel': return <Ship className="w-4 h-4 text-blue-400" />;
      case 'tongkang': return <Anchor className="w-4 h-4 text-cyan-400" />;
      case 'trucking': return <Truck className="w-4 h-4 text-amber-400" />;
      default: return null;
    }
  };

  const getKontrakBadge = (kontrak) => {
    const colors = {
      'CIF': 'bg-green-500/20 text-green-400 border-green-500/30',
      'CFR': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      'FOB': 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    };
    return colors[kontrak] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="space-y-6" data-testid="merit-order-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Award className="w-8 h-8 text-emerald-400" />
            Merit Order Batubara
          </h1>
          <p className="text-slate-400 mt-1">Data perbandingan harga pemasok batubara ({data.length} data)</p>
        </div>
        {canEdit && (
          <div className="flex flex-wrap gap-3">
            {isAdmin && data.length > 0 && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10" data-testid="delete-all-mo-btn">
                    <Trash2 className="w-4 h-4 mr-2" />Hapus Semua
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="bg-[#0B1221] border-white/10">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-white flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                      Hapus Semua Data Merit Order?
                    </AlertDialogTitle>
                    <AlertDialogDescription className="text-slate-400">
                      Tindakan ini akan menghapus <span className="text-red-400 font-bold">{data.length}</span> data secara permanen.
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
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="upload-excel-mo-btn">
                  <Upload className="w-4 h-4 mr-2" />Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-3xl">
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel Merit Order</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-emerald-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-2">Format kolom: Periode, Pemasok, Moda, Tipikal, Jenis Kontrak, Harga</p>
                    <p className="text-slate-500 text-xs mb-4">Kolom "Periode" menentukan bulan/tahun data</p>
                    <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileUpload} className="hidden" />
                    <Button onClick={() => fileInputRef.current?.click()} disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Preview File
                    </Button>
                  </div>
                  {importPreview && (
                    <div className="space-y-4 rounded-xl border border-white/10 bg-slate-950/40 p-4">
                      <div className="grid grid-cols-3 gap-3">
                        <div className="rounded-lg bg-emerald-500/10 p-3">
                          <p className="text-xs text-emerald-300">Rows</p>
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
                              <TableHead className="text-slate-400">Pemasok</TableHead>
                              <TableHead className="text-slate-400">Moda</TableHead>
                              <TableHead className="text-slate-400 text-right">RP/Kcal</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {importPreview.preview_rows?.map((row, idx) => (
                              <TableRow key={idx} className="border-white/5">
                                <TableCell className="text-white">{row.pemasok || "-"}</TableCell>
                                <TableCell className="text-slate-300">{row.moda || "-"}</TableCell>
                                <TableCell className="text-right text-white">{formatNumber(row.rp_kcal, 6)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                      <div className="flex justify-end">
                        <Button onClick={commitImportPreview} disabled={submitting || importPreview.issue_count > 0} className="bg-emerald-600 hover:bg-emerald-500">
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
                <Button className="bg-emerald-600 hover:bg-emerald-500 neon-glow" data-testid="add-mo-btn">
                  <Plus className="w-4 h-4 mr-2" />Tambah Data
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-3xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingItem ? "Edit Data Merit Order" : "Tambah Data Merit Order"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[75vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4" data-testid="mo-form">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="Periode" name="periode" type="date" />
                      <FormField label="Pemasok" name="pemasok" placeholder="Nama pemasok" />
                      <div className="space-y-2">
                        <Label className="text-slate-300 text-xs">Moda</Label>
                        <Select value={formData.moda} onValueChange={(val) => setFormData({...formData, moda: val})}>
                          <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white h-9" data-testid="select-moda">
                            <SelectValue placeholder="Pilih moda" />
                          </SelectTrigger>
                          <SelectContent className="bg-[#0B1221] border-slate-800">
                            {MODA_OPTIONS.map(m => (
                              <SelectItem key={m} value={m} className="text-slate-300">{m}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="Tipikal (Kcal/Kg)" name="tipikal_kcal_kg" type="number" placeholder="3800" />
                      <div className="space-y-2">
                        <Label className="text-slate-300 text-xs">Jenis Kontrak</Label>
                        <Select value={formData.jenis_kontrak} onValueChange={(val) => setFormData({...formData, jenis_kontrak: val})}>
                          <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white h-9" data-testid="select-kontrak">
                            <SelectValue placeholder="Pilih jenis" />
                          </SelectTrigger>
                          <SelectContent className="bg-[#0B1221] border-slate-800">
                            {KONTRAK_OPTIONS.map(k => (
                              <SelectItem key={k} value={k} className="text-slate-300">{k}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <FormField label="Harga Batubara (RP/Ton)" name="harga_batubara" type="number" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="Harga Freight (RP/Ton)" name="harga_freight" type="number" />
                      <FormField label="Harga CIF (RP/Ton)" name="harga_cif" type="number" />
                      <FormField label="RP/Kg" name="rp_kg" type="number" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <FormField label="RP/Kcal" name="rp_kcal" type="number" />
                    </div>
                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">
                        Batal
                      </Button>
                      <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500" data-testid="submit-mo-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {editingItem ? "Perbarui" : "Simpan"}
                      </Button>
                    </div>
                  </form>
                </ScrollArea>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>

      {/* Data Table */}
      {loading ? (
        <Card className="glass-card border-white/5 p-8 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400 mx-auto" />
          <p className="text-slate-400 mt-4">Memuat data...</p>
        </Card>
      ) : data.length === 0 ? (
        <Card className="glass-card border-white/5 p-8 text-center">
          <Award className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">Belum ada data Merit Order</p>
          <p className="text-slate-500 text-sm mt-2">Upload file Excel atau tambahkan data manual</p>
        </Card>
      ) : (
        <Card className="glass-card border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-slate-400 font-mono text-xs">Periode</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">Pemasok</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">Moda</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">Tipikal</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">Kontrak</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs text-right">Harga BB</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs text-right">Harga Freight</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs text-right">Harga CIF</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs text-right">RP/Kcal</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((item) => (
                  <TableRow key={item.id} className="border-white/5 hover:bg-slate-900/50">
                    <TableCell className="text-slate-400 text-xs font-mono">{item.periode?.split(" ")[0] || "-"}</TableCell>
                    <TableCell className="text-white text-sm max-w-[200px] truncate">{item.pemasok}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getModaIcon(item.moda)}
                        <span className="text-slate-300 text-sm">{item.moda}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-cyan-400 text-sm font-mono">{formatNumber(item.tipikal_kcal_kg, 0)}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getKontrakBadge(item.jenis_kontrak)}`}>
                        {item.jenis_kontrak}
                      </span>
                    </TableCell>
                    <TableCell className="text-slate-300 text-sm font-mono text-right">{formatCurrency(item.harga_batubara)}</TableCell>
                    <TableCell className="text-slate-300 text-sm font-mono text-right">{item.harga_freight ? formatCurrency(item.harga_freight) : "-"}</TableCell>
                    <TableCell className="text-green-400 text-sm font-mono text-right">{formatCurrency(item.harga_cif)}</TableCell>
                    <TableCell className="text-emerald-400 text-sm font-mono font-bold text-right">{formatNumber(item.rp_kcal, 6)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4 text-slate-400" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-[#0B1221] border-slate-800">
                          <DropdownMenuItem onClick={() => handleView(item)} className="text-slate-300 hover:bg-slate-800 cursor-pointer">
                            <Eye className="w-4 h-4 mr-2" />Lihat
                          </DropdownMenuItem>
                          {canEdit && <DropdownMenuItem onClick={() => handleEdit(item)} className="text-slate-300 hover:bg-slate-800 cursor-pointer">
                            <Edit className="w-4 h-4 mr-2" />Edit
                          </DropdownMenuItem>}
                          {isAdmin && <DropdownMenuItem onClick={() => handleDelete(item.id)} className="text-red-400 hover:bg-slate-800 cursor-pointer">
                            <Trash2 className="w-4 h-4 mr-2" />Hapus
                          </DropdownMenuItem>}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}

      {/* View Detail Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="bg-[#0B1221] border-white/10 max-w-2xl">
          <DialogHeader><DialogTitle className="text-white font-heading">Detail Merit Order</DialogTitle></DialogHeader>
          {viewingItem && (
            <div className="space-y-6 pt-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                <div><p className="text-slate-500 text-xs">Periode</p><p className="text-white text-sm font-medium">{viewingItem.periode || "-"}</p></div>
                <div><p className="text-slate-500 text-xs">Pemasok</p><p className="text-white text-sm">{viewingItem.pemasok || "-"}</p></div>
                <div><p className="text-slate-500 text-xs">Moda</p>
                  <div className="flex items-center gap-2">
                    {getModaIcon(viewingItem.moda)}
                    <span className="text-white text-sm">{viewingItem.moda || "-"}</span>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                <div><p className="text-slate-500 text-xs">Tipikal (Kcal/Kg)</p><p className="text-cyan-400 text-sm font-mono font-bold">{formatNumber(viewingItem.tipikal_kcal_kg, 0)}</p></div>
                <div><p className="text-slate-500 text-xs">Jenis Kontrak</p>
                  <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium border ${getKontrakBadge(viewingItem.jenis_kontrak)}`}>
                    {viewingItem.jenis_kontrak}
                  </span>
                </div>
                <div><p className="text-slate-500 text-xs">Harga Batubara</p><p className="text-white text-sm font-mono">{formatCurrency(viewingItem.harga_batubara)}</p></div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                <div><p className="text-slate-500 text-xs">Harga Freight</p><p className="text-white text-sm font-mono">{viewingItem.harga_freight ? formatCurrency(viewingItem.harga_freight) : "-"}</p></div>
                <div><p className="text-slate-500 text-xs">Harga CIF</p><p className="text-green-400 text-sm font-mono font-bold">{formatCurrency(viewingItem.harga_cif)}</p></div>
                <div><p className="text-slate-500 text-xs">RP/Kg</p><p className="text-white text-sm font-mono">{formatNumber(viewingItem.rp_kg, 3)}</p></div>
              </div>
              <div className="p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  <p className="text-emerald-400 text-sm font-medium">Merit Order Index</p>
                </div>
                <p className="text-emerald-400 text-2xl font-mono font-bold">{formatNumber(viewingItem.rp_kcal, 6)} <span className="text-sm font-normal">RP/Kcal</span></p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MeritOrderPage;
