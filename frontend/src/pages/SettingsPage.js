import { useState, useEffect } from "react";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Settings,
  Users,
  Plus,
  Trash2,
  Shield,
  User,
  Mail,
  Loader2
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SettingsPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [newUser, setNewUser] = useState({
    name: "",
    email: "",
    password: "",
    role: "operator"
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/users`, { headers: getAuthHeader() });
      setUsers(response.data);
    } catch (error) {
      // Users endpoint might not exist yet
      console.log("Users endpoint not available");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/auth/register`, newUser, { headers: getAuthHeader() });
      toast.success("User berhasil ditambahkan");
      setDialogOpen(false);
      setNewUser({ name: "", email: "", password: "", role: "operator" });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menambahkan user");
    } finally {
      setSubmitting(false);
    }
  };

  const roles = [
    { value: "admin", label: "Administrator", color: "red" },
    { value: "operator", label: "Operator", color: "blue" },
    { value: "viewer", label: "Viewer", color: "gray" }
  ];

  const getRoleBadge = (role) => {
    const roleInfo = roles.find(r => r.value === role) || roles[2];
    const colorClasses = {
      red: "bg-red-500/20 text-red-400",
      blue: "bg-blue-500/20 text-blue-400",
      gray: "bg-slate-500/20 text-slate-400"
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colorClasses[roleInfo.color]}`}>
        {roleInfo.label}
      </span>
    );
  };

  return (
    <div className="space-y-6" data-testid="settings-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <Settings className="w-8 h-8 text-slate-400" />
            Pengaturan
          </h1>
          <p className="text-slate-400 mt-1">Kelola sistem dan pengguna aplikasi</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="glass-card border-white/5 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center">
              <User className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-white font-medium">Profil Anda</h3>
              <p className="text-slate-500 text-sm">{user?.email}</p>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-400 text-sm">Nama</span>
              <span className="text-white text-sm">{user?.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 text-sm">Role</span>
              {getRoleBadge(user?.role)}
            </div>
          </div>
        </Card>

        <Card className="glass-card border-white/5 p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
                <Users className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h3 className="text-white font-medium">Manajemen User</h3>
                <p className="text-slate-500 text-sm">{users.length} pengguna terdaftar</p>
              </div>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-purple-600 hover:bg-purple-500" data-testid="add-user-btn">
                  <Plus className="w-4 h-4 mr-2" />Tambah User
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0B1221] border-white/10 max-w-md">
                <DialogHeader>
                  <DialogTitle className="text-white font-heading">Tambah User Baru</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleCreateUser} className="space-y-4 pt-4" data-testid="add-user-form">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Nama</Label>
                    <Input
                      value={newUser.name}
                      onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                      className="bg-slate-950/50 border-slate-800 text-white"
                      placeholder="Nama lengkap"
                      required
                      data-testid="input-new-user-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Email</Label>
                    <Input
                      type="email"
                      value={newUser.email}
                      onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                      className="bg-slate-950/50 border-slate-800 text-white"
                      placeholder="email@example.com"
                      required
                      data-testid="input-new-user-email"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Password</Label>
                    <Input
                      type="password"
                      value={newUser.password}
                      onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                      className="bg-slate-950/50 border-slate-800 text-white"
                      placeholder="********"
                      required
                      data-testid="input-new-user-password"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Role</Label>
                    <Select value={newUser.role} onValueChange={(value) => setNewUser({...newUser, role: value})}>
                      <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white" data-testid="select-new-user-role">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#0B1221] border-slate-800">
                        {roles.map(role => (
                          <SelectItem key={role.value} value={role.value} className="text-white">
                            {role.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="border-slate-700 text-slate-300">
                      Batal
                    </Button>
                    <Button type="submit" disabled={submitting} className="bg-purple-600 hover:bg-purple-500" data-testid="submit-new-user-btn">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                      Tambah
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
          
          <div className="rounded-lg border border-white/5 overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-slate-400 font-mono text-xs">Nama</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">Email</TableHead>
                  <TableHead className="text-slate-400 font-mono text-xs">Role</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-purple-400 mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-8 text-slate-500">
                      Belum ada data pengguna
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((u) => (
                    <TableRow key={u.id} className="border-white/5 hover:bg-slate-900/50" data-testid={`user-row-${u.id}`}>
                      <TableCell className="text-white text-sm">{u.name}</TableCell>
                      <TableCell className="text-slate-300 text-sm">{u.email}</TableCell>
                      <TableCell>{getRoleBadge(u.role)}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>

      <Card className="glass-card border-white/5 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
            <Shield className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-white font-medium">Hak Akses Role</h3>
            <p className="text-slate-500 text-sm">Informasi tingkat akses per role</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5">
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400">Administrator</span>
            </div>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Akses penuh ke semua fitur</li>
              <li>• Kelola pengguna sistem</li>
              <li>• Hapus semua data</li>
              <li>• Akses pengaturan</li>
            </ul>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5">
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400">Operator</span>
            </div>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Input data baru</li>
              <li>• Edit dan hapus data</li>
              <li>• Upload file Excel</li>
              <li>• Akses laporan</li>
            </ul>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5">
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-slate-500/20 text-slate-400">Viewer</span>
            </div>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Lihat dashboard</li>
              <li>• Lihat semua data</li>
              <li>• Akses laporan</li>
              <li>• Tidak bisa edit data</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default SettingsPage;
