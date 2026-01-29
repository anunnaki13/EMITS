import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  LayoutDashboard,
  Ship,
  Truck,
  Leaf,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronRight,
  ChevronDown,
  Anchor,
  User,
  Package,
  ShoppingCart,
  Award,
  Bot
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [rekapOpen, setRekapOpen] = useState(true);
  const [smartStockOpen, setSmartStockOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const rekapItems = [
    { path: "/vessel", label: "Vessel TNY", icon: Ship },
    { path: "/barge", label: "Barge TNY", icon: Anchor },
    { path: "/trucking", label: "Trucking TNY", icon: Truck },
    { path: "/biomassa", label: "Biomassa TNY", icon: Leaf },
    { path: "/po-batubara", label: "Purchase Order Batubara", icon: ShoppingCart },
    { path: "/merit-order", label: "Merit Order", icon: Award },
  ];

  const smartStockItems = [
    { path: "/smart-stock/sumber-penerimaan", label: "Sumber Penerimaan", icon: Package },
    { path: "/smart-stock/sumber-pemakaian", label: "Sumber Pemakaian", icon: TrendingUp },
  ];

  const isRekapActive = rekapItems.some(item => location.pathname === item.path);
  const isSmartStockActive = smartStockItems.some(item => location.pathname === item.path);

  return (
    <div className="min-h-screen bg-[#02040A] grid-bg">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-72 bg-[#0B1221]/95 backdrop-blur-xl border-r border-white/5 transform transition-transform duration-300 ease-out lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center neon-glow">
              <Ship className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-heading font-bold text-white text-lg">PLTU</h1>
              <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Tenayan</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1 overflow-y-auto max-h-[calc(100vh-180px)]">
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-600 px-3 mb-3">
            Menu Utama
          </p>
          
          {/* Dashboard */}
          <Link
            to="/dashboard"
            onClick={() => setSidebarOpen(false)}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
              location.pathname === "/dashboard"
                ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                : "text-slate-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <LayoutDashboard className="w-5 h-5" />
            <span className="text-sm font-medium">Dashboard</span>
            {location.pathname === "/dashboard" && <ChevronRight className="w-4 h-4 ml-auto" />}
          </Link>

          {/* Rekapitulasi Dropdown */}
          <Collapsible open={rekapOpen} onOpenChange={setRekapOpen}>
            <CollapsibleTrigger className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
              isRekapActive 
                ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" 
                : "text-slate-400 hover:text-white hover:bg-white/5"
            }`}>
              <Package className="w-5 h-5" />
              <span className="text-sm font-medium flex-1 text-left">Rekap Penerimaan BB</span>
              <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${rekapOpen ? "rotate-180" : ""}`} />
            </CollapsibleTrigger>
            <CollapsibleContent className="pl-4 mt-1 space-y-1">
              {rekapItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                      isActive
                        ? "bg-cyan-500/10 text-cyan-400"
                        : "text-slate-500 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <item.icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : ""}`} />
                    <span className="text-xs font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </CollapsibleContent>
          </Collapsible>

          {/* Smart Stock Dropdown */}
          <Collapsible open={smartStockOpen} onOpenChange={setSmartStockOpen}>
            <CollapsibleTrigger className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
              isSmartStockActive 
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                : "text-slate-400 hover:text-white hover:bg-white/5"
            }`}>
              <Package className="w-5 h-5" />
              <span className="text-sm font-medium flex-1 text-left">Smart Stock</span>
              <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${smartStockOpen ? "rotate-180" : ""}`} />
            </CollapsibleTrigger>
            <CollapsibleContent className="pl-4 mt-1 space-y-1">
              {smartStockItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                      isActive
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "text-slate-500 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <item.icon className={`w-4 h-4 ${isActive ? "text-emerald-400" : ""}`} />
                    <span className="text-xs font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </CollapsibleContent>
          </Collapsible>

          {/* Laporan */}
          <Link
            to="/laporan"
            onClick={() => setSidebarOpen(false)}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
              location.pathname === "/laporan"
                ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                : "text-slate-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <FileText className="w-5 h-5" />
            <span className="text-sm font-medium">Laporan</span>
            {location.pathname === "/laporan" && <ChevronRight className="w-4 h-4 ml-auto" />}
          </Link>

          {/* AI Intelligence Agent */}
          <Link
            to="/ai-intelligence"
            onClick={() => setSidebarOpen(false)}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
              location.pathname === "/ai-intelligence"
                ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-500/30"
                : "text-slate-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Bot className="w-5 h-5" />
            <span className="text-sm font-medium">AI Intelligence</span>
            {location.pathname === "/ai-intelligence" && <ChevronRight className="w-4 h-4 ml-auto" />}
          </Link>

          {user?.role === "admin" && (
            <>
              <p className="text-[10px] font-mono uppercase tracking-wider text-slate-600 px-3 mb-3 mt-6">
                Administrasi
              </p>
              <Link
                to="/settings"
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                  location.pathname === "/settings"
                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Settings className="w-5 h-5" />
                <span className="text-sm font-medium">Pengaturan</span>
              </Link>
            </>
          )}
        </nav>

        {/* User info at bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/5">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name}</p>
              <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:ml-72">
        {/* Header */}
        <header className="h-16 bg-[#0B1221]/80 backdrop-blur-xl border-b border-white/5 sticky top-0 z-30">
          <div className="h-full px-4 lg:px-8 flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="hidden lg:block">
              <h2 className="font-heading font-semibold text-white text-lg">
                Sistem Manajemen Bahan Bakar Digital
              </h2>
              <p className="text-xs text-slate-500">UP Tenayan - Rekapitulasi Penerimaan</p>
            </div>

            <div className="flex items-center gap-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="flex items-center gap-2 text-slate-300 hover:text-white hover:bg-white/5"
                    data-testid="user-menu-btn"
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                      <User className="w-4 h-4 text-white" />
                    </div>
                    <span className="hidden sm:inline text-sm">{user?.name}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 bg-[#0B1221] border-white/10">
                  <DropdownMenuItem className="text-slate-300 focus:text-white focus:bg-white/5">
                    <User className="w-4 h-4 mr-2" />
                    Profil
                  </DropdownMenuItem>
                  {user?.role === "admin" && (
                    <DropdownMenuItem
                      onClick={() => navigate("/settings")}
                      className="text-slate-300 focus:text-white focus:bg-white/5"
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Pengaturan
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="text-red-400 focus:text-red-300 focus:bg-red-500/10"
                    data-testid="logout-btn"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Keluar
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
};

export default Layout;
