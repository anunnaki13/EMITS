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
  Ship,
  Plus,
  Search,
  Upload,
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
  FileSpreadsheet,
  AlertTriangle
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
  const [deleting, setDeleting] = useState(false);
  const fileInputRef = useRef(null);

  const initialFormData = {
    periode_ta: "", periode_realisasi: "", shipment_code: "", voyage_code: "",
    suppliers: "", voyage: "", name_of_vessel: "", coal_from: "",
    time_arrival: "", berthed_time: "", commenced_unloading: "", completed_unloading: "",
    durasi_pembongkaran_hari: "", durasi_pembongkaran_jam: "", waktu_tunggu_jam: "",
    bl_mt: "", ds_mt: "", no_cow: "", tgl_terbit_cow: "",
    gcv_arb: "", gcv_adb: "", gcv_db: "", tm_arb: "", im_adb: "",
    ash_arb: "", ash_adb: "", ash_db: "", vm_arb: "", vm_adb: "",
    fc_arb: "", fc_adb: "", ts_arb: "", ts_adb: "", ts_db: "", ts_dafb: "",
    c_arb: "", c_adb: "", h_arb: "", h_adb: "", n_arb: "", n_adb: "", n_dafb: "",
    o_arb: "", o_adb: "", hgi: "", slagging_index: "", fouling_index: "", idt_reducing: "",
    sio2_db: "", al2o3_db: "", tio2_db: "", fe2o3_db: "", cao_db: "", mgo_db: "",
    k2o_db: "", na2o_db: "", so3_db: "", p2o5_db: "", mno2_db: "", mn3o4_db: "",
    size_70mm: "", size_50mm: "", size_32mm: "", size_2_38mm: "",
    no_coa: "", tgl_terbit_coa: "", durasi_terbit_coa: ""
  };

  const [formData, setFormData] = useState(initialFormData);

  useEffect(() => { fetchVessels(); }, [search]);

  const fetchVessels = async () => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/vessels`, { headers: getAuthHeader(), params });
      setVessels(response.data);
    } catch (error) {
      toast.error("Gagal memuat data vessel");
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
        durasi_pembongkaran_jam: parseFloat2(formData.durasi_pembongkaran_jam),
        waktu_tunggu_jam: parseFloat2(formData.waktu_tunggu_jam),
        bl_mt: parseFloat2(formData.bl_mt), ds_mt: parseFloat2(formData.ds_mt),
        gcv_arb: parseFloat2(formData.gcv_arb), gcv_adb: parseFloat2(formData.gcv_adb),
        gcv_db: parseFloat2(formData.gcv_db), tm_arb: parseFloat2(formData.tm_arb),
        im_adb: parseFloat2(formData.im_adb), ash_arb: parseFloat2(formData.ash_arb),
        ash_adb: parseFloat2(formData.ash_adb), ash_db: parseFloat2(formData.ash_db),
        vm_arb: parseFloat2(formData.vm_arb), vm_adb: parseFloat2(formData.vm_adb),
        fc_arb: parseFloat2(formData.fc_arb), fc_adb: parseFloat2(formData.fc_adb),
        ts_arb: parseFloat2(formData.ts_arb), ts_adb: parseFloat2(formData.ts_adb),
        ts_db: parseFloat2(formData.ts_db), ts_dafb: parseFloat2(formData.ts_dafb),
        c_arb: parseFloat2(formData.c_arb), c_adb: parseFloat2(formData.c_adb),
        h_arb: parseFloat2(formData.h_arb), h_adb: parseFloat2(formData.h_adb),
        n_arb: parseFloat2(formData.n_arb), n_adb: parseFloat2(formData.n_adb),
        n_dafb: parseFloat2(formData.n_dafb), o_arb: parseFloat2(formData.o_arb),
        o_adb: parseFloat2(formData.o_adb), hgi: parseFloat2(formData.hgi),
        idt_reducing: parseFloat2(formData.idt_reducing),
        sio2_db: parseFloat2(formData.sio2_db), al2o3_db: parseFloat2(formData.al2o3_db),
        tio2_db: parseFloat2(formData.tio2_db), fe2o3_db: parseFloat2(formData.fe2o3_db),
        cao_db: parseFloat2(formData.cao_db), mgo_db: parseFloat2(formData.mgo_db),
        k2o_db: parseFloat2(formData.k2o_db), na2o_db: parseFloat2(formData.na2o_db),
        so3_db: parseFloat2(formData.so3_db), p2o5_db: parseFloat2(formData.p2o5_db),
        mno2_db: parseFloat2(formData.mno2_db), mn3o4_db: parseFloat2(formData.mn3o4_db),
        size_70mm: parseFloat2(formData.size_70mm), size_50mm: parseFloat2(formData.size_50mm),
        size_32mm: parseFloat2(formData.size_32mm), size_2_38mm: parseFloat2(formData.size_2_38mm)
      };

      if (editingVessel) {
        await axios.put(`${API_URL}/api/vessels/${editingVessel.id}`, dataToSend, { headers: getAuthHeader() });
        toast.success("Data vessel berhasil diperbarui");
      } else {
        await axios.post(`${API_URL}/api/vessels`, dataToSend, { headers: getAuthHeader() });
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
    const newFormData = {};
    Object.keys(initialFormData).forEach(key => {
      const val = vessel[key];
      newFormData[key] = val !== null && val !== undefined ? String(val) : "";
    });
    setFormData(newFormData);
    setDialogOpen(true);
  };

  const handleDelete = async (vesselId) => {
    if (!window.confirm("Apakah Anda yakin ingin menghapus data ini?")) return;
    try {
      await axios.delete(`${API_URL}/api/vessels/${vesselId}`, { headers: getAuthHeader() });
      toast.success("Data vessel berhasil dihapus");
      fetchVessels();
    } catch (error) {
      toast.error("Gagal menghapus data");
    }
  };

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      const response = await axios.delete(`${API_URL}/api/vessels`, { headers: getAuthHeader() });
      toast.success(response.data.message);
      fetchVessels();
    } catch (error) {
      toast.error("Gagal menghapus semua data");
    } finally {
      setDeleting(false);
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
        headers: { ...getAuthHeader(), "Content-Type": "multipart/form-data" }
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
    setFormData(initialFormData);
    setEditingVessel(null);
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
      />
    </div>
  );

  return (
    <div className="space-y-6" data-testid="vessel-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Ship className="w-8 h-8 text-cyan-400" />
            Vessel TNY
          </h1>
          <p className="text-slate-400 mt-1">Data penerimaan batubara via kapal ({vessels.length} data)</p>
        </div>
        {canEdit && (
          <div className="flex flex-wrap gap-3">
            {isAdmin && vessels.length > 0 && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10" data-testid="delete-all-vessel-btn">
                    <Trash2 className="w-4 h-4 mr-2" />Hapus Semua
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="bg-[#0B1221] border-white/10">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-white flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                      Hapus Semua Data Vessel?
                    </AlertDialogTitle>
                    <AlertDialogDescription className="text-slate-400">
                      Tindakan ini akan menghapus <span className="text-red-400 font-bold">{vessels.length}</span> data vessel secara permanen. Data yang sudah dihapus tidak dapat dikembalikan.
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
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" data-testid="upload-excel-btn">
                  <Upload className="w-4 h-4 mr-2" />Upload Excel
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
                <DialogHeader><DialogTitle className="text-white font-heading">Upload Data Excel</DialogTitle></DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-cyan-500/50 transition-colors">
                    <FileSpreadsheet className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                    <p className="text-slate-400 mb-2">Format kolom Excel harus sesuai template</p>
                    <p className="text-slate-500 text-xs mb-4">Pastikan header Excel sesuai dengan format PLTU Tenayan</p>
                    <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileUpload} className="hidden" />
                    <Button onClick={() => fileInputRef.current?.click()} disabled={submitting} className="bg-cyan-600 hover:bg-cyan-500">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}Pilih File
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
              <DialogTrigger asChild>
                <Button className="bg-cyan-600 hover:bg-cyan-500 neon-glow" data-testid="add-vessel-btn">
                  <Plus className="w-4 h-4 mr-2" />Tambah Data
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-5xl max-h-[90vh]">
                <DialogHeader><DialogTitle className="text-white font-heading">{editingVessel ? "Edit Data Vessel" : "Tambah Data Vessel"}</DialogTitle></DialogHeader>
                <ScrollArea className="max-h-[75vh] pr-4">
                  <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    <Tabs defaultValue="shipment" className="w-full">
                      <TabsList className="grid w-full grid-cols-5 bg-slate-900/50">
                        <TabsTrigger value="shipment" className="text-xs data-[state=active]:bg-cyan-500/20">Shipment</TabsTrigger>
                        <TabsTrigger value="muatan" className="text-xs data-[state=active]:bg-cyan-500/20">Muatan</TabsTrigger>
                        <TabsTrigger value="kualitas" className="text-xs data-[state=active]:bg-cyan-500/20">Kualitas</TabsTrigger>
                        <TabsTrigger value="ultimate" className="text-xs data-[state=active]:bg-cyan-500/20">Ultimate</TabsTrigger>
                        <TabsTrigger value="ash" className="text-xs data-[state=active]:bg-cyan-500/20">Ash Comp</TabsTrigger>
                      </TabsList>
                      
                      <TabsContent value="shipment" className="space-y-4 mt-4">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="Periode TA (Rakor)" name="periode_ta" placeholder="Jan-25" />
                          <FormField label="Periode Realisasi" name="periode_realisasi" placeholder="Jan-25" />
                          <FormField label="Shipment Code" name="shipment_code" />
                          <FormField label="Voyage Code" name="voyage_code" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="Suppliers" name="suppliers" />
                          <FormField label="Voyage" name="voyage" />
                          <FormField label="Name Of Vessel" name="name_of_vessel" />
                          <FormField label="Coal From" name="coal_from" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="Time Arrival" name="time_arrival" />
                          <FormField label="Berthed Time" name="berthed_time" />
                          <FormField label="Commenced Unloading" name="commenced_unloading" />
                          <FormField label="Completed Unloading" name="completed_unloading" />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">Size Analysis</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="< 70 mm (%wt)" name="size_70mm" type="number" />
                          <FormField label="< 50 mm (%wt)" name="size_50mm" type="number" />
                          <FormField label="< 32 mm (%wt)" name="size_32mm" type="number" />
                          <FormField label="< 2,38 mm (%wt)" name="size_2_38mm" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="kualitas" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-cyan-400">GCV (Kcal/Kg)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="GCV ARB" name="gcv_arb" type="number" />
                          <FormField label="GCV ADB" name="gcv_adb" type="number" />
                          <FormField label="GCV DB" name="gcv_db" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">Moisture (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="TM ARB" name="tm_arb" type="number" />
                          <FormField label="IM ADB" name="im_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">Ash Content (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="Ash ARB" name="ash_arb" type="number" />
                          <FormField label="Ash ADB" name="ash_adb" type="number" />
                          <FormField label="Ash DB" name="ash_db" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">VM & FC (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="VM ARB" name="vm_arb" type="number" />
                          <FormField label="VM ADB" name="vm_adb" type="number" />
                          <FormField label="FC ARB" name="fc_arb" type="number" />
                          <FormField label="FC ADB" name="fc_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">Total Sulphur (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="TS ARB" name="ts_arb" type="number" />
                          <FormField label="TS ADB" name="ts_adb" type="number" />
                          <FormField label="TS DB" name="ts_db" type="number" />
                          <FormField label="TS DAFB" name="ts_dafb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">Index</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <FormField label="HGI (Point Index)" name="hgi" type="number" />
                          <FormField label="Slagging Index" name="slagging_index" />
                          <FormField label="Fouling Index" name="fouling_index" />
                          <FormField label="IDT Reducing (C°)" name="idt_reducing" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="ultimate" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-cyan-400">Carbon (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="C ARB" name="c_arb" type="number" />
                          <FormField label="C ADB" name="c_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">Hydrogen (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="H ARB" name="h_arb" type="number" />
                          <FormField label="H ADB" name="h_adb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">Nitrogen (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <FormField label="N ARB" name="n_arb" type="number" />
                          <FormField label="N ADB" name="n_adb" type="number" />
                          <FormField label="N DAFB" name="n_dafb" type="number" />
                        </div>
                        <h4 className="text-sm font-mono text-cyan-400 mt-4">Oxygen (%wt)</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField label="O ARB" name="o_arb" type="number" />
                          <FormField label="O ADB" name="o_adb" type="number" />
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="ash" className="space-y-4 mt-4">
                        <h4 className="text-sm font-mono text-cyan-400">Ash Composition (%DB)</h4>
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

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <Input placeholder="Cari shipment code, vessel, supplier..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10 bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600" data-testid="vessel-search-input" />
      </div>

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
                <TableHead className="text-slate-400 font-mono text-xs">B/L (MT)</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">DS (MT)</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">GCV ARB</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">TM ARB</TableHead>
                {canEdit && <TableHead className="text-slate-400 font-mono text-xs w-12"></TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={canEdit ? 10 : 9} className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-cyan-400" /></TableCell></TableRow>
              ) : vessels.length === 0 ? (
                <TableRow><TableCell colSpan={canEdit ? 10 : 9} className="text-center py-12 text-slate-500">Tidak ada data vessel</TableCell></TableRow>
              ) : (
                vessels.map((vessel) => (
                  <TableRow key={vessel.id} className="border-white/5 hover:bg-white/5">
                    <TableCell className="text-slate-300 font-mono text-sm">{vessel.periode_ta}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[150px] truncate">{vessel.shipment_code}</TableCell>
                    <TableCell className="text-white font-medium max-w-[150px] truncate">{vessel.name_of_vessel}</TableCell>
                    <TableCell className="text-slate-300 text-sm max-w-[120px] truncate">{vessel.suppliers}</TableCell>
                    <TableCell className="text-slate-400 text-sm max-w-[120px] truncate">{vessel.coal_from}</TableCell>
                    <TableCell className="text-slate-300 font-mono">{vessel.bl_mt?.toLocaleString() || "-"}</TableCell>
                    <TableCell className="text-cyan-400 font-mono">{vessel.ds_mt?.toLocaleString() || "-"}</TableCell>
                    <TableCell className="text-amber-400 font-mono">{vessel.gcv_arb?.toLocaleString() || "-"}</TableCell>
                    <TableCell className="text-blue-400 font-mono">{vessel.tm_arb?.toFixed(2) || "-"}</TableCell>
                    {canEdit && (
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="text-slate-400 hover:text-white"><MoreHorizontal className="w-4 h-4" /></Button></DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-[#0B1221] border-white/10">
                            <DropdownMenuItem onClick={() => handleEdit(vessel)} className="text-slate-300 focus:text-white focus:bg-white/5"><Edit className="w-4 h-4 mr-2" />Edit</DropdownMenuItem>
                            {isAdmin && (<DropdownMenuItem onClick={() => handleDelete(vessel.id)} className="text-red-400 focus:text-red-300 focus:bg-red-500/10"><Trash2 className="w-4 h-4 mr-2" />Hapus</DropdownMenuItem>)}
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
