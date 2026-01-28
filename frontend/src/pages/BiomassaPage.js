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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Leaf, Plus, Search, Upload, MoreHorizontal, Edit, Trash2, Loader2, FileSpreadsheet, AlertTriangle } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const BiomassaPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [biomassa, setBiomassa] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editingBiomassa, setEditingBiomassa] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const fileInputRef = useRef(null);

  const initialFormData = {
    periode: "", shipment_code: "", voyage_code: "", lot: "", suppliers: "", shipper: "",
    lot_detail: "", tb: "", bg: "", biomass_type: "", ta: "", berthed_time: "",
    commenced_unloading: "", completed_unloading: "", durasi_pembongkaran_hari: "", waktu_tunggu_jam: "",
    bl_mt: "", jembatan_timbang_mt: "", surveyor: "", no_cow: "", tgl_terbit_cow: "", lama_terbit_row: "",
    gcv_arb: "", gcv_adb: "", tm_arb: "", im_adb: "", no_coa: "", tgl_terbit_coa: "", durasi_terbit_coa: ""
  };

  const [formData, setFormData] = useState(initialFormData);

  useEffect(() => { fetchBiomassa(); }, [search]);

  const fetchBiomassa = async () => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/biomassa`, { headers: getAuthHeader(), params });
      setBiomassa(response.data);
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
      const dataToSend = { ...formData };
      const numericFields = ['durasi_pembongkaran_hari', 'waktu_tunggu_jam', 'bl_mt', 'jembatan_timbang_mt',
        'gcv_arb', 'gcv_adb', 'tm_arb', 'im_adb'];
      numericFields.forEach(f => { dataToSend[f] = parseFloat2(formData[f]); });

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

  const handleEdit = (item) => {
    setEditingBiomassa(item);
    const newFormData = {};
    Object.keys(initialFormData).forEach(key => {
      const val = item[key];
      newFormData[key] = val !== null && val !== undefined ? String(val) : "";
    });
    setFormData(newFormData);
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;
    try {
      await axios.delete(`${API_URL}/api/biomassa/${id}`, { headers: getAuthHeader() });
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
    const fd = new FormData();
    fd.append("file", file);
    setSubmitting(true);
    try {
      const response = await axios.post(`${API_URL}/api/upload/biomassa`, fd, {
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

  const resetForm = () => { setFormData(initialFormData); setEditingBiomassa(null); };
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

  const getBiomassTypeBadge = (type) => {
    const colors = {
      "WOODCHIP": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      "SAWDUST": "bg-amber-500/20 text-amber-400 border-amber-500/30",
      "OIL PALM MESOCARP FIBER": "bg-orange-500/20 text-orange-400 border-orange-500/30"
    };
    return colors[type] || "bg-slate-500/20 text-slate-400 border-slate-500/30";
  };

  return (
    <div className="space-y-6" data-testid="biomassa-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Leaf className="w-8 h-8 text-emerald-400" />
            Biomassa TNY
          </h1>
          <p className="text-slate-400 mt-1">Data penerimaan biomassa ({biomassa.length} data)</p>
        </div>
        {canEdit && (
          <div className="flex flex-wrap gap-3">
            {isAdmin && biomassa.length > 0 && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10" data-testid="delete-all-biomassa-btn">
                    <Trash2 className="w-4 h-4 mr-2" />Hapus Semua
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="bg-[#0B1221] border-white/10">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-white flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-400" />Hapus Semua Data Biomassa?
                    </AlertDialogTitle>
                    <AlertDialogDescription className="text-slate-400">
                      Tindakan ini akan menghapus <span className="text-red-400 font-bold">{biomassa.length}</span> data biomassa secara permanen.
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
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="biomassa-upload-btn">
                  <Upload className="w-4 h-4 mr-2" />Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel Biomassa</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-emerald-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-2">Format kolom Excel harus sesuai template</p>
                    <p className="text-slate-500 text-xs mb-4">Kolom: Periode, LOT, Suppliers, Shipper, Biomass, dll</p>
                    <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileUpload} className="hidden" />
                    <Button onClick={() => fileInputRef.current?.click()} disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Pilih File
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-emerald-600 hover:bg-emerald-500" data-testid="add-biomassa-btn">
                  <Plus className="w-4 h-4 mr-2" />Tambah Data
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-4xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingBiomassa ? "Edit Data Biomassa" : "Tambah Data Biomassa"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[75vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    {/* Informasi Shipment */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">Informasi Shipment</h3>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <FormField label="Periode" name="periode" />
                        <FormField label="Shipment Code" name="shipment_code" />
                        <FormField label="Voyage Code" name="voyage_code" />
                        <FormField label="LOT" name="lot" />
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <FormField label="Suppliers" name="suppliers" />
                        <FormField label="Shipper" name="shipper" />
                        <FormField label="LOT Detail" name="lot_detail" />
                        <div className="space-y-2">
                          <Label className="text-slate-300 text-xs">Jenis Biomassa</Label>
                          <Select value={formData.biomass_type} onValueChange={(value) => setFormData({...formData, biomass_type: value})}>
                            <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white h-9">
                              <SelectValue placeholder="Pilih jenis" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#0B1221] border-white/10">
                              <SelectItem value="WOODCHIP" className="text-slate-300 focus:bg-white/5 focus:text-white">Woodchip</SelectItem>
                              <SelectItem value="SAWDUST" className="text-slate-300 focus:bg-white/5 focus:text-white">Sawdust</SelectItem>
                              <SelectItem value="OIL PALM MESOCARP FIBER" className="text-slate-300 focus:bg-white/5 focus:text-white">Oil Palm Mesocarp Fiber</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField label="TB (Tug Boat)" name="tb" />
                        <FormField label="BG (Barge)" name="bg" />
                      </div>
                    </div>

                    {/* Waktu Operasional */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">Waktu Operasional</h3>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <FormField label="TA (Time Arrival)" name="ta" />
                        <FormField label="Berthed Time" name="berthed_time" />
                        <FormField label="Commenced Unloading" name="commenced_unloading" />
                        <FormField label="Completed Unloading" name="completed_unloading" />
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField label="Durasi Pembongkaran (Hari)" name="durasi_pembongkaran_hari" type="number" />
                        <FormField label="Waktu Tunggu (Jam)" name="waktu_tunggu_jam" type="number" />
                      </div>
                    </div>

                    {/* Muatan */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">Data Muatan</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <FormField label="B/L (MT)" name="bl_mt" type="number" />
                        <FormField label="Jembatan Timbang (MT)" name="jembatan_timbang_mt" type="number" />
                        <FormField label="Surveyor" name="surveyor" />
                      </div>
                    </div>

                    {/* COW/ROW */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">COW / ROW</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <FormField label="NO. ROW" name="no_cow" />
                        <FormField label="Tgl Terbit ROW" name="tgl_terbit_cow" />
                        <FormField label="Lama Terbit ROW (Hari)" name="lama_terbit_row" />
                      </div>
                    </div>

                    {/* Kualitas */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">Data Kualitas</h3>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <FormField label="GCV ARB (Kcal/Kg)" name="gcv_arb" type="number" />
                        <FormField label="GCV ADB (Kcal/Kg)" name="gcv_adb" type="number" />
                        <FormField label="TM ARB (%wt)" name="tm_arb" type="number" />
                        <FormField label="IM ADB (%wt)" name="im_adb" type="number" />
                      </div>
                    </div>

                    {/* COA */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">COA</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <FormField label="NO. COA" name="no_coa" />
                        <FormField label="Tgl Terbit COA" name="tgl_terbit_coa" />
                        <FormField label="Durasi Terbit COA" name="durasi_terbit_coa" />
                      </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">Batal</Button>
                      <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500" data-testid="biomassa-submit-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {editingBiomassa ? "Simpan Perubahan" : "Tambah Data"}
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
        <Input placeholder="Cari shipment code, supplier, jenis biomassa..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10 bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600" data-testid="biomassa-search-input" />
      </div>

      <Card className="glass-card border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400 font-mono text-xs">PERIODE</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">SHIPMENT CODE</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">LOT</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">SUPPLIER</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">JENIS</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">J. TIMBANG (MT)</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">GCV ARB</TableHead>
                {canEdit && <TableHead className="text-slate-400 font-mono text-xs w-12"></TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={canEdit ? 8 : 7} className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-emerald-400" /></TableCell></TableRow>
              ) : biomassa.length === 0 ? (
                <TableRow><TableCell colSpan={canEdit ? 8 : 7} className="text-center py-12 text-slate-500">Tidak ada data biomassa</TableCell></TableRow>
              ) : (
                biomassa.map((item) => (
                  <TableRow key={item.id} className="border-white/5 hover:bg-white/5">
                    <TableCell className="text-slate-300 font-mono text-sm">{item.periode}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{item.shipment_code}</TableCell>
                    <TableCell className="text-white font-medium">{item.lot}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[120px] truncate">{item.suppliers}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 text-xs rounded-full border ${getBiomassTypeBadge(item.biomass_type)}`}>
                        {item.biomass_type || "-"}
                      </span>
                    </TableCell>
                    <TableCell className="text-emerald-400 font-mono">{item.jembatan_timbang_mt?.toLocaleString() || "-"}</TableCell>
                    <TableCell className="text-amber-400 font-mono">{item.gcv_arb?.toLocaleString() || "-"}</TableCell>
                    {canEdit && (
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="text-slate-400 hover:text-white"><MoreHorizontal className="w-4 h-4" /></Button></DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-[#0B1221] border-white/10">
                            <DropdownMenuItem onClick={() => handleEdit(item)} className="text-slate-300 focus:text-white focus:bg-white/5"><Edit className="w-4 h-4 mr-2" />Edit</DropdownMenuItem>
                            {isAdmin && (<DropdownMenuItem onClick={() => handleDelete(item.id)} className="text-red-400 focus:text-red-300 focus:bg-red-500/10"><Trash2 className="w-4 h-4 mr-2" />Hapus</DropdownMenuItem>)}
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

export default BiomassaPage;
