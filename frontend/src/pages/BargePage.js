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
import { Anchor, Plus, Search, Upload, MoreHorizontal, Edit, Trash2, Loader2, FileSpreadsheet, AlertTriangle } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

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
  const fileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    periode_ta: "", periode_realisasi: "", shipment_code: "", voyage_code: "",
    suppliers: "", voyage: "", name_of_barge: "", coal_from: "",
    time_arrival: "", berthed: "", time_commenced_unloading: "", completed_unloading: "",
    durasi_pembongkaran_hari: "", bl_mt: "", ds_mt: "", no_cow: "",
    tgl_terbit_cow: "", gcv_arb: "", tm_arb: "", no_coa: ""
  });

  useEffect(() => { fetchBarges(); }, [search]);

  const fetchBarges = async () => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/barges`, { headers: getAuthHeader(), params });
      setBarges(response.data);
    } catch (error) {
      toast.error("Gagal memuat data barge");
    } finally {
      setLoading(false);
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const dataToSend = {
        ...formData,
        durasi_pembongkaran_hari: formData.durasi_pembongkaran_hari ? parseFloat(formData.durasi_pembongkaran_hari) : null,
        bl_mt: formData.bl_mt ? parseFloat(formData.bl_mt) : null,
        ds_mt: formData.ds_mt ? parseFloat(formData.ds_mt) : null,
        gcv_arb: formData.gcv_arb ? parseFloat(formData.gcv_arb) : null,
        tm_arb: formData.tm_arb ? parseFloat(formData.tm_arb) : null
      };
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
    setFormData({
      periode_ta: barge.periode_ta || "", periode_realisasi: barge.periode_realisasi || "",
      shipment_code: barge.shipment_code || "", voyage_code: barge.voyage_code || "",
      suppliers: barge.suppliers || "", voyage: barge.voyage || "",
      name_of_barge: barge.name_of_barge || "", coal_from: barge.coal_from || "",
      time_arrival: barge.time_arrival || "", berthed: barge.berthed || "",
      time_commenced_unloading: barge.time_commenced_unloading || "", completed_unloading: barge.completed_unloading || "",
      durasi_pembongkaran_hari: barge.durasi_pembongkaran_hari?.toString() || "",
      bl_mt: barge.bl_mt?.toString() || "", ds_mt: barge.ds_mt?.toString() || "",
      no_cow: barge.no_cow || "", tgl_terbit_cow: barge.tgl_terbit_cow || "",
      gcv_arb: barge.gcv_arb?.toString() || "", tm_arb: barge.tm_arb?.toString() || "",
      no_coa: barge.no_coa || ""
    });
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

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setSubmitting(true);
    try {
      const response = await axios.post(`${API_URL}/api/upload/barge`, formData, {
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

  const resetForm = () => {
    setFormData({
      periode_ta: "", periode_realisasi: "", shipment_code: "", voyage_code: "",
      suppliers: "", voyage: "", name_of_barge: "", coal_from: "",
      time_arrival: "", berthed: "", time_commenced_unloading: "", completed_unloading: "",
      durasi_pembongkaran_hari: "", bl_mt: "", ds_mt: "", no_cow: "",
      tgl_terbit_cow: "", gcv_arb: "", tm_arb: "", no_coa: ""
    });
    setEditingBarge(null);
  };

  const canEdit = user?.role === "admin" || user?.role === "operator";
  const isAdmin = user?.role === "admin";

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
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                      Hapus Semua Data Barge?
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
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-blue-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-4">Pilih file Excel (.xlsx, .xls)</p>
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
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-4xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingBarge ? "Edit Data Barge" : "Tambah Data Barge"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[70vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-blue-400">Informasi Shipment</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Periode TA</Label><Input value={formData.periode_ta} onChange={(e) => setFormData({...formData, periode_ta: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="barge-periode-ta" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Periode Realisasi</Label><Input value={formData.periode_realisasi} onChange={(e) => setFormData({...formData, periode_realisasi: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Shipment Code</Label><Input value={formData.shipment_code} onChange={(e) => setFormData({...formData, shipment_code: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="barge-shipment-code" /></div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Voyage Code</Label><Input value={formData.voyage_code} onChange={(e) => setFormData({...formData, voyage_code: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Supplier</Label><Input value={formData.suppliers} onChange={(e) => setFormData({...formData, suppliers: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="barge-suppliers" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Voyage</Label><Input value={formData.voyage} onChange={(e) => setFormData({...formData, voyage: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required /></div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-blue-400">Informasi Tongkang</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Nama Barge</Label><Input value={formData.name_of_barge} onChange={(e) => setFormData({...formData, name_of_barge: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="barge-name" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Asal Batubara</Label><Input value={formData.coal_from} onChange={(e) => setFormData({...formData, coal_from: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required /></div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-blue-400">Data Muatan</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">B/L (MT)</Label><Input type="number" step="0.001" value={formData.bl_mt} onChange={(e) => setFormData({...formData, bl_mt: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" data-testid="barge-bl-mt" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">DS (MT)</Label><Input type="number" step="0.001" value={formData.ds_mt} onChange={(e) => setFormData({...formData, ds_mt: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" data-testid="barge-ds-mt" /></div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-blue-400">Data Kualitas</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">GCV ARB (Kcal/Kg)</Label><Input type="number" value={formData.gcv_arb} onChange={(e) => setFormData({...formData, gcv_arb: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">TM ARB (%)</Label><Input type="number" step="0.01" value={formData.tm_arb} onChange={(e) => setFormData({...formData, tm_arb: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">Batal</Button>
                      <Button type="submit" disabled={submitting} className="bg-blue-600 hover:bg-blue-500" data-testid="barge-submit-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}{editingBarge ? "Simpan Perubahan" : "Tambah Data"}
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
                <TableHead className="text-slate-400 font-mono text-xs">BARGE</TableHead>
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
                    <TableCell className="text-slate-300 font-mono text-sm">{barge.periode_ta}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[200px] truncate">{barge.shipment_code}</TableCell>
                    <TableCell className="text-white font-medium">{barge.name_of_barge}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{barge.suppliers}</TableCell>
                    <TableCell className="text-slate-400 text-sm max-w-[150px] truncate">{barge.coal_from}</TableCell>
                    <TableCell className="text-blue-400 font-mono">{barge.ds_mt?.toLocaleString() || "-"}</TableCell>
                    <TableCell className="text-amber-400 font-mono">{barge.gcv_arb?.toLocaleString() || "-"}</TableCell>
                    {canEdit && (
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="text-slate-400 hover:text-white"><MoreHorizontal className="w-4 h-4" /></Button></DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-[#0B1221] border-white/10">
                            <DropdownMenuItem onClick={() => handleEdit(barge)} className="text-slate-300 focus:text-white focus:bg-white/5"><Edit className="w-4 h-4 mr-2" />Edit</DropdownMenuItem>
                            {user?.role === "admin" && (<DropdownMenuItem onClick={() => handleDelete(barge.id)} className="text-red-400 focus:text-red-300 focus:bg-red-500/10"><Trash2 className="w-4 h-4 mr-2" />Hapus</DropdownMenuItem>)}
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
