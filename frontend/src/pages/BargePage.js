import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Anchor, Plus, Search, Upload, MoreHorizontal, Edit, Trash2, Loader2, FileSpreadsheet, AlertTriangle, Eye } from "lucide-react";
import Pagination from "@/components/Pagination";

const API_URL = process.env.REACT_APP_BACKEND_URL;
const ITEMS_PER_PAGE = 100;

const BargePage = () => {
  const { user, getAuthHeader } = useAuth();
  const [barges, setBarges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editingBarge, setEditingBarge] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [viewingBarge, setViewingBarge] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const fileInputRef = useRef(null);

  const initialFormData = {
    periode: "", shipment_code: "", voyage_code: "", shipment: "", suppliers: "", voyage: "",
    tb: "", bg: "", coal_from: "", ta: "", berthed_time: "", commenced_unloading: "", completed_unloading: "",
    durasi_pembongkaran_hari: "", durasi_pembongkaran_jam: "", waktu_tunggu_jam: "",
    bl_mt: "", ds_mt: "", no_cow: "", tgl_terbit_cow: "",
    gcv_arb: "", gcv_adb: "", gcv_db: "", tm_arb: "", im_adb: "",
    ash_arb: "", ash_adb: "", ash_db: "", vm_arb: "", vm_adb: "", fc_arb: "", fc_adb: "",
    ts_arb: "", ts_adb: "", ts_db: "", ts_dafb: "",
    c_arb: "", c_adb: "", h_arb: "", h_adb: "", n_arb: "", n_adb: "", n_dafb: "", o_arb: "", o_adb: "",
    hgi: "", slagging_index: "", fouling_index: "", idt_reducing: "",
    sio2_db: "", al2o3_db: "", tio2_db: "", fe2o3_db: "", cao_db: "", mgo_db: "",
    k2o_db: "", na2o_db: "", so3_db: "", p2o5_db: "", mno2_db: "", mn3o4_db: "",
    size_70mm: "", size_50mm: "", size_32mm: "", size_2_38mm: "",
    no_coa: "", tgl_terbit_coa: "", durasi_terbit_coa: ""
  };

  const [formData, setFormData] = useState(initialFormData);

  useEffect(() => { fetchBarges(); setCurrentPage(1); }, [search]);

  const fetchBarges = async () => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/barges`, { headers: getAuthHeader(), params });
      const sortedData = response.data.reverse();
      setBarges(sortedData);
    } catch (error) {
      toast.error("Gagal memuat data barge");
    } finally {
      setLoading(false);
    }
  };

  const parseFloat2 = (val) => val ? parseFloat(val) : null;

  const totalPages = Math.ceil(barges.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedBarges = barges.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const dataToSend = { ...formData };
      // Convert numeric fields
      const numericFields = ['durasi_pembongkaran_hari', 'durasi_pembongkaran_jam', 'waktu_tunggu_jam',
        'bl_mt', 'ds_mt', 'gcv_arb', 'gcv_adb', 'gcv_db', 'tm_arb', 'im_adb',
        'ash_arb', 'ash_adb', 'ash_db', 'vm_arb', 'vm_adb', 'fc_arb', 'fc_adb',
        'ts_arb', 'ts_adb', 'ts_db', 'ts_dafb', 'c_arb', 'c_adb', 'h_arb', 'h_adb',
        'n_arb', 'n_adb', 'n_dafb', 'o_arb', 'o_adb', 'hgi', 'idt_reducing',
        'sio2_db', 'al2o3_db', 'tio2_db', 'fe2o3_db', 'cao_db', 'mgo_db',
        'k2o_db', 'na2o_db', 'so3_db', 'p2o5_db', 'mno2_db', 'mn3o4_db',
        'size_70mm', 'size_50mm', 'size_32mm', 'size_2_38mm'];
      numericFields.forEach(f => { dataToSend[f] = parseFloat2(formData[f]); });

      if (editingBarge) {
        await axios.put(`${API_URL}/api/barges/${editingBarge.id}`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data barge berhasil diperbarui");
      } else {
        await axios.post(`${API_URL}/api/barges`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data barge berhasil ditambahkan");
      }
      setDialogOpen(false);
      resetForm();
      fetchBarges();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menyimpan data");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (barge) => {
    setEditingBarge(barge);
    const newFormData = {};
    Object.keys(initialFormData).forEach(key => {
      const val = barge[key];
      newFormData[key] = val !== null && val !== undefined ? String(val) : "";
    });
    setFormData(newFormData);
    setDialogOpen(true);
  };

  const handleDelete = async (bargeId) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;
    try {
      await axios.delete(`${API_URL}/api/barges/${bargeId}`, { headers: getAuthHeader() });
      toast.success("Data barge berhasil dihapus");
      fetchBarges();
    } catch (error) {
      toast.error("Gagal menghapus data");
    }
  };

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      const response = await axios.delete(`${API_URL}/api/barges`, { headers: getAuthHeader() });
      toast.success(response.data.message);
      fetchBarges();
    } catch (error) {
      toast.error("Gagal menghapus semua data");
    } finally {
      setDeleting(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    setSubmitting(true);
    try {
      const response = await axios.post(`${API_URL}/api/upload/barge`, fd, {
        headers: { ...getAuthHeader(), "Content-Type": "multipart/form-data" }
      });
      toast.success(response.data.message);
      setUploadDialogOpen(false);
      fetchBarges();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal mengupload file");
    } finally {
      setSubmitting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const resetForm = () => { setFormData(initialFormData); setEditingBarge(null); };
  const canEdit = user?.role === "admin" || user?.role === "operator";
  const isAdmin = user?.role === "admin";

  const FormField = ({ label, name, type = "text" }) => (
    <div className="space-y-2">
      <Label className="text-slate-300 text-xs">{label}</Label>
      <Input type={type} step={type === "number" ? "0.001" : undefined} value={formData[name]}
        onChange={(e) => setFormData({...formData, [name]: e.target.value})}
        className="bg-slate-950/50 border-slate-800 text-white h-9 text-sm" />
    </div>
  );

  return (
    <div className="space-y-6" data-testid="barge-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Anchor className="w-8 h-8 text-blue-400" />
            Barge TNY
          </h1>
          <p className="text-slate-400 mt-1">Data penerimaan batubara via tongkang ({barges.length} data)</p>
        </div>
        {canEdit && (
          <div className="flex flex-wrap gap-3">
            {isAdmin && barges.length > 0 && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10" data-testid="delete-all-barge-btn">
                    <Trash2 className="w-4 h-4 mr-2" />Hapus Semua
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="bg-[#0B1221] border-white/10">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-white flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-400" />Hapus Semua Data Barge?
                    </AlertDialogTitle>
                    <AlertDialogDescription className="text-slate-400">
                      Tindakan ini akan menghapus <span className="text-red-400 font-bold">{barges.length}</span> data barge secara permanen.
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
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="barge-upload-btn">
                  <Upload className="w-4 h-4 mr-2" />Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel Barge</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-blue-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-2">Format kolom Excel harus sesuai template</p>
                    <p className="text-slate-500 text-xs mb-4">Kolom: Periode, Shipment Code, TB, BG, Suppliers, dll</p>
                    <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileUpload} className="hidden" />
                    <Button onClick={() => fileInputRef.current?.click()} disabled={submitting} className="bg-blue-600 hover:bg-blue-500">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Pilih File
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-500" data-testid="add-barge-btn">
                  <Plus className="w-4 h-4 mr-2" />Tambah Data
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-5xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingBarge ? "Edit Data Barge" : "Tambah Data Barge"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[75vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    <Tabs defaultValue="shipment" className="w-full">
                      <TabsList className="grid w-full grid-cols-5 bg-slate-900/50">
                        <TabsTrigger value="shipment" className="text-xs data-[state=active]:bg-blue-500/20">Shipment</TabsTrigger>
                        <TabsTrigger value="muatan" className="text-xs data-[state=active]:bg-blue-500/20">Muatan</TabsTrigger>
                        <TabsTrigger value="kualitas" className="text-xs data-[state=active]:bg-blue-500/20">Kualitas</TabsTrigger>
                        <TabsTrigger value="ultimate" className="text-xs data-[state=active]:bg-blue-500/20">Ultimate</TabsTrigger>
                        <TabsTrigger value="ash" className="text-xs data-[state=active]:bg-blue-500/20">Ash Comp</TabsTrigger>
                      </TabsList>
                      
                      <TabsContent value="shipment" className="space-y-4 mt-4">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="Periode" name="periode" />
                          <FormField label="Shipment Code" name="shipment_code" />
                          <FormField label="Voyage Code" name="voyage_code" />
                          <FormField label="Shipment" name="shipment" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="Suppliers" name="suppliers" />
                          <FormField label="Voyage" name="voyage" />
                          <FormField label="TB (Tug Boat)" name="tb" />
                          <FormField label="BG (Barge)" name="bg" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="Coal From" name="coal_from" />
                          <FormField label="TA (Time Arrival)" name="ta" />
                          <FormField label="Berthed Time" name="berthed_time" />
                          <FormField label="Commenced Unloading" name="commenced_unloading" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="Completed Unloading" name="completed_unloading" />
                          <FormField label="Durasi Pembongkaran (Hari)" name="durasi_pembongkaran_hari" type="number" />
                          <FormField label="Durasi Pembongkaran (Jam)" name="durasi_pembongkaran_jam" type="number" />
                          <FormField label="Waktu Tunggu (Jam)" name="waktu_tunggu_jam" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="muatan" className="space-y-4 mt-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="B/L (MT)" name="bl_mt" type="number" />
                          <FormField label="DS (MT)" name="ds_mt" type="number" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="NO. COW" name="no_cow" />
                          <FormField label="Tgl Terbit COW" name="tgl_terbit_cow" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="NO. COA" name="no_coa" />
                          <FormField label="Tgl Terbit COA" name="tgl_terbit_coa" />
                          <FormField label="Durasi Terbit COA" name="durasi_terbit_coa" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">Size Analysis</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="< 70 mm (%wt)" name="size_70mm" type="number" />
                          <FormField label="< 50 mm (%wt)" name="size_50mm" type="number" />
                          <FormField label="< 32 mm (%wt)" name="size_32mm" type="number" />
                          <FormField label="< 2,38 mm (%wt)" name="size_2_38mm" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="kualitas" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-blue-400">GCV (Kcal/Kg)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="GCV ARB" name="gcv_arb" type="number" />
                          <FormField label="GCV ADB" name="gcv_adb" type="number" />
                          <FormField label="GCV DB" name="gcv_db" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">Moisture (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="TM ARB" name="tm_arb" type="number" />
                          <FormField label="IM ADB" name="im_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">Ash Content (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="Ash ARB" name="ash_arb" type="number" />
                          <FormField label="Ash ADB" name="ash_adb" type="number" />
                          <FormField label="Ash DB" name="ash_db" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">VM & FC (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="VM ARB" name="vm_arb" type="number" />
                          <FormField label="VM ADB" name="vm_adb" type="number" />
                          <FormField label="FC ARB" name="fc_arb" type="number" />
                          <FormField label="FC ADB" name="fc_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">Total Sulphur (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="TS ARB" name="ts_arb" type="number" />
                          <FormField label="TS ADB" name="ts_adb" type="number" />
                          <FormField label="TS DB" name="ts_db" type="number" />
                          <FormField label="TS DAFB" name="ts_dafb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">Index</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="HGI (Point Index)" name="hgi" type="number" />
                          <FormField label="Slagging Index" name="slagging_index" />
                          <FormField label="Fouling Index" name="fouling_index" />
                          <FormField label="IDT Reducing (C°)" name="idt_reducing" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="ultimate" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-blue-400">Carbon (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="C ARB" name="c_arb" type="number" />
                          <FormField label="C ADB" name="c_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">Hydrogen (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="H ARB" name="h_arb" type="number" />
                          <FormField label="H ADB" name="h_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">Nitrogen (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="N ARB" name="n_arb" type="number" />
                          <FormField label="N ADB" name="n_adb" type="number" />
                          <FormField label="N DAFB" name="n_dafb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-blue-400 mt-4">Oxygen (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="O ARB" name="o_arb" type="number" />
                          <FormField label="O ADB" name="o_adb" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="ash" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-blue-400">Ash Composition (%DB)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="SiO2" name="sio2_db" type="number" />
                          <FormField label="Al2O3" name="al2o3_db" type="number" />
                          <FormField label="TiO2" name="tio2_db" type="number" />
                          <FormField label="Fe2O3" name="fe2o3_db" type="number" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="CaO" name="cao_db" type="number" />
                          <FormField label="MgO" name="mgo_db" type="number" />
                          <FormField label="K2O" name="k2o_db" type="number" />
                          <FormField label="Na2O" name="na2o_db" type="number" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="SO3" name="so3_db" type="number" />
                          <FormField label="P2O5" name="p2o5_db" type="number" />
                          <FormField label="MnO2" name="mno2_db" type="number" />
                          <FormField label="Mn3O4" name="mn3o4_db" type="number" />
                        </div>
                      </TabsContent>
                    </Tabs>

                    <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">Batal</Button>
                      <Button type="submit" disabled={submitting} className="bg-blue-600 hover:bg-blue-500" data-testid="barge-submit-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {editingBarge ? "Simpan Perubahan" : "Tambah Data"}
                      </Button>
                    </div>
                  </form>
                </ScrollArea>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <Input placeholder="Cari shipment code, barge, supplier..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10 bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600" data-testid="barge-search-input" />
      </div>

      <Card className="glass-card border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400 font-mono text-xs">PERIODE</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">SHIPMENT CODE</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">TB / BG</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">SUPPLIER</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">ASAL</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">DS (MT)</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">GCV ARB</TableHead>
                {canEdit && <TableHead className="text-slate-400 font-mono text-xs w-12"></TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={canEdit ? 8 : 7} className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-blue-400" /></TableCell></TableRow>
              ) : barges.length === 0 ? (
                <TableRow><TableCell colSpan={canEdit ? 8 : 7} className="text-center py-12 text-slate-500">Tidak ada data barge</TableCell></TableRow>
              ) : (
                barges.map((barge) => (
                  <TableRow key={barge.id} className="border-white/5 hover:bg-white/5">
                    <TableCell className="text-slate-300 font-mono text-sm">{barge.periode}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{barge.shipment_code}</TableCell>
                    <TableCell className="text-white font-medium">{barge.tb} / {barge.bg}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[120px] truncate">{barge.suppliers}</TableCell>
                    <TableCell className="text-slate-400 text-sm max-w-[120px] truncate">{barge.coal_from}</TableCell>
                    <TableCell className="text-blue-400 font-mono">{barge.ds_mt?.toLocaleString() || "-"}</TableCell>
                    <TableCell className="text-amber-400 font-mono">{barge.gcv_arb?.toLocaleString() || "-"}</TableCell>
                    {canEdit && (
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="text-slate-400 hover:text-white"><MoreHorizontal className="w-4 h-4" /></Button></DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-[#0B1221] border-white/10">
                            <DropdownMenuItem onClick={() => handleEdit(barge)} className="text-slate-300 focus:text-white focus:bg-white/5"><Edit className="w-4 h-4 mr-2" />Edit</DropdownMenuItem>
                            {isAdmin && (<DropdownMenuItem onClick={() => handleDelete(barge.id)} className="text-red-400 focus:text-red-300 focus:bg-red-500/10"><Trash2 className="w-4 h-4 mr-2" />Hapus</DropdownMenuItem>)}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    )}
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

export default BargePage;
