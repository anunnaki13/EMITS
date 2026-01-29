import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import VesselPage from "@/pages/VesselPage";
import BargePage from "@/pages/BargePage";
import TruckingPage from "@/pages/TruckingPage";
import BiomassaPage from "@/pages/BiomassaPage";
import POBatubaraPage from "@/pages/POBatubaraPage";
import MeritOrderPage from "@/pages/MeritOrderPage";
import SmartStockPage from "@/pages/SmartStockPage";
import AIIntelligencePage from "@/pages/AIIntelligencePage";
import LaporanPage from "@/pages/LaporanPage";
import SettingsPage from "@/pages/SettingsPage";
import Layout from "@/components/Layout";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#02040A] flex items-center justify-center">
        <div className="animate-pulse-glow w-16 h-16 rounded-full bg-cyan-500/20 flex items-center justify-center">
          <div className="w-8 h-8 rounded-full bg-cyan-500/40"></div>
        </div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout><Dashboard /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/vessel"
        element={
          <ProtectedRoute>
            <Layout><VesselPage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/barge"
        element={
          <ProtectedRoute>
            <Layout><BargePage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/trucking"
        element={
          <ProtectedRoute>
            <Layout><TruckingPage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/biomassa"
        element={
          <ProtectedRoute>
            <Layout><BiomassaPage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/po-batubara"
        element={
          <ProtectedRoute>
            <Layout><POBatubaraPage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/merit-order"
        element={
          <ProtectedRoute>
            <Layout><MeritOrderPage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/smart-stock"
        element={
          <ProtectedRoute>
            <Layout><SmartStockPage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-intelligence"
        element={
          <ProtectedRoute>
            <Layout><AIIntelligencePage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/laporan"
        element={
          <ProtectedRoute>
            <Layout><LaporanPage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute allowedRoles={["admin"]}>
            <Layout><SettingsPage /></Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
