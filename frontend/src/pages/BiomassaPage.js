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

  const [formData, setFormData] = useState({
    periode: "", shipment_code: "", lot: "", suppliers: "", shipper: "",
    biomass_type: "", berthed_time: "", commenced: "", completed: "",
    durasi_pembongkaran: "", jembatan_timbang_mt: "", surveyor: "",
    no_cow: "", tgl_terbit_cow: "", gcv_arb: "", gcv_adb: "",
    tm_arb: "", im_arb: "", no_coa: "", tgl_terbit_coa: ""
  });

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const dataToSend = {
        ...formData,
        durasi_pembongkaran: formData.durasi_pembongkaran ? parseFloat(formData.durasi_pembongkaran) : null,
        jembatan_timbang_mt: formData.jembatan_timbang_mt ? parseFloat(formData.jembatan_timbang_mt) : null,
        gcv_arb: formData.gcv_arb ? parseFloat(formData.gcv_arb) : null,
        gcv_adb: formData.gcv_adb ? parseFloat(formData.gcv_adb) : null,
        tm_arb: formData.tm_arb ? parseFloat(formData.tm_arb) : null,
        im_arb: formData.im_arb ? parseFloat(formData.im_arb) : null
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

  const handleEdit = (item) => {
    setEditingBiomassa(item);
    setFormData({
      periode: item.periode || "", shipment_code: item.shipment_code || "",
      lot: item.lot || "", suppliers: item.suppliers || "",
      shipper: item.shipper || "", biomass_type: item.biomass_type || "",
      berthed_time: item.berthed_time || "", commenced: item.commenced || "",
      completed: item.completed || "", durasi_pembongkaran: item.durasi_pembongkaran?.toString() || "",
      jembatan_timbang_mt: item.jembatan_timbang_mt?.toString() || "",
      surveyor: item.surveyor || "", no_cow: item.no_cow || "",
      tgl_terbit_cow: item.tgl_terbit_cow || "", gcv_arb: item.gcv_arb?.toString() || "",
      gcv_adb: item.gcv_adb?.toString() || "", tm_arb: item.tm_arb?.toString() || "",
      im_arb: item.im_arb?.toString() || "", no_coa: item.no_coa || "",
      tgl_terbit_coa: item.tgl_terbit_coa || ""
    });
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

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setSubmitting(true);
    try {
      const response = await axios.post(`${API_URL}/api/upload/biomassa`, formData, {
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
    setFormData({
      periode: "", shipment_code: "", lot: "", suppliers: "", shipper: "",
      biomass_type: "", berthed_time: "", commenced: "", completed: "",
      durasi_pembongkaran: "", jembatan_timbang_mt: "", surveyor: "",
      no_cow: "", tgl_terbit_cow: "", gcv_arb: "", gcv_adb: "",
      tm_arb: "", im_arb: "", no_coa: "", tgl_terbit_coa: ""
    });
    setEditingBiomassa(null);
  };

  const canEdit = user?.role === "admin" || user?.role === "operator";

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
          <p className="text-slate-400 mt-1">Data penerimaan biomassa (Woodchip, Sawdust, Palm Fiber)</p>
        </div>
        {canEdit && (
          <div className="flex gap-3">
            <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="biomassa-upload-btn">
                  <Upload className="w-4 h-4 mr-2" />Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-emerald-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-4">Pilih file Excel (.xlsx, .xls)</p>
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
                <ScrollArea className="max-h-[70vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">Informasi Shipment</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Periode</Label><Input value={formData.periode} onChange={(e) => setFormData({...formData, periode: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" placeholder="Jan-25" required data-testid="biomassa-periode" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Shipment Code</Label><Input value={formData.shipment_code} onChange={(e) => setFormData({...formData, shipment_code: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="biomassa-shipment-code" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Lot</Label><Input value={formData.lot} onChange={(e) => setFormData({...formData, lot: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="biomassa-lot" /></div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Supplier</Label><Input value={formData.suppliers} onChange={(e) => setFormData({...formData, suppliers: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="biomassa-suppliers" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Shipper</Label><Input value={formData.shipper} onChange={(e) => setFormData({...formData, shipper: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="biomassa-shipper" /></div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Jenis Biomassa</Label>
                          <Select value={formData.biomass_type} onValueChange={(value) => setFormData({...formData, biomass_type: value})}>
                            <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white" data-testid="biomassa-type-select">
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
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">Data Muatan</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Jembatan Timbang (MT)</Label><Input type="number" step="0.001" value={formData.jembatan_timbang_mt} onChange={(e) => setFormData({...formData, jembatan_timbang_mt: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" data-testid="biomassa-weight" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Surveyor</Label><Input value={formData.surveyor} onChange={(e) => setFormData({...formData, surveyor: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-emerald-400">Data Kualitas</h3>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">GCV ARB (Kcal/Kg)</Label><Input type="number" value={formData.gcv_arb} onChange={(e) => setFormData({...formData, gcv_arb: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">GCV ADB (Kcal/Kg)</Label><Input type="number" value={formData.gcv_adb} onChange={(e) => setFormData({...formData, gcv_adb: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">TM ARB (%)</Label><Input type="number" step="0.01" value={formData.tm_arb} onChange={(e) => setFormData({...formData, tm_arb: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">IM ARB (%)</Label><Input type="number" step="0.01" value={formData.im_arb} onChange={(e) => setFormData({...formData, im_arb: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">Batal</Button>
                      <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500" data-testid="biomassa-submit-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}{editingBiomassa ? "Simpan Perubahan" : "Tambah Data"}
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
                <TableHead className="text-slate-400 font-mono text-xs">BERAT (MT)</TableHead>
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
                    <TableCell className="text-slate-300 text-sm max-w-[200px] truncate">{item.shipment_code}</TableCell>
                    <TableCell className="text-white font-medium">{item.lot}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{item.suppliers}</TableCell>
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
                            {user?.role === "admin" && (<DropdownMenuItem onClick={() => handleDelete(item.id)} className="text-red-400 focus:text-red-300 focus:bg-red-500/10"><Trash2 className="w-4 h-4 mr-2" />Hapus</DropdownMenuItem>)}
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
