import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Settings, Users, Plus, Loader2, Shield, User, Eye } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SettingsPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "operator"
  });

  useEffect(() => { fetchUsers(); }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/users`, { headers: getAuthHeader() });
      setUsers(response.data);
    } catch (error) {
      toast.error("Gagal memuat data pengguna");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/auth/register`, formData, { headers: getAuthHeader() });
      toast.success("Pengguna berhasil ditambahkan");
      setDialogOpen(false);
      resetForm();
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menambahkan pengguna");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({ name: "", email: "", password: "", role: "operator" });
  };

  const getRoleBadge = (role) => {
    const styles = {
      admin: "bg-red-500/20 text-red-400 border-red-500/30",
      operator: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      viewer: "bg-slate-500/20 text-slate-400 border-slate-500/30"
    };
    const icons = {
      admin: Shield,
      operator: User,
      viewer: Eye
    };
    const Icon = icons[role] || User;
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border ${styles[role] || styles.viewer}`}>
        <Icon className="w-3 h-3" />
        {role.charAt(0).toUpperCase() + role.slice(1)}
      </span>
    );
  };

  return (
    <div className="space-y-6" data-testid="settings-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Settings className="w-8 h-8 text-cyan-400" />
            Pengaturan
          </h1>
          <p className="text-slate-400 mt-1">Kelola pengguna dan konfigurasi sistem</p>
        </div>
      </div>

      {/* User Management */}
      <Card className="glass-card border-white/10">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-heading text-lg text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            Manajemen Pengguna
          </CardTitle>
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="bg-cyan-600 hover:bg-cyan-500" data-testid="add-user-btn">
                <Plus className="w-4 h-4 mr-2" />Tambah Pengguna
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
              <DialogHeader>
                <DialogTitle className="text-white font-heading">Tambah Pengguna Baru</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">Nama Lengkap</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="bg-slate-950/50 border-slate-800 text-white"
                    placeholder="Nama lengkap"
                    required
                    data-testid="user-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Email</Label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="bg-slate-950/50 border-slate-800 text-white"
                    placeholder="email@pltu-tenayan.co.id"
                    required
                    data-testid="user-email-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Password</Label>
                  <Input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    className="bg-slate-950/50 border-slate-800 text-white"
                    placeholder="••••••••"
                    required
                    data-testid="user-password-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Role</Label>
                  <Select value={formData.role} onValueChange={(value) => setFormData({...formData, role: value})}>
                    <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white" data-testid="user-role-select">
                      <SelectValue placeholder="Pilih role" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0B1221] border-white/10">
                      <SelectItem value="viewer" className="text-slate-300 focus:bg-white/5 focus:text-white">
                        <div className="flex items-center gap-2">
                          <Eye className="w-4 h-4" />Viewer - Hanya bisa melihat data
                        </div>
                      </SelectItem>
                      <SelectItem value="operator" className="text-slate-300 focus:bg-white/5 focus:text-white">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4" />Operator - Bisa menambah & edit data
                        </div>
                      </SelectItem>
                      <SelectItem value="admin" className="text-slate-300 focus:bg-white/5 focus:text-white">
                        <div className="flex items-center gap-2">
                          <Shield className="w-4 h-4" />Admin - Akses penuh
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }} className="border-slate-700 text-slate-300">
                    Batal
                  </Button>
                  <Button type="submit" disabled={submitting} className="bg-cyan-600 hover:bg-cyan-500" data-testid="user-submit-btn">
                    {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Tambah Pengguna
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-slate-400 font-mono text-xs">NAMA</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">EMAIL</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">ROLE</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">TERDAFTAR</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-12">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto text-cyan-400" />
                    </TableCell>
                  </TableRow>
                ) : users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-12 text-slate-500">
                      Tidak ada data pengguna
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((u) => (
                    <TableRow key={u.id} className="border-white/5 hover:bg-white/5">
                      <TableCell className="text-white font-medium">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
                            {u.name?.charAt(0).toUpperCase()}
                          </div>
                          {u.name}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-300">{u.email}</TableCell>
                      <TableCell>{getRoleBadge(u.role)}</TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {new Date(u.created_at).toLocaleDateString('id-ID')}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Role Info */}
      <Card className="glass-card border-white/10">
        <CardHeader>
          <CardTitle className="font-heading text-lg text-white">Informasi Role</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-5 h-5 text-red-400" />
                <span className="font-medium text-white">Admin</span>
              </div>
              <ul className="text-sm text-slate-400 space-y-1">
                <li>• Akses penuh ke semua fitur</li>
                <li>• Kelola pengguna</li>
                <li>• Hapus data</li>
                <li>• Export laporan</li>
              </ul>
            </div>
            <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
              <div className="flex items-center gap-2 mb-3">
                <User className="w-5 h-5 text-blue-400" />
                <span className="font-medium text-white">Operator</span>
              </div>
              <ul className="text-sm text-slate-400 space-y-1">
                <li>• Tambah data baru</li>
                <li>• Edit data yang ada</li>
                <li>• Upload file Excel</li>
                <li>• Lihat semua data</li>
              </ul>
            </div>
            <div className="p-4 rounded-xl bg-slate-500/10 border border-slate-500/20">
              <div className="flex items-center gap-2 mb-3">
                <Eye className="w-5 h-5 text-slate-400" />
                <span className="font-medium text-white">Viewer</span>
              </div>
              <ul className="text-sm text-slate-400 space-y-1">
                <li>• Lihat dashboard</li>
                <li>• Lihat semua data</li>
                <li>• Lihat laporan</li>
                <li>• Tidak bisa mengubah data</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;
