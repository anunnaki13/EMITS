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
import { Truck, Plus, Search, Upload, MoreHorizontal, Edit, Trash2, Loader2, FileSpreadsheet, AlertTriangle } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TruckingPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [trucking, setTrucking] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editingTrucking, setEditingTrucking] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    periode: "", shipment_code: "", suppliers: "", no_truck: "", driver_name: "",
    origin: "", destination: "", pickup_date: "", delivery_date: "",
    weight_mt: "", no_cow: "", gcv_arb: "", tm_arb: ""
  });

  useEffect(() => { fetchTrucking(); }, [search]);

  const fetchTrucking = async () => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/trucking`, { headers: getAuthHeader(), params });
      setTrucking(response.data);
    } catch (error) {
      toast.error("Gagal memuat data trucking");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const dataToSend = {
        ...formData,
        weight_mt: formData.weight_mt ? parseFloat(formData.weight_mt) : null,
        gcv_arb: formData.gcv_arb ? parseFloat(formData.gcv_arb) : null,
        tm_arb: formData.tm_arb ? parseFloat(formData.tm_arb) : null
      };
      if (editingTrucking) {
        await axios.put(`${API_URL}/api/trucking/${editingTrucking.id}`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data trucking berhasil diperbarui");
      } else {
        await axios.post(`${API_URL}/api/trucking`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data trucking berhasil ditambahkan");
      }
      setDialogOpen(false);
      resetForm();
      fetchTrucking();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menyimpan data");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (item) => {
    setEditingTrucking(item);
    setFormData({
      periode: item.periode || "", shipment_code: item.shipment_code || "",
      suppliers: item.suppliers || "", no_truck: item.no_truck || "",
      driver_name: item.driver_name || "", origin: item.origin || "",
      destination: item.destination || "", pickup_date: item.pickup_date || "",
      delivery_date: item.delivery_date || "", weight_mt: item.weight_mt?.toString() || "",
      no_cow: item.no_cow || "", gcv_arb: item.gcv_arb?.toString() || "",
      tm_arb: item.tm_arb?.toString() || ""
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;
    try {
      await axios.delete(`${API_URL}/api/trucking/${id}`, { headers: getAuthHeader() });
      toast.success("Data trucking berhasil dihapus");
      fetchTrucking();
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
      const response = await axios.post(`${API_URL}/api/upload/trucking`, formData, {
        headers: { ...getAuthHeader(), "Content-Type": "multipart/form-data" }
      });
      toast.success(response.data.message);
      setUploadDialogOpen(false);
      fetchTrucking();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal mengupload file");
    } finally {
      setSubmitting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const resetForm = () => {
    setFormData({
      periode: "", shipment_code: "", suppliers: "", no_truck: "", driver_name: "",
      origin: "", destination: "", pickup_date: "", delivery_date: "",
      weight_mt: "", no_cow: "", gcv_arb: "", tm_arb: ""
    });
    setEditingTrucking(null);
  };

  const canEdit = user?.role === "admin" || user?.role === "operator";

  return (
    <div className="space-y-6" data-testid="trucking-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Truck className="w-8 h-8 text-amber-400" />
            Trucking TNY
          </h1>
          <p className="text-slate-400 mt-1">Data pengiriman batubara via truk</p>
        </div>
        {canEdit && (
          <div className="flex gap-3">
            <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="trucking-upload-btn">
                  <Upload className="w-4 h-4 mr-2" />Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-amber-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-4">Pilih file Excel (.xlsx, .xls)</p>
                    <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileUpload} className="hidden" />
                    <Button onClick={() => fileInputRef.current?.click()} disabled={submitting} className="bg-amber-600 hover:bg-amber-500">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Pilih File
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-amber-600 hover:bg-amber-500" data-testid="add-trucking-btn">
                  <Plus className="w-4 h-4 mr-2" />Tambah Data
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-3xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingTrucking ? "Edit Data Trucking" : "Tambah Data Trucking"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[70vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-amber-400">Informasi Shipment</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Periode</Label><Input value={formData.periode} onChange={(e) => setFormData({...formData, periode: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" placeholder="Jan-25" required data-testid="trucking-periode" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Shipment Code</Label><Input value={formData.shipment_code} onChange={(e) => setFormData({...formData, shipment_code: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="trucking-shipment-code" /></div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Supplier</Label><Input value={formData.suppliers} onChange={(e) => setFormData({...formData, suppliers: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="trucking-suppliers" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">No. Truk</Label><Input value={formData.no_truck} onChange={(e) => setFormData({...formData, no_truck: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="trucking-no-truck" /></div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-amber-400">Informasi Pengiriman</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Nama Sopir</Label><Input value={formData.driver_name} onChange={(e) => setFormData({...formData, driver_name: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Berat (MT)</Label><Input type="number" step="0.001" value={formData.weight_mt} onChange={(e) => setFormData({...formData, weight_mt: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" data-testid="trucking-weight" /></div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">Asal</Label><Input value={formData.origin} onChange={(e) => setFormData({...formData, origin: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="trucking-origin" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">Tujuan</Label><Input value={formData.destination} onChange={(e) => setFormData({...formData, destination: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" required data-testid="trucking-destination" /></div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-amber-400">Data Kualitas</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2"><Label className="text-slate-300">GCV ARB (Kcal/Kg)</Label><Input type="number" value={formData.gcv_arb} onChange={(e) => setFormData({...formData, gcv_arb: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                        <div className="space-y-2"><Label className="text-slate-300">TM ARB (%)</Label><Input type="number" step="0.01" value={formData.tm_arb} onChange={(e) => setFormData({...formData, tm_arb: e.target.value})} className="bg-slate-950/50 border-slate-800 text-white" /></div>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">Batal</Button>
                      <Button type="submit" disabled={submitting} className="bg-amber-600 hover:bg-amber-500" data-testid="trucking-submit-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}{editingTrucking ? "Simpan Perubahan" : "Tambah Data"}
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
        <Input placeholder="Cari shipment code, no truk, supplier..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10 bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600" data-testid="trucking-search-input" />
      </div>

      <Card className="glass-card border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400 font-mono text-xs">PERIODE</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">SHIPMENT CODE</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">NO. TRUK</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">SUPPLIER</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">ASAL</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">TUJUAN</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">BERAT (MT)</TableHead>
                {canEdit && <TableHead className="text-slate-400 font-mono text-xs w-12"></TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={canEdit ? 8 : 7} className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-amber-400" /></TableCell></TableRow>
              ) : trucking.length === 0 ? (
                <TableRow><TableCell colSpan={canEdit ? 8 : 7} className="text-center py-12 text-slate-500">Tidak ada data trucking</TableCell></TableRow>
              ) : (
                trucking.map((item) => (
                  <TableRow key={item.id} className="border-white/5 hover:bg-white/5">
                    <TableCell className="text-slate-300 font-mono text-sm">{item.periode}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[200px] truncate">{item.shipment_code}</TableCell>
                    <TableCell className="text-white font-medium">{item.no_truck}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{item.suppliers}</TableCell>
                    <TableCell className="text-slate-400 text-sm">{item.origin}</TableCell>
                    <TableCell className="text-slate-400 text-sm">{item.destination}</TableCell>
                    <TableCell className="text-amber-400 font-mono">{item.weight_mt?.toLocaleString() || "-"}</TableCell>
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

export default TruckingPage;
