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
  const [editingBiomassa, setEditingBiomassa] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [viewingBiomassa, setViewingBiomassa] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const fileInputRef = useRef(null);

  const initialFormData = {
    periode: "",
    shipment_code: "",
    voyage_code: "",
    lot: "",
    suppliers: "",
    shipper: "",
    lot_detail: "",
    tb: "",
    bg: "",
    biomass_type: "",
    ta: "",
    berthed_time: "",
    commenced_unloading: "",
    completed_unloading: "",
    durasi_pembongkaran_hari: "",
    waktu_tunggu_jam: "",
    bl_mt: "",
    jembatan_timbang_mt: "",
    surveyor: "",
    no_cow: "",
    tgl_terbit_cow: "",
    lama_terbit_row: "",
    gcv_arb: "",
    gcv_adb: "",
    tm_arb: "",
    im_adb: "",
    no_coa: "",
    tgl_terbit_coa: "",
    durasi_terbit_coa: ""
  };

  const [formData, setFormData] = useState(initialFormData);

  useEffect(() => { fetchBiomassa(); }, [search]);

  const fetchBiomassa = async () => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/biomassa`, { headers: getAuthHeader(), params });
      setBiomassaList(response.data);
    } catch (error) {
      toast.error("Gagal memuat data biomassa");
    } finally {
      setLoading(false);
    }
  };

  const parseFloat2 = (val) => val ? parseFloat(val) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const dataToSend = {
        ...formData,
        durasi_pembongkaran_hari: parseFloat2(formData.durasi_pembongkaran_hari),
        waktu_tunggu_jam: parseFloat2(formData.waktu_tunggu_jam),
        bl_mt: parseFloat2(formData.bl_mt),
        jembatan_timbang_mt: parseFloat2(formData.jembatan_timbang_mt),
        gcv_arb: parseFloat2(formData.gcv_arb),
        gcv_adb: parseFloat2(formData.gcv_adb),
        tm_arb: parseFloat2(formData.tm_arb),
        im_adb: parseFloat2(formData.im_adb)
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

  const biomassTypes = ["WOODCHIP", "SAWDUST", "OIL PALM MESOCARP FIBER"];

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
                      Tindakan ini akan menghapus <span className="text-red-400 font-bold">{biomassaList.length}</span> data biomassa secara permanen. Data yang sudah dihapus tidak dapat dikembalikan.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel className="border-slate-700 text-slate-300">Batal</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDeleteAll} disabled={deleting} className="bg-red-600 hover:bg-red-500">
                      {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                      Ya, Hapus Semua
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
                    <p className="text-slate-500 text-xs mb-4">Pastikan header Excel sesuai dengan format Biomassa PLTU Tenayan</p>
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
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-4xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingBiomassa ? "Edit Data Biomassa" : "Tambah Data Biomassa"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[75vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4" data-testid="biomassa-form">
                    <Tabs defaultValue="shipment" className="w-full">
                      <TabsList className="grid w-full grid-cols-4 bg-slate-900/50">
                        <TabsTrigger value="shipment" className="text-xs data-[state=active]:bg-green-500/20">Shipment</TabsTrigger>
                        <TabsTrigger value="waktu" className="text-xs data-[state=active]:bg-green-500/20">Waktu</TabsTrigger>
                        <TabsTrigger value="muatan" className="text-xs data-[state=active]:bg-green-500/20">Muatan</TabsTrigger>
                        <TabsTrigger value="kualitas" className="text-xs data-[state=active]:bg-green-500/20">Kualitas</TabsTrigger>
                      </TabsList>
                      
                      <TabsContent value="shipment" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">Informasi Shipment</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="Periode" name="periode" placeholder="Jan-25" />
                          <FormField label="Shipment Code" name="shipment_code" />
                          <FormField label="Voyage Code" name="voyage_code" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="Lot" name="lot" />
                          <FormField label="Suppliers" name="suppliers" />
                          <FormField label="Shipper" name="shipper" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="Lot Detail" name="lot_detail" />
                          <FormField label="TB (Tug Boat)" name="tb" />
                          <FormField label="BG (Barge)" name="bg" />
                          <div className="space-y-2">
                            <Label className="text-slate-300 text-xs">Jenis Biomassa</Label>
                            <Select 
                              value={formData.biomass_type} 
                              onValueChange={(value) => setFormData({...formData, biomass_type: value})}
                            >
                              <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white h-9 text-sm" data-testid="select-biomass-type">
                                <SelectValue placeholder="Pilih jenis" />
                              </SelectTrigger>
                              <SelectContent className="bg-[#0B1221] border-slate-800">
                                {biomassTypes.map(type => (
                                  <SelectItem key={type} value={type} className="text-white hover:bg-slate-800">{type}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="waktu" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">Waktu Operasional</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="Time Arrival (TA)" name="ta" />
                          <FormField label="Berthed Time" name="berthed_time" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="Commenced Unloading" name="commenced_unloading" />
                          <FormField label="Completed Unloading" name="completed_unloading" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="Durasi Pembongkaran (Hari)" name="durasi_pembongkaran_hari" type="number" />
                          <FormField label="Waktu Tunggu (Jam)" name="waktu_tunggu_jam" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="muatan" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">Data Muatan</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="B/L (MT)" name="bl_mt" type="number" />
                          <FormField label="Jembatan Timbang (MT)" name="jembatan_timbang_mt" type="number" />
                          <FormField label="Surveyor" name="surveyor" />
                        </div>
                        <h4 className="text-sm font-mono text-green-400 mt-4">COW/ROW</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="NO. COW" name="no_cow" />
                          <FormField label="Tgl Terbit COW" name="tgl_terbit_cow" />
                          <FormField label="Lama Terbit ROW" name="lama_terbit_row" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="kualitas" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-green-400">Data Kualitas</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="GCV ARB (Kcal/Kg)" name="gcv_arb" type="number" />
                          <FormField label="GCV ADB (Kcal/Kg)" name="gcv_adb" type="number" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="TM ARB (%wt)" name="tm_arb" type="number" />
                          <FormField label="IM ADB (%wt)" name="im_adb" type="number" />
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
              placeholder="Cari shipment, supplier, jenis..."
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
                <TableHead className="text-slate-400 font-mono text-xs">Jenis</TableHead>
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
              ) : biomassaList.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                    Belum ada data biomassa
                  </TableCell>
                </TableRow>
              ) : (
                biomassaList.map((biomassa) => (
                  <TableRow key={biomassa.id} className="border-white/5 hover:bg-slate-900/50" data-testid={`biomassa-row-${biomassa.id}`}>
                    <TableCell className="text-slate-300 text-sm">{biomassa.periode}</TableCell>
                    <TableCell className="text-white font-medium text-sm">{biomassa.shipment_code}</TableCell>
                    <TableCell className="text-slate-300 text-sm">{biomassa.suppliers}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        biomassa.biomass_type === 'WOODCHIP' ? 'bg-emerald-500/20 text-emerald-400' :
                        biomassa.biomass_type === 'SAWDUST' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-orange-500/20 text-orange-400'
                      }`}>
                        {biomassa.biomass_type}
                      </span>
                    </TableCell>
                    <TableCell className="text-slate-300 text-sm font-mono">{biomassa.bl_mt?.toLocaleString() || '-'}</TableCell>
                    <TableCell className="text-green-400 text-sm font-mono">{biomassa.gcv_arb?.toLocaleString() || '-'}</TableCell>
                    <TableCell>
                      {canEdit && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" data-testid={`action-btn-${biomassa.id}`}>
                              <MoreHorizontal className="h-4 w-4 text-slate-400" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-[#0B1221] border-slate-800">
                            <DropdownMenuItem onClick={() => handleEdit(biomassa)} className="text-slate-300 hover:bg-slate-800 cursor-pointer">
                              <Edit className="w-4 h-4 mr-2" />Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleDelete(biomassa.id)} className="text-red-400 hover:bg-slate-800 cursor-pointer">
                              <Trash2 className="w-4 h-4 mr-2" />Hapus
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Card>
    </div>
  );
};

export default BiomassaPage;
