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
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Leaf,
  Plus,
  Search,
  Upload,
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
  FileSpreadsheet,
  AlertTriangle,
  Eye
} from "lucide-react";
import Pagination from "@/components/Pagination";

const API_URL = process.env.REACT_APP_BACKEND_URL;
const ITEMS_PER_PAGE = 100;

const BiomassaPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [biomassaList, setBiomassaList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editingBiomassa, setEditingBiomassa] = useState(null);
  const [viewingBiomassa, setViewingBiomassa] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const fileInputRef = useRef(null);

  const initialFormData = {
    periode: "",
    shipment_code: "",
    lot: "",
    suppliers: "",
    shipper: "",
    tb: "",
    bg: "",
    biomass_type: "",
    ta: "",
    berthed_time: "",
    commenced_unloading: "",
    completed_unloading: "",
    durasi_pembongkaran: "",
    bl_mt: "",
    jembatan_timbang_mt: "",
    surveyor_unloading: "",
    no_cow_row: "",
    tgl_terbit_cow: "",
    lama_terbit_row: "",
    gcv_adb: "",
    gcv_arb: "",
    tm_arb: "",
    im_arb: "",
    tm_adb: "",
    im_adb: "",
    no_coa: "",
    tgl_terbit_coa: "",
    durasi_pembongkaran_2: "",
    waktu_tunggu_jam: "",
    durasi_terbit_coa: ""
  };

  const [formData, setFormData] = useState(initialFormData);

  useEffect(() => { fetchBiomassa(); setCurrentPage(1); }, [search]);

  const fetchBiomassa = async () => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/biomassa`, { headers: getAuthHeader(), params });
      const sortedData = response.data.reverse();
      setBiomassaList(sortedData);
    } catch (error) {
      toast.error("Gagal memuat data biomassa");
    } finally {
      setLoading(false);
    }
  };

  const parseFloat2 = (val) => val ? parseFloat(val) : null;

  const totalPages = Math.ceil(biomassaList.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedBiomassa = biomassaList.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const dataToSend = {
        ...formData,
        durasi_pembongkaran: parseFloat2(formData.durasi_pembongkaran),
        bl_mt: parseFloat2(formData.bl_mt),
        jembatan_timbang_mt: parseFloat2(formData.jembatan_timbang_mt),
        gcv_adb: parseFloat2(formData.gcv_adb),
        gcv_arb: parseFloat2(formData.gcv_arb),
        tm_arb: parseFloat2(formData.tm_arb),
        im_arb: parseFloat2(formData.im_arb),
        tm_adb: parseFloat2(formData.tm_adb),
        im_adb: parseFloat2(formData.im_adb),
        durasi_pembongkaran_2: parseFloat2(formData.durasi_pembongkaran_2),
        waktu_tunggu_jam: parseFloat2(formData.waktu_tunggu_jam)
      };

      if (editingBiomassa) {
        await axios.put(`${API_URL}/api/biomassa/${editingBiomassa.id}`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data biomassa berhasil diperbarui");
      } else {
        await axios.post(`${API_URL}/api/biomassa`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data biomassa berhasil ditambahkan");
      }
      setDialogOpen(false);
      resetForm();
      fetchBiomassa();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menyimpan data");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (biomassa) => {
    setEditingBiomassa(biomassa);
    const newFormData = {};
    Object.keys(initialFormData).forEach(key => {
      const val = biomassa[key];
      newFormData[key] = val !== null && val !== undefined ? String(val) : "";
    });
    setFormData(newFormData);
    setDialogOpen(true);
  };

  const handleView = (biomassa) => {
    setViewingBiomassa(biomassa);
    setViewDialogOpen(true);
  };

  const handleDelete = async (biomassaId) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;
    try {
      await axios.delete(`${API_URL}/api/biomassa/${biomassaId}`, { headers: getAuthHeader() });
      toast.success("Data biomassa berhasil dihapus");
      fetchBiomassa();
    } catch (error) {
      toast.error("Gagal menghapus data");
    }
  };

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      const response = await axios.delete(`${API_URL}/api/biomassa`, { headers: getAuthHeader() });
      toast.success(response.data.message);
      fetchBiomassa();
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
      const response = await axios.post(`${API_URL}/api/upload/biomassa`, formDataUpload, {
        headers: { ...getAuthHeader(), "Content-Type": "multipart/form-data" }
      });
      toast.success(response.data.message);
      setUploadDialogOpen(false);
      fetchBiomassa();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal mengupload file");
    } finally {
      setSubmitting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingBiomassa(null);
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

  return (
    <div className="space-y-6" data-testid="biomassa-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Leaf className="w-8 h-8 text-green-400" />
            Biomassa TNY
          </h1>
          <p className="text-slate-400 mt-1">Data penerimaan biomassa ({biomassaList.length} data)</p>
        </div>
        {canEdit && (
          <div className="flex flex-wrap gap-3">
            {isAdmin && biomassaList.length > 0 && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10" data-testid="delete-all-biomassa-btn">
                    <Trash2 className="w-4 h-4 mr-2" />Hapus Semua
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="bg-[#0B1221] border-white/10">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-white flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                      Hapus Semua Data Biomassa?
                    </AlertDialogTitle>
                    <AlertDialogDescription className="text-slate-400">
                      Tindakan ini akan menghapus <span className="text-red-400 font-bold">{biomassaList.length}</span> data biomassa secara permanen.
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
            <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="upload-excel-biomassa-btn">
                  <Upload className="w-4 h-4 mr-2" />Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel Biomassa</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-green-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-2">Format kolom Excel harus sesuai template</p>
                    <p className="text-slate-500 text-xs mb-4">Header: Periode, Shipment Code, Lot, Suppliers, Shipper, TB, BG, Biomass, dll.</p>
                    <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileUpload} className="hidden" />
                    <Button onClick={() => fileInputRef.current?.click()} disabled={submitting} className="bg-green-600 hover:bg-green-500">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Pilih File
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-green-600 hover:bg-green-500 neon-glow" data-testid="add-biomassa-btn">
                  <Plus className="w-4 h-4 mr-2" />Tambah Data
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-5xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingBiomassa ? "Edit Data Biomassa" : "Tambah Data Biomassa"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[75vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4" data-testid="biomassa-form">
                    <Tabs defaultValue="shipment" className="w-full">
                      <TabsList className="grid w-full grid-cols-5 bg-slate-900/50">
                        <TabsTrigger value="shipment" className="text-xs data-[state=active]:bg-green-500/20">Shipment</TabsTrigger>
                        <TabsTrigger value="waktu" className="text-xs data-[state=active]:bg-green-500/20">Waktu</TabsTrigger>
                        <TabsTrigger value="muatan" className="text-xs data-[state=active]:bg-green-500/20">Muatan</TabsTrigger>
                        <TabsTrigger value="kualitas" className="text-xs data-[state=active]:bg-green-500/20">Kualitas</TabsTrigger>
                        <TabsTrigger value="dokumen" className="text-xs data-[state=active]:bg-green-500/20">Dokumen</TabsTrigger>
                      </TabsList>
                      
                      <TabsContent value="shipment" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">Informasi Shipment</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="Periode" name="periode" placeholder="Jan-25" />
                          <FormField label="Shipment Code" name="shipment_code" />
                          <FormField label="Lot" name="lot" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="Suppliers" name="suppliers" />
                          <FormField label="Shipper" name="shipper" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="TB (Tug Boat)" name="tb" />
                          <FormField label="BG (Barge)" name="bg" />
                          <FormField label="Biomass" name="biomass_type" placeholder="WOODCHIP, SAWDUST, dll." />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="waktu" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">Waktu Operasional</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="TA (Time Arrival)" name="ta" />
                          <FormField label="Berthed Time" name="berthed_time" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="Commenced Unloading" name="commenced_unloading" />
                          <FormField label="Completed Unloading" name="completed_unloading" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="Durasi Pembongkaran" name="durasi_pembongkaran" type="number" />
                          <FormField label="Waktu Tunggu (Jam)" name="waktu_tunggu_jam" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="muatan" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">Data Muatan</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="B/L (MT)" name="bl_mt" type="number" />
                          <FormField label="Jembatan Timbang (MT)" name="jembatan_timbang_mt" type="number" />
                          <FormField label="Surveyor Unloading" name="surveyor_unloading" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="kualitas" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">GCV (Kcal/Kg)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="GCV ADB" name="gcv_adb" type="number" />
                          <FormField label="GCV ARB" name="gcv_arb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-green-400 mt-4">TM (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="TM ARB" name="tm_arb" type="number" />
                          <FormField label="TM ADB" name="tm_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-green-400 mt-4">IM (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="IM ARB" name="im_arb" type="number" />
                          <FormField label="IM ADB" name="im_adb" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="dokumen" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">COW / ROW</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="NO. COW / ROW" name="no_cow_row" />
                          <FormField label="Tgl Terbit COW" name="tgl_terbit_cow" />
                          <FormField label="Lama Terbit ROW" name="lama_terbit_row" />
                        </div>
                        <h4 className="text-sm font-mono text-green-400 mt-4">COA</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="NO. COA" name="no_coa" />
                          <FormField label="Tgl Terbit COA" name="tgl_terbit_coa" />
                          <FormField label="Durasi Terbit COA" name="durasi_terbit_coa" />
                        </div>
                      </TabsContent>
                    </Tabs>
                    
                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">
                        Batal
                      </Button>
                      <Button type="submit" disabled={submitting} className="bg-green-600 hover:bg-green-500" data-testid="submit-biomassa-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {editingBiomassa ? "Perbarui" : "Simpan"}
                      </Button>
                    </div>
                  </form>
                </ScrollArea>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>

      <Card className="glass-card border-white/5 p-4">
        <div className="flex items-center gap-4 mb-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <Input
              placeholder="Cari shipment, supplier, biomass type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-slate-950/50 border-slate-800 text-white"
              data-testid="search-biomassa-input"
            />
          </div>
        </div>
        
        <div className="rounded-lg border border-white/5 overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400 font-mono text-xs">Periode</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">Shipment</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">Supplier</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">Biomass</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">B/L (MT)</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">GCV ARB</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-green-400 mx-auto" />
                  </TableCell>
                </TableRow>
              ) : paginatedBiomassa.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                    Belum ada data biomassa
                  </TableCell>
                </TableRow>
              ) : (
                paginatedBiomassa.map((biomassa) => (
                  <TableRow key={biomassa.id} className="border-white/5 hover:bg-slate-900/50" data-testid={`biomassa-row-${biomassa.id}`}>
                    <TableCell className="text-slate-300 text-sm">{biomassa.periode}</TableCell>
                    <TableCell className="text-white font-medium text-sm">{biomassa.shipment_code}</TableCell>
                    <TableCell className="text-slate-300 text-sm">{biomassa.suppliers}</TableCell>
                    <TableCell>
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400">
                        {biomassa.biomass_type || "-"}
                      </span>
                    </TableCell>
                    <TableCell className="text-slate-300 text-sm font-mono">{biomassa.bl_mt?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-green-400 text-sm font-mono">{biomassa.gcv_arb?.toLocaleString() || '-'}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" data-testid={`action-btn-${biomassa.id}`}>
                            <MoreHorizontal className="h-4 w-4 text-slate-400" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-[#0B1221] border-slate-800">
                          <DropdownMenuItem onClick={() => handleView(biomassa)} className="text-slate-300 hover:bg-slate-800 cursor-pointer">
                            <Eye className="w-4 h-4 mr-2" />Lihat
                          </DropdownMenuItem>
                          {canEdit && <DropdownMenuItem onClick={() => handleEdit(biomassa)} className="text-slate-300 hover:bg-slate-800 cursor-pointer">
                            <Edit className="w-4 h-4 mr-2" />Edit
                          </DropdownMenuItem>}
                          {isAdmin && <DropdownMenuItem onClick={() => handleDelete(biomassa.id)} className="text-red-400 hover:bg-slate-800 cursor-pointer">
                            <Trash2 className="w-4 h-4 mr-2" />Hapus
                          </DropdownMenuItem>}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} totalItems={biomassaList.length} itemsPerPage={ITEMS_PER_PAGE} />
      </Card>

      {/* View Detail Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="bg-[#0B1221] border-white/10 max-w-4xl max-h-[90vh]">
          <DialogHeader><DialogTitle className="text-white font-heading">Detail Data Biomassa</DialogTitle></DialogHeader>
          <ScrollArea className="max-h-[75vh] pr-4">
            {viewingBiomassa && (
              <div className="space-y-6 pt-4">
                <h4 className="text-sm font-mono text-green-400">Informasi Shipment</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-900/50 rounded-lg">
                  <div><p className="text-slate-500 text-xs">Periode</p><p className="text-white text-sm">{viewingBiomassa.periode || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Shipment Code</p><p className="text-white text-sm">{viewingBiomassa.shipment_code || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Lot</p><p className="text-white text-sm">{viewingBiomassa.lot || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Suppliers</p><p className="text-white text-sm">{viewingBiomassa.suppliers || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Shipper</p><p className="text-white text-sm">{viewingBiomassa.shipper || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">TB / BG</p><p className="text-white text-sm">{viewingBiomassa.tb || "-"} / {viewingBiomassa.bg || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Biomass</p><p className="text-white text-sm">{viewingBiomassa.biomass_type || "-"}</p></div>
                </div>
                <h4 className="text-sm font-mono text-green-400">Waktu Operasional</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-900/50 rounded-lg">
                  <div><p className="text-slate-500 text-xs">TA</p><p className="text-white text-sm">{viewingBiomassa.ta || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Berthed Time</p><p className="text-white text-sm">{viewingBiomassa.berthed_time || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Commenced Unloading</p><p className="text-white text-sm">{viewingBiomassa.commenced_unloading || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Completed Unloading</p><p className="text-white text-sm">{viewingBiomassa.completed_unloading || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Durasi Pembongkaran</p><p className="text-white text-sm">{viewingBiomassa.durasi_pembongkaran || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Waktu Tunggu (Jam)</p><p className="text-white text-sm">{viewingBiomassa.waktu_tunggu_jam || "-"}</p></div>
                </div>
                <h4 className="text-sm font-mono text-green-400">Data Muatan</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                  <div><p className="text-slate-500 text-xs">B/L (MT)</p><p className="text-white text-sm">{viewingBiomassa.bl_mt?.toLocaleString() || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Jembatan Timbang (MT)</p><p className="text-white text-sm">{viewingBiomassa.jembatan_timbang_mt?.toLocaleString() || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Surveyor Unloading</p><p className="text-white text-sm">{viewingBiomassa.surveyor_unloading || "-"}</p></div>
                </div>
                <h4 className="text-sm font-mono text-green-400">Kualitas</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                  <div><p className="text-slate-500 text-xs">GCV ADB (Kcal/Kg)</p><p className="text-white text-sm">{viewingBiomassa.gcv_adb?.toLocaleString() || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">GCV ARB (Kcal/Kg)</p><p className="text-white text-sm">{viewingBiomassa.gcv_arb?.toLocaleString() || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">TM ARB (%wt)</p><p className="text-white text-sm">{viewingBiomassa.tm_arb?.toFixed(2) || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">IM ARB (%wt)</p><p className="text-white text-sm">{viewingBiomassa.im_arb?.toFixed(2) || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">TM ADB (%wt)</p><p className="text-white text-sm">{viewingBiomassa.tm_adb?.toFixed(2) || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">IM ADB (%wt)</p><p className="text-white text-sm">{viewingBiomassa.im_adb?.toFixed(2) || "-"}</p></div>
                </div>
                <h4 className="text-sm font-mono text-green-400">Dokumen COW/ROW & COA</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-900/50 rounded-lg">
                  <div><p className="text-slate-500 text-xs">NO. COW / ROW</p><p className="text-white text-sm">{viewingBiomassa.no_cow_row || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Tgl Terbit COW</p><p className="text-white text-sm">{viewingBiomassa.tgl_terbit_cow || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Lama Terbit ROW</p><p className="text-white text-sm">{viewingBiomassa.lama_terbit_row || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">NO. COA</p><p className="text-white text-sm">{viewingBiomassa.no_coa || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Tgl Terbit COA</p><p className="text-white text-sm">{viewingBiomassa.tgl_terbit_coa || "-"}</p></div>
                  <div><p className="text-slate-500 text-xs">Durasi Terbit COA</p><p className="text-white text-sm">{viewingBiomassa.durasi_terbit_coa || "-"}</p></div>
                </div>
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BiomassaPage;
