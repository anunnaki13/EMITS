import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Ship, Loader2, Eye, EyeOff } from "lucide-react";

const Login = () => {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  // Login form
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  
  // Register form
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regRole, setRegRole] = useState("operator");

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(loginEmail, loginPassword);
      toast.success("Login berhasil!");
      navigate("/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Login gagal. Periksa email dan password Anda.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(regEmail, regPassword, regName, regRole);
      toast.success("Registrasi berhasil!");
      navigate("/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Registrasi gagal.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#02040A] grid-bg flex items-center justify-center p-4">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mx-auto mb-4 neon-glow-strong">
            <Ship className="w-8 h-8 text-white" />
          </div>
          <h1 className="font-heading font-bold text-3xl text-white">PLTU Tenayan</h1>
          <p className="text-slate-500 text-sm mt-1">Sistem Manajemen Bahan Bakar Digital</p>
        </div>

        <Card className="glass-card border-white/10">
          <Tabs defaultValue="login" className="w-full">
            <CardHeader className="pb-4">
              <TabsList className="grid w-full grid-cols-2 bg-slate-900/50">
                <TabsTrigger value="login" className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  Masuk
                </TabsTrigger>
                <TabsTrigger value="register" className="data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  Daftar
                </TabsTrigger>
              </TabsList>
            </CardHeader>
            
            <CardContent>
              <TabsContent value="login" className="mt-0">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email" className="text-slate-300">Email</Label>
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="nama@pltu-tenayan.co.id"
                      value={loginEmail}
                      onChange={(e) => setLoginEmail(e.target.value)}
                      required
                      className="bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600 focus:border-cyan-500"
                      data-testid="login-email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password" className="text-slate-300">Password</Label>
                    <div className="relative">
                      <Input
                        id="login-password"
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        required
                        className="bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600 focus:border-cyan-500 pr-10"
                        data-testid="login-password-input"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-cyan-600 hover:bg-cyan-500 text-white neon-glow"
                    data-testid="login-submit-btn"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Memproses...
                      </>
                    ) : (
                      "Masuk"
                    )}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="mt-0">
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="reg-name" className="text-slate-300">Nama Lengkap</Label>
                    <Input
                      id="reg-name"
                      type="text"
                      placeholder="Nama Lengkap"
                      value={regName}
                      onChange={(e) => setRegName(e.target.value)}
                      required
                      className="bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600 focus:border-cyan-500"
                      data-testid="register-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-email" className="text-slate-300">Email</Label>
                    <Input
                      id="reg-email"
                      type="email"
                      placeholder="nama@pltu-tenayan.co.id"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      required
                      className="bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600 focus:border-cyan-500"
                      data-testid="register-email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-password" className="text-slate-300">Password</Label>
                    <Input
                      id="reg-password"
                      type="password"
                      placeholder="••••••••"
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      required
                      className="bg-slate-950/50 border-slate-800 text-white placeholder:text-slate-600 focus:border-cyan-500"
                      data-testid="register-password-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-role" className="text-slate-300">Role</Label>
                    <Select value={regRole} onValueChange={setRegRole}>
                      <SelectTrigger className="bg-slate-950/50 border-slate-800 text-white" data-testid="register-role-select">
                        <SelectValue placeholder="Pilih role" />
                      </SelectTrigger>
                      <SelectContent className="bg-[#0B1221] border-white/10">
                        <SelectItem value="viewer" className="text-slate-300 focus:bg-white/5 focus:text-white">Viewer</SelectItem>
                        <SelectItem value="operator" className="text-slate-300 focus:bg-white/5 focus:text-white">Operator</SelectItem>
                        <SelectItem value="admin" className="text-slate-300 focus:bg-white/5 focus:text-white">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-cyan-600 hover:bg-cyan-500 text-white neon-glow"
                    data-testid="register-submit-btn"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Memproses...
                      </>
                    ) : (
                      "Daftar"
                    )}
                  </Button>
                </form>
              </TabsContent>
            </CardContent>
          </Tabs>
        </Card>

        <p className="text-center text-slate-600 text-xs mt-6">
          © 2025 PLTU Tenayan. All rights reserved.
        </p>
      </div>
    </div>
  );
};

export default Login;
