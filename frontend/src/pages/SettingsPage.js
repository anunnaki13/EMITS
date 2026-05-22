import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import RuntimeHealthPanel from "@/components/RuntimeHealthPanel";
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
import { Switch } from "@/components/ui/switch";
import {
  Settings,
  Users,
  Plus,
  Trash2,
  Shield,
  User,
  Mail,
  Loader2,
  Bot,
  Key,
  Save,
  Scale,
  DollarSign,
  Download,
  Upload,
  DatabaseBackup,
  AlertTriangle,
  History,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const INITIAL_AUDIT_FILTERS = {
  category: "all",
  action: "all",
  severity: "all",
  actor: "",
  record_id: "",
  date_from: "",
  date_to: ""
};

const SettingsPage = () => {
  const { user, getAuthHeader } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // AI Settings state
  const [aiSettings, setAiSettings] = useState({
    custom_api_key: "",
    llm_provider: "gemini",
    llm_model: "gemini-2.5-flash",
    using_default: true
  });
  const [savingAI, setSavingAI] = useState(false);
  
  // COA Settings state
  const [coaSettings, setCoaSettings] = useState({
    price_per_kcal_per_ton: ""
  });
  const [savingCOA, setSavingCOA] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);
  const [savingBackupSettings, setSavingBackupSettings] = useState(false);
  const [managedBackupLoading, setManagedBackupLoading] = useState(false);
  const [backupSettings, setBackupSettings] = useState({
    enabled: false,
    interval_hours: 24,
    retention_days: 14,
    max_backups: 7,
    backup_dir: ""
  });
  const [backupHealth, setBackupHealth] = useState(null);
  const [backupHistory, setBackupHistory] = useState([]);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [restoreFile, setRestoreFile] = useState(null);
  const [restoreConfirmation, setRestoreConfirmation] = useState("");
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditFilters, setAuditFilters] = useState(INITIAL_AUDIT_FILTERS);
  const [alertOverview, setAlertOverview] = useState({
    open_count: 0,
    critical_count: 0,
    warning_count: 0,
    rule_config: {}
  });
  
  const [newUser, setNewUser] = useState({
    name: "",
    email: "",
    password: "",
    role: "operator"
  });

  const fetchAlertOverview = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/alerts?status=open&limit=5`, { headers: getAuthHeader() });
      setAlertOverview({
        open_count: response.data.open_count || 0,
        critical_count: response.data.critical_count || 0,
        warning_count: response.data.warning_count || 0,
        rule_config: response.data.rule_config || {}
      });
    } catch (error) {
      console.log("Alert overview not available");
    }
  }, [getAuthHeader]);

  const fetchCOASettings = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/settings/coa`, { headers: getAuthHeader() });
      setCoaSettings({
        price_per_kcal_per_ton: response.data.price_per_kcal_per_ton?.toString() || ""
      });
    } catch (error) {
      console.log("COA settings not available");
    }
  }, [getAuthHeader]);

  const handleSaveCOASettings = async () => {
    if (!coaSettings.price_per_kcal_per_ton) {
      toast.error("Fallback harga per kCal per Ton wajib diisi");
      return;
    }
    setSavingCOA(true);
    try {
      await axios.put(`${API_URL}/api/settings/coa`, {
        price_per_kcal_per_ton: parseFloat(coaSettings.price_per_kcal_per_ton)
      }, { headers: getAuthHeader() });
      toast.success("Pengaturan COA berhasil disimpan");
      fetchCOASettings();
      fetchAuditLogs();
    } catch (error) {
      toast.error("Gagal menyimpan pengaturan COA");
    } finally {
      setSavingCOA(false);
    }
  };

  const fetchAISettings = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/ai/settings`, { headers: getAuthHeader() });
      setAiSettings({
        custom_api_key: response.data.custom_api_key || "",
        llm_provider: response.data.llm_provider || "gemini",
        llm_model: response.data.llm_model || "gemini-2.5-flash",
        using_default: response.data.using_default
      });
    } catch (error) {
      console.log("AI settings not available");
    }
  }, [getAuthHeader]);

  const handleSaveAISettings = async () => {
    setSavingAI(true);
    try {
      await axios.put(`${API_URL}/api/ai/settings`, {
        custom_api_key: aiSettings.custom_api_key || null,
        llm_provider: aiSettings.llm_provider,
        llm_model: aiSettings.llm_model
      }, { headers: getAuthHeader() });
      toast.success("Pengaturan AI berhasil disimpan");
      fetchAISettings();
      fetchAuditLogs();
    } catch (error) {
      toast.error("Gagal menyimpan pengaturan AI");
    } finally {
      setSavingAI(false);
    }
  };

  const fetchUsers = useCallback(async () => {
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
  }, [getAuthHeader]);

  const fetchAuditLogsForFilters = useCallback(async (filters) => {
    setAuditLoading(true);
    try {
      const params = { page_size: 25 };
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== "all") params[key] = value;
      });
      const response = await axios.get(`${API_URL}/api/admin/audit-logs`, { headers: getAuthHeader(), params });
      setAuditLogs(response.data.items || []);
    } catch (error) {
      console.log("Audit logs endpoint not available");
    } finally {
      setAuditLoading(false);
    }
  }, [getAuthHeader]);

  const fetchAuditLogs = useCallback(() => {
    return fetchAuditLogsForFilters(auditFilters);
  }, [auditFilters, fetchAuditLogsForFilters]);

  const exportAuditLogs = async () => {
    try {
      const params = {};
      Object.entries(auditFilters).forEach(([key, value]) => {
        if (value && value !== "all") params[key] = value;
      });
      const response = await axios.get(`${API_URL}/api/admin/audit-logs/export`, {
        headers: getAuthHeader(),
        params,
        responseType: "blob"
      });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `emits-audit-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast.success("Audit log diekspor");
    } catch (error) {
      toast.error("Gagal export audit log");
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
      fetchAuditLogs();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menambahkan user");
    } finally {
      setSubmitting(false);
    }
  };

  const readRestoreFile = async () => {
    if (!restoreFile) {
      toast.error("Pilih file backup terlebih dahulu");
      return null;
    }

    try {
      const text = await restoreFile.text();
      return JSON.parse(text);
    } catch (error) {
      toast.error("File backup tidak valid");
      return null;
    }
  };

  const handleCreateBackup = async () => {
    setBackupLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/admin/backup`, {}, { headers: getAuthHeader() });
      const generatedAt = response.data.generated_at?.replace(/[:.]/g, "-") || new Date().toISOString().replace(/[:.]/g, "-");
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `emits-backup-${generatedAt}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast.success("Backup berhasil dibuat");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal membuat backup");
    } finally {
      setBackupLoading(false);
    }
  };

  const fetchBackupStatus = useCallback(async () => {
    try {
      const [settingsResponse, historyResponse] = await Promise.all([
        axios.get(`${API_URL}/api/admin/backup/settings`, { headers: getAuthHeader() }),
        axios.get(`${API_URL}/api/admin/backup/history`, { headers: getAuthHeader(), params: { page_size: 5 } })
      ]);
      const settings = settingsResponse.data.settings || {};
      setBackupSettings({
        enabled: Boolean(settings.enabled),
        interval_hours: settings.interval_hours || 24,
        retention_days: settings.retention_days || 14,
        max_backups: settings.max_backups || 7,
        backup_dir: settings.backup_dir || ""
      });
      setBackupHealth(settingsResponse.data.health || null);
      setBackupHistory(historyResponse.data.items || []);
    } catch (error) {
      console.log("Backup status not available");
    }
  }, [getAuthHeader]);

  useEffect(() => {
    fetchUsers();
    fetchAISettings();
    fetchCOASettings();
    fetchBackupStatus();
    fetchAuditLogsForFilters(INITIAL_AUDIT_FILTERS);
    fetchAlertOverview();
  }, [
    fetchAISettings,
    fetchAlertOverview,
    fetchAuditLogsForFilters,
    fetchBackupStatus,
    fetchCOASettings,
    fetchUsers
  ]);

  const handleSaveBackupSettings = async () => {
    setSavingBackupSettings(true);
    try {
      const response = await axios.put(
        `${API_URL}/api/admin/backup/settings`,
        {
          enabled: backupSettings.enabled,
          interval_hours: Number(backupSettings.interval_hours || 24),
          retention_days: Number(backupSettings.retention_days || 14),
          max_backups: Number(backupSettings.max_backups || 7),
          backup_dir: backupSettings.backup_dir || null
        },
        { headers: getAuthHeader() }
      );
      setBackupHealth(response.data.health || null);
      toast.success("Pengaturan backup otomatis disimpan");
      fetchBackupStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal menyimpan pengaturan backup");
    } finally {
      setSavingBackupSettings(false);
    }
  };

  const handleRunManagedBackup = async () => {
    setManagedBackupLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/admin/backup/run`, {}, { headers: getAuthHeader() });
      const docs = response.data.backup?.total_documents || 0;
      toast.success(`Backup server berhasil: ${docs.toLocaleString("id-ID")} dokumen`);
      fetchBackupStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Backup server gagal");
    } finally {
      setManagedBackupLoading(false);
    }
  };

  const handleValidateRestore = async () => {
    const backup = await readRestoreFile();
    if (!backup) return;

    setRestoreLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/admin/restore`,
        { confirmation: "RESTORE", backup, dry_run: true },
        { headers: getAuthHeader() }
      );
      const totalRows = Object.values(response.data.counts || {}).reduce((sum, count) => sum + Number(count || 0), 0);
      toast.success(`File valid: ${totalRows.toLocaleString("id-ID")} dokumen siap direstore`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Validasi restore gagal");
    } finally {
      setRestoreLoading(false);
    }
  };

  const handleRestoreBackup = async () => {
    if (restoreConfirmation !== "RESTORE") {
      toast.error("Ketik RESTORE untuk konfirmasi");
      return;
    }

    const backup = await readRestoreFile();
    if (!backup) return;

    setRestoreLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/admin/restore`,
        { confirmation: restoreConfirmation, backup, dry_run: false },
        { headers: getAuthHeader() }
      );
      const totalRows = Object.values(response.data.restored || {}).reduce((sum, count) => sum + Number(count || 0), 0);
      toast.success(`Restore berhasil: ${totalRows.toLocaleString("id-ID")} dokumen dipulihkan`);
      setRestoreFile(null);
      setRestoreConfirmation("");
      fetchUsers();
      fetchAISettings();
      fetchCOASettings();
      fetchAuditLogs();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Restore backup gagal");
    } finally {
      setRestoreLoading(false);
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

  const actionLabels = {
    create: "Tambah",
    update: "Ubah",
    delete: "Hapus",
    restore: "Restore"
  };

  const categoryLabels = {
    rekap: "Rekap",
    coa: "COA",
    settings: "Settings",
    users: "Users"
  };

  const formatAuditTime = (value) => {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString("id-ID", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const getBackupHealthBadge = () => {
    const status = backupHealth?.status || "disabled";
    const config = {
      healthy: { icon: CheckCircle, text: "Sehat", className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
      warning: { icon: AlertTriangle, text: "Perhatian", className: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
      disabled: { icon: XCircle, text: "Nonaktif", className: "bg-slate-500/15 text-slate-300 border-slate-500/30" }
    };
    const item = config[status] || config.disabled;
    const Icon = item.icon;
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border ${item.className}`}>
        <Icon className="w-3.5 h-3.5" />
        {item.text}
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

      <RuntimeHealthPanel getAuthHeader={getAuthHeader} />

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
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <h3 className="text-white font-medium">Alert Operasional</h3>
              <p className="text-slate-500 text-sm">Low stock, keterlambatan kedatangan, delta COA tinggi, dan dispute stale</p>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={fetchAlertOverview}
            className="border-slate-700 text-slate-300 hover:bg-white/5"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Alert
          </Button>
        </div>
        <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="rounded-lg bg-slate-900/50 p-4">
            <p className="text-xs text-slate-500">Open</p>
            <p className="font-heading text-3xl font-bold text-white">{alertOverview.open_count}</p>
          </div>
          <div className="rounded-lg bg-red-500/10 p-4">
            <p className="text-xs text-red-300">Critical</p>
            <p className="font-heading text-3xl font-bold text-white">{alertOverview.critical_count}</p>
          </div>
          <div className="rounded-lg bg-amber-500/10 p-4">
            <p className="text-xs text-amber-300">Warning</p>
            <p className="font-heading text-3xl font-bold text-white">{alertOverview.warning_count}</p>
          </div>
          <div className="rounded-lg bg-blue-500/10 p-4">
            <p className="text-xs text-blue-300">Rule Config</p>
            <p className="text-sm text-white">Stock {alertOverview.rule_config.low_stock_days || 14} hari</p>
            <p className="text-xs text-slate-500">COA delta {alertOverview.rule_config.high_coa_delta || 100}</p>
          </div>
        </div>
      </Card>

      {/* COA Settings Card */}
      <Card className="glass-card border-white/5 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
            <Scale className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-white font-medium">Pengaturan COA Reconciliation</h3>
            <p className="text-slate-500 text-sm">
              Potential Loss utama memakai harga PO Batubara
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-300 text-sm flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Fallback Harga per kCal per Ton (Rp)
              </Label>
              <Input
                type="number"
                step="0.01"
                value={coaSettings.price_per_kcal_per_ton}
                onChange={(e) => setCoaSettings({...coaSettings, price_per_kcal_per_ton: e.target.value})}
                placeholder="Contoh: 150"
                className="bg-slate-900/50 border-slate-700 text-white"
                data-testid="coa-price-input"
              />
              <p className="text-xs text-slate-500">
                Nilai ini hanya referensi lama. Dashboard COA sekarang menghitung dari total PO / tonase PO.
              </p>
            </div>
            
            <div className="bg-slate-900/30 rounded-lg p-3 border border-white/5">
              <p className="text-xs text-slate-400">
                <span className="text-amber-400 font-medium">Formula:</span><br/>
                Potential Loss = Σ (Delta_GCV × Tonase × (Harga_PO_per_MT / Loading_GCV))
              </p>
              <p className="text-xs text-slate-500 mt-2">
                Jika shipment belum ada di PO, sistem memakai harga PO supplier terakhir yang tersedia.
              </p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="bg-cyan-500/10 rounded-lg p-4 border border-cyan-500/20">
              <p className="text-sm text-cyan-300 font-medium mb-2">Nilai Saat Ini</p>
              <p className="text-2xl font-bold text-white">
                {coaSettings.price_per_kcal_per_ton 
                  ? `Rp ${parseFloat(coaSettings.price_per_kcal_per_ton).toLocaleString("id-ID")}`
                  : "Belum diatur"
                }
              </p>
              <p className="text-xs text-slate-400 mt-1">fallback lama, bukan basis utama dashboard</p>
            </div>
            
            <Button 
              onClick={handleSaveCOASettings}
              disabled={savingCOA}
              className="w-full bg-amber-600 hover:bg-amber-500"
              data-testid="save-coa-settings-btn"
            >
              {savingCOA ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
              Simpan Pengaturan COA
            </Button>
          </div>
        </div>
      </Card>

      {/* AI Settings Card */}
      <Card className="glass-card border-white/5 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center">
            <Bot className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-white font-medium">Pengaturan AI Intelligence</h3>
            <p className="text-slate-500 text-sm">
              {aiSettings.using_default
                ? "Menggunakan OpenRouter API Key default"
                : "Menggunakan API Key custom"
              }
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-300 text-sm flex items-center gap-2">
                <Key className="w-4 h-4" />
                API Key (Gemini/OpenAI)
              </Label>
              <Input
                type="password"
                value={aiSettings.custom_api_key}
                onChange={(e) => setAiSettings({...aiSettings, custom_api_key: e.target.value})}
                placeholder="Kosongkan untuk menggunakan key default"
                className="bg-slate-900/50 border-slate-700 text-white"
                data-testid="ai-api-key-input"
              />
              <p className="text-xs text-slate-500">
                Jika kosong, sistem akan menggunakan OpenRouter API Key default secara otomatis
              </p>
            </div>
            
            <div className="space-y-2">
              <Label className="text-slate-300 text-sm">Provider</Label>
              <Select 
                value={aiSettings.llm_provider} 
                onValueChange={(val) => setAiSettings({...aiSettings, llm_provider: val})}
              >
                <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white" data-testid="ai-provider-select">
                  <SelectValue placeholder="Pilih provider" />
                </SelectTrigger>
                <SelectContent className="bg-[#0B1221] border-slate-800">
                  <SelectItem value="gemini" className="text-slate-300">Google Gemini</SelectItem>
                  <SelectItem value="openai" className="text-slate-300">OpenAI</SelectItem>
                  <SelectItem value="anthropic" className="text-slate-300">Anthropic Claude</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-300 text-sm">Model</Label>
              <Select 
                value={aiSettings.llm_model} 
                onValueChange={(val) => setAiSettings({...aiSettings, llm_model: val})}
              >
                <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white" data-testid="ai-model-select">
                  <SelectValue placeholder="Pilih model" />
                </SelectTrigger>
                <SelectContent className="bg-[#0B1221] border-slate-800">
                  {aiSettings.llm_provider === "gemini" && (
                    <>
                      <SelectItem value="gemini-2.5-flash" className="text-slate-300">Gemini 2.5 Flash</SelectItem>
                      <SelectItem value="gemini-2.5-pro" className="text-slate-300">Gemini 2.5 Pro</SelectItem>
                    </>
                  )}
                  {aiSettings.llm_provider === "openai" && (
                    <>
                      <SelectItem value="gpt-4o" className="text-slate-300">GPT-4o</SelectItem>
                      <SelectItem value="gpt-4o-mini" className="text-slate-300">GPT-4o Mini</SelectItem>
                    </>
                  )}
                  {aiSettings.llm_provider === "anthropic" && (
                    <>
                      <SelectItem value="claude-sonnet-4-20250514" className="text-slate-300">Claude Sonnet 4</SelectItem>
                      <SelectItem value="claude-haiku-4-20250514" className="text-slate-300">Claude Haiku 4</SelectItem>
                    </>
                  )}
                </SelectContent>
              </Select>
            </div>
            
            <div className="pt-4">
              <Button 
                onClick={handleSaveAISettings}
                disabled={savingAI}
                className="w-full bg-cyan-600 hover:bg-cyan-500"
                data-testid="save-ai-settings-btn"
              >
                {savingAI ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                Simpan Pengaturan AI
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Backup & Restore Card */}
      <Card className="glass-card border-white/5 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
            <DatabaseBackup className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-white font-medium">Backup & Restore Data</h3>
            <p className="text-slate-500 text-sm">
              Backup seluruh koleksi aktif dan restore dengan konfirmasi admin
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-slate-700/70 bg-slate-900/40 px-4 py-3">
              <div>
                <p className="text-sm text-white font-medium">Backup Otomatis</p>
                <p className="text-xs text-slate-500">{backupHealth?.reason || "Memuat status backup"}</p>
              </div>
              <div className="flex items-center gap-3">
                {getBackupHealthBadge()}
                <Switch
                  checked={backupSettings.enabled}
                  onCheckedChange={(checked) => setBackupSettings({ ...backupSettings, enabled: checked })}
                  data-testid="backup-enabled-switch"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-2">
                <Label className="text-xs text-slate-400">Interval (jam)</Label>
                <Input
                  type="number"
                  min="1"
                  max="168"
                  value={backupSettings.interval_hours}
                  onChange={(e) => setBackupSettings({ ...backupSettings, interval_hours: e.target.value })}
                  className="bg-slate-900/50 border-slate-700 text-white"
                  data-testid="backup-interval-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-slate-400">Retensi (hari)</Label>
                <Input
                  type="number"
                  min="1"
                  max="365"
                  value={backupSettings.retention_days}
                  onChange={(e) => setBackupSettings({ ...backupSettings, retention_days: e.target.value })}
                  className="bg-slate-900/50 border-slate-700 text-white"
                  data-testid="backup-retention-input"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-slate-400">Maks. file</Label>
                <Input
                  type="number"
                  min="1"
                  max="100"
                  value={backupSettings.max_backups}
                  onChange={(e) => setBackupSettings({ ...backupSettings, max_backups: e.target.value })}
                  className="bg-slate-900/50 border-slate-700 text-white"
                  data-testid="backup-max-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleSaveBackupSettings}
                disabled={savingBackupSettings || backupLoading || restoreLoading}
                className="border-emerald-500/30 text-emerald-300"
                data-testid="save-backup-settings-btn"
              >
                {savingBackupSettings ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                Simpan Jadwal
              </Button>
              <Button
                type="button"
                onClick={handleRunManagedBackup}
                disabled={managedBackupLoading || restoreLoading}
                className="bg-emerald-600 hover:bg-emerald-500"
                data-testid="run-managed-backup-btn"
              >
                {managedBackupLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <DatabaseBackup className="w-4 h-4 mr-2" />}
                Jalankan Backup
              </Button>
            </div>

            <div className="bg-emerald-500/10 rounded-lg p-4 border border-emerald-500/20">
              <p className="text-sm text-emerald-300 font-medium mb-2">Buat Backup</p>
              <p className="text-xs text-slate-400">
                File JSON berisi users, rekap penerimaan, smart stock, COA, pengaturan, dan riwayat AI.
              </p>
            </div>
            <Button
              onClick={handleCreateBackup}
              disabled={backupLoading || restoreLoading}
              className="w-full bg-emerald-600 hover:bg-emerald-500"
              data-testid="create-backup-btn"
            >
              {backupLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Download className="w-4 h-4 mr-2" />}
              Download Backup JSON
            </Button>

            <div className="rounded-lg border border-slate-700/70 bg-slate-900/30 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-700/70 flex items-center justify-between">
                <p className="text-sm text-white font-medium">Riwayat Backup</p>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={fetchBackupStatus}
                  className="text-slate-400 hover:text-white"
                  data-testid="refresh-backup-history-btn"
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
              <div className="divide-y divide-slate-800">
                {backupHistory.length === 0 ? (
                  <div className="px-4 py-4 text-sm text-slate-500">Belum ada riwayat backup server</div>
                ) : (
                  backupHistory.map((item) => (
                    <div key={item.id} className="px-4 py-3 flex items-center justify-between gap-3" data-testid={`backup-history-${item.id}`}>
                      <div className="min-w-0">
                        <p className="text-sm text-slate-200 truncate">{item.filename || item.trigger || "backup"}</p>
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatAuditTime(item.created_at)}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className={item.status === "success" ? "text-xs text-emerald-300" : "text-xs text-red-300"}>
                          {item.status}
                        </p>
                        <p className="text-xs text-slate-500">
                          {(item.total_documents || 0).toLocaleString("id-ID")} dokumen
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-red-500/10 rounded-lg p-4 border border-red-500/20">
              <p className="text-sm text-red-300 font-medium mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Restore Mengganti Data Aktif
              </p>
              <p className="text-xs text-slate-400">
                Restore akan mengosongkan koleksi aktif lalu mengisi ulang dari file backup yang valid.
              </p>
            </div>

            <div className="space-y-2">
              <Label className="text-slate-300 text-sm flex items-center gap-2">
                <Upload className="w-4 h-4" />
                File Backup JSON
              </Label>
              <Input
                type="file"
                accept="application/json,.json"
                onChange={(e) => setRestoreFile(e.target.files?.[0] || null)}
                className="bg-slate-900/50 border-slate-700 text-white file:text-slate-300"
                data-testid="restore-file-input"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-slate-300 text-sm">Ketik RESTORE untuk konfirmasi</Label>
              <Input
                value={restoreConfirmation}
                onChange={(e) => setRestoreConfirmation(e.target.value)}
                placeholder="RESTORE"
                className="bg-slate-900/50 border-slate-700 text-white"
                data-testid="restore-confirmation-input"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleValidateRestore}
                disabled={!restoreFile || restoreLoading || backupLoading}
                className="border-slate-700 text-slate-300"
                data-testid="validate-restore-btn"
              >
                {restoreLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Validasi File
              </Button>
              <Button
                type="button"
                onClick={handleRestoreBackup}
                disabled={!restoreFile || restoreConfirmation !== "RESTORE" || restoreLoading || backupLoading}
                className="bg-red-600 hover:bg-red-500"
                data-testid="restore-backup-btn"
              >
                {restoreLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Upload className="w-4 h-4 mr-2" />}
                Restore
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Audit Trail Card */}
      <Card className="glass-card border-white/5 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
              <History className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-white font-medium">Audit Trail Admin</h3>
              <p className="text-slate-500 text-sm">
                Riwayat create, update, delete, dan restore pada data penting
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={fetchAuditLogs}
            disabled={auditLoading}
            className="border-slate-700 text-slate-300"
            data-testid="refresh-audit-logs-btn"
          >
            {auditLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Refresh
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={exportAuditLogs}
            className="border-slate-700 text-slate-300"
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
          <Select value={auditFilters.category} onValueChange={(value) => setAuditFilters({ ...auditFilters, category: value })}>
            <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white">
              <SelectValue placeholder="Kategori" />
            </SelectTrigger>
            <SelectContent className="bg-[#0B1221] border-slate-700">
              <SelectItem value="all">Semua Kategori</SelectItem>
              <SelectItem value="rekap">Rekap</SelectItem>
              <SelectItem value="coa">COA</SelectItem>
              <SelectItem value="settings">Settings</SelectItem>
              <SelectItem value="users">Users</SelectItem>
            </SelectContent>
          </Select>
          <Select value={auditFilters.action} onValueChange={(value) => setAuditFilters({ ...auditFilters, action: value })}>
            <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white">
              <SelectValue placeholder="Aksi" />
            </SelectTrigger>
            <SelectContent className="bg-[#0B1221] border-slate-700">
              <SelectItem value="all">Semua Aksi</SelectItem>
              <SelectItem value="create">Create</SelectItem>
              <SelectItem value="update">Update</SelectItem>
              <SelectItem value="delete">Delete</SelectItem>
              <SelectItem value="restore">Restore</SelectItem>
            </SelectContent>
          </Select>
          <Select value={auditFilters.severity} onValueChange={(value) => setAuditFilters({ ...auditFilters, severity: value })}>
            <SelectTrigger className="bg-slate-900/50 border-slate-700 text-white">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent className="bg-[#0B1221] border-slate-700">
              <SelectItem value="all">Semua Severity</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
          <Input
            value={auditFilters.actor}
            onChange={(e) => setAuditFilters({ ...auditFilters, actor: e.target.value })}
            placeholder="Actor/email"
            className="bg-slate-900/50 border-slate-700 text-white"
          />
          <Input
            value={auditFilters.record_id}
            onChange={(e) => setAuditFilters({ ...auditFilters, record_id: e.target.value })}
            placeholder="Record ID"
            className="bg-slate-900/50 border-slate-700 text-white"
          />
          <Input
            type="date"
            value={auditFilters.date_from}
            onChange={(e) => setAuditFilters({ ...auditFilters, date_from: e.target.value })}
            className="bg-slate-900/50 border-slate-700 text-white"
          />
          <Input
            type="date"
            value={auditFilters.date_to}
            onChange={(e) => setAuditFilters({ ...auditFilters, date_to: e.target.value })}
            className="bg-slate-900/50 border-slate-700 text-white"
          />
          <Button type="button" onClick={fetchAuditLogs} className="bg-blue-600 hover:bg-blue-500">
            Terapkan Filter
          </Button>
        </div>

        <div className="rounded-lg border border-white/5 overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400 font-mono text-xs">Waktu</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">Severity</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">Aksi</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">Kategori</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">Resource</TableHead>
                <TableHead className="text-slate-400 font-mono text-xs">Admin</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {auditLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-blue-400 mx-auto" />
                  </TableCell>
                </TableRow>
              ) : auditLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                    Belum ada audit log
                  </TableCell>
                </TableRow>
              ) : (
                auditLogs.map((log) => (
                  <TableRow key={log.id} className="border-white/5 hover:bg-slate-900/50" data-testid={`audit-row-${log.id}`}>
                    <TableCell className="text-slate-300 text-xs">{formatAuditTime(log.created_at)}</TableCell>
                    <TableCell className="text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        log.severity === "high" ? "bg-red-500/20 text-red-300" :
                        log.severity === "medium" ? "bg-amber-500/20 text-amber-300" :
                        "bg-slate-500/20 text-slate-300"
                      }`}>
                        {log.severity || "low"}
                      </span>
                    </TableCell>
                    <TableCell className="text-white text-sm">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-300">
                        {actionLabels[log.action] || log.action}
                      </span>
                    </TableCell>
                    <TableCell className="text-slate-300 text-sm">{categoryLabels[log.category] || log.category}</TableCell>
                    <TableCell className="text-slate-300 text-sm">
                      {log.resource}
                      {log.record_id ? <span className="text-slate-500"> / {log.record_id}</span> : null}
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">{log.actor_email || "-"}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Card>

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
