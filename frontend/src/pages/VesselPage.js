import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import {
  Ship,
  Plus,
  Search,
  Upload,
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
  FileSpreadsheet,
  X
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const VesselPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [vessels, setVessels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editingVessel, setEditingVessel] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    periode_ta: "",
    periode_realisasi: "",
    shipment_code: "",
    voyage_code: "",
    suppliers: "",
    voyage: "",
    name_of_vessel: "",
    coal_from: "",
    time_arrival: "",
    berthed: "",
    time_commenced_unloading: "",
    completed_unloading: "",
    durasi_pembongkaran_hari: "",
    bl_mt: "",
    ds_mt: "",
    no_cow: "",
    tgl_terbit_cow: "",
    gcv_arb: "",
    gcv_adb: "",
    tm_arb: "",
    im_arb: "",
    ash_arb: "",
    hgi: "",
    slagging_index: "",
    fouling_index: "",
    no_coa: "",
    tgl_terbit_coa: ""
  });

  useEffect(() => {
    fetchVessels();
  }, [search]);

  const fetchVessels = async () => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/vessels`, {
        headers: getAuthHeader(),
        params
      });
      setVessels(response.data);
    } catch (error) {
      console.error("Error fetching vessels:", error);
      toast.error("Gagal memuat data vessel");
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
        durasi_pembongkaran_hari: formData.durasi_pembongkaran_hari ? parseFloat(formData.durasi_pembongkaran_hari) : null,
        bl_mt: formData.bl_mt ? parseFloat(formData.bl_mt) : null,
        ds_mt: formData.ds_mt ? parseFloat(formData.ds_mt) : null,
        gcv_arb: formData.gcv_arb ? parseFloat(formData.gcv_arb) : null,
        gcv_adb: formData.gcv_adb ? parseFloat(formData.gcv_adb) : null,
        tm_arb: formData.tm_arb ? parseFloat(formData.tm_arb) : null,
        im_arb: formData.im_arb ? parseFloat(formData.im_arb) : null,
        ash_arb: formData.ash_arb ? parseFloat(formData.ash_arb) : null,
        hgi: formData.hgi ? parseFloat(formData.hgi) : null
      };

      if (editingVessel) {
        await axios.put(`${API_URL}/api/vessels/${editingVessel.id}`, dataToSend, {
          headers: getAuthHeader()
        });
        toast.success("Data vessel berhasil diperbarui");
      } else {
        await axios.post(`${API_URL}/api/vessels`, dataToSend, {
          headers: getAuthHeader()
        });
        toast.success("Data vessel berhasil ditambahkan");
      }
      setDialogOpen(false);
      resetForm();
      fetchVessels();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menyimpan data");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (vessel) => {
    setEditingVessel(vessel);
    setFormData({
      periode_ta: vessel.periode_ta || "",
      periode_realisasi: vessel.periode_realisasi || "",
      shipment_code: vessel.shipment_code || "",
      voyage_code: vessel.voyage_code || "",
      suppliers: vessel.suppliers || "",
      voyage: vessel.voyage || "",
      name_of_vessel: vessel.name_of_vessel || "",
      coal_from: vessel.coal_from || "",
      time_arrival: vessel.time_arrival || "",
      berthed: vessel.berthed || "",
      time_commenced_unloading: vessel.time_commenced_unloading || "",
      completed_unloading: vessel.completed_unloading || "",
      durasi_pembongkaran_hari: vessel.durasi_pembongkaran_hari?.toString() || "",
      bl_mt: vessel.bl_mt?.toString() || "",
      ds_mt: vessel.ds_mt?.toString() || "",
      no_cow: vessel.no_cow || "",
      tgl_terbit_cow: vessel.tgl_terbit_cow || "",
      gcv_arb: vessel.gcv_arb?.toString() || "",
      gcv_adb: vessel.gcv_adb?.toString() || "",
      tm_arb: vessel.tm_arb?.toString() || "",
      im_arb: vessel.im_arb?.toString() || "",
      ash_arb: vessel.ash_arb?.toString() || "",
      hgi: vessel.hgi?.toString() || "",
      slagging_index: vessel.slagging_index || "",
      fouling_index: vessel.fouling_index || "",
      no_coa: vessel.no_coa || "",
      tgl_terbit_coa: vessel.tgl_terbit_coa || ""
    });
    setDialogOpen(true);
  };

  const handleDelete = async (vesselId) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;
    try {
      await axios.delete(`${API_URL}/api/vessels/${vesselId}`, {
        headers: getAuthHeader()
      });
      toast.success("Data vessel berhasil dihapus");
      fetchVessels();
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
      const response = await axios.post(`${API_URL}/api/upload/vessel`, formData, {
        headers: {
          ...getAuthHeader(),
          "Content-Type": "multipart/form-data"
        }
      });
      toast.success(response.data.message);
      setUploadDialogOpen(false);
      fetchVessels();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal mengupload file");
    } finally {
      setSubmitting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const resetForm = () => {
    setFormData({
      periode_ta: "",
      periode_realisasi: "",
      shipment_code: "",
      voyage_code: "",
      suppliers: "",
      voyage: "",
      name_of_vessel: "",
      coal_from: "",
      time_arrival: "",
      berthed: "",
      time_commenced_unloading: "",
      completed_unloading: "",
      durasi_pembongkaran_hari: "",
      bl_mt: "",
      ds_mt: "",
      no_cow: "",
      tgl_terbit_cow: "",
      gcv_arb: "",
      gcv_adb: "",
      tm_arb: "",
      im_arb: "",
      ash_arb: "",
      hgi: "",
      slagging_index: "",
      fouling_index: "",
      no_coa: "",
      tgl_terbit_coa: ""
    });
    setEditingVessel(null);
  };

  const canEdit = user?.role === "admin" || user?.role === "operator";

  return (
    <div className="space-y-6" data-testid="vessel-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Ship className="w-8 h-8 text-cyan-400" />
            Vessel TNY
          </h1>
          <p className="text-slate-400 mt-1">Data penerimaan batubara via kapal</p>
        </div>
        {canEdit && (
          <div className="flex gap-3">
            <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="upload-excel-btn">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
                <DialogHeader>
                  <DialogTitle className="text-white font-heading">Upload Data Excel</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-cyan-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-4">Pilih file Excel (.xlsx, .xls)</p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="excel-upload"
                    />
                    <Button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={submitting}
                      className="bg-cyan-600 hover:bg-cyan-500"
                    >
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                      Pilih File
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-cyan-600 hover:bg-cyan-500 neon-glow" data-testid="add-vessel-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Tambah Data
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-4xl max-h-[90vh]">
                <DialogHeader>
                  <DialogTitle className="text-white font-heading">
                    {editingVessel ? "Edit Data Vessel" : "Tambah Data Vessel"}
                  </DialogTitle>
                </DialogHeader>
                <ScrollArea className="max-h-[70vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    {/* Informasi Shipment */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-cyan-400">Informasi Shipment</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">Periode TA</Label>
                          <Input
                            value={formData.periode_ta}
                            onChange={(e) => setFormData({...formData, periode_ta: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            placeholder="Jan-25"
                            required
                            data-testid="vessel-periode-ta"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Periode Realisasi</Label>
                          <Input
                            value={formData.periode_realisasi}
                            onChange={(e) => setFormData({...formData, periode_realisasi: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            placeholder="Jan-25"
                            required
                            data-testid="vessel-periode-realisasi"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Shipment Code</Label>
                          <Input
                            value={formData.shipment_code}
                            onChange={(e) => setFormData({...formData, shipment_code: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            placeholder="TENAYAN VESSEL 2025 1 #1"
                            required
                            data-testid="vessel-shipment-code"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">Voyage Code</Label>
                          <Input
                            value={formData.voyage_code}
                            onChange={(e) => setFormData({...formData, voyage_code: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            required
                            data-testid="vessel-voyage-code"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Supplier</Label>
                          <Input
                            value={formData.suppliers}
                            onChange={(e) => setFormData({...formData, suppliers: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            required
                            data-testid="vessel-suppliers"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Voyage</Label>
                          <Input
                            value={formData.voyage}
                            onChange={(e) => setFormData({...formData, voyage: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            required
                            data-testid="vessel-voyage"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Informasi Kapal */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-cyan-400">Informasi Kapal</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">Nama Vessel</Label>
                          <Input
                            value={formData.name_of_vessel}
                            onChange={(e) => setFormData({...formData, name_of_vessel: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            placeholder="MV. SHIP NAME"
                            required
                            data-testid="vessel-name"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Asal Batubara</Label>
                          <Input
                            value={formData.coal_from}
                            onChange={(e) => setFormData({...formData, coal_from: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            required
                            data-testid="vessel-coal-from"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Muatan */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-cyan-400">Data Muatan</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">B/L (MT)</Label>
                          <Input
                            type="number"
                            step="0.001"
                            value={formData.bl_mt}
                            onChange={(e) => setFormData({...formData, bl_mt: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            data-testid="vessel-bl-mt"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">DS (MT)</Label>
                          <Input
                            type="number"
                            step="0.001"
                            value={formData.ds_mt}
                            onChange={(e) => setFormData({...formData, ds_mt: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            data-testid="vessel-ds-mt"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Kualitas */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-mono uppercase tracking-wider text-cyan-400">Data Kualitas</h3>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">GCV ARB (Kcal/Kg)</Label>
                          <Input
                            type="number"
                            value={formData.gcv_arb}
                            onChange={(e) => setFormData({...formData, gcv_arb: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            data-testid="vessel-gcv-arb"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">TM ARB (%)</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={formData.tm_arb}
                            onChange={(e) => setFormData({...formData, tm_arb: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            data-testid="vessel-tm-arb"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">IM ARB (%)</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={formData.im_arb}
                            onChange={(e) => setFormData({...formData, im_arb: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Ash ARB (%)</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={formData.ash_arb}
                            onChange={(e) => setFormData({...formData, ash_arb: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">HGI</Label>
                          <Input
                            type="number"
                            value={formData.hgi}
                            onChange={(e) => setFormData({...formData, hgi: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Slagging Index</Label>
                          <Input
                            value={formData.slagging_index}
                            onChange={(e) => setFormData({...formData, slagging_index: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            placeholder="LOW/MEDIUM/HIGH"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Fouling Index</Label>
                          <Input
                            value={formData.fouling_index}
                            onChange={(e) => setFormData({...formData, fouling_index: e.target.value})}
                            className="bg-slate-950/50 border-slate-800 text-white"
                            placeholder="LOW/MEDIUM/HIGH"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">
                        Batal
                      </Button>
                      <Button type="submit" disabled={submitting} className="bg-cyan-600 hover:bg-cyan-500" data-testid="vessel-submit-btn">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {editingVessel ? "Simpan Perubahan" : "Tambah Data"}
                      </Button>
                    </div>
                  </form>
                </ScrollArea>
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <Input
          placeholder="Cari shipment code, vessel, supplier..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10 bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600"
          data-testid="vessel-search-input"
        />
      </div>

      {/* Table */}
      <Card className="glass-card border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400 font-mono text-xs">PERIODE</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">SHIPMENT CODE</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">VESSEL</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">SUPPLIER</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">ASAL</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">DS (MT)</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">GCV ARB</TableHead>
                {canEdit && <TableHead className="text-slate-400 font-mono text-xs w-12"></TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={canEdit ? 8 : 7} className="text-center py-12">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-cyan-400" />
                  </TableCell>
                </TableRow>
              ) : vessels.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={canEdit ? 8 : 7} className="text-center py-12 text-slate-500">
                    Tidak ada data vessel
                  </TableCell>
                </TableRow>
              ) : (
                vessels.map((vessel) => (
                  <TableRow key={vessel.id} className="border-white/5 hover:bg-white/5">
                    <TableCell className="text-slate-300 font-mono text-sm">{vessel.periode_ta}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[200px] truncate">{vessel.shipment_code}</TableCell>
                    <TableCell className="text-white font-medium">{vessel.name_of_vessel}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{vessel.suppliers}</TableCell>
                    <TableCell className="text-slate-400 text-sm max-w-[150px] truncate">{vessel.coal_from}</TableCell>
                    <TableCell className="text-cyan-400 font-mono">{vessel.ds_mt?.toLocaleString() || "-"}</TableCell>
                    <TableCell className="text-amber-400 font-mono">{vessel.gcv_arb?.toLocaleString() || "-"}</TableCell>
                    {canEdit && (
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-[#0B1221] border-white/10">
                            <DropdownMenuItem onClick={() => handleEdit(vessel)} className="text-slate-300 focus:text-white focus:bg-white/5">
                              <Edit className="w-4 h-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            {user?.role === "admin" && (
                              <DropdownMenuItem onClick={() => handleDelete(vessel.id)} className="text-red-400 focus:text-red-300 focus:bg-red-500/10">
                                <Trash2 className="w-4 h-4 mr-2" />
                                Hapus
                              </DropdownMenuItem>
                            )}
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

export default VesselPage;
