import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { PanelLeftOpen } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import ConversationSidebar from "@/components/ai-chat/ConversationSidebar";
import ConversationPanel from "@/components/ai-chat/ConversationPanel";
import { Sheet, SheetContent } from "@/components/ui/sheet";

const API_URL = process.env.REACT_APP_BACKEND_URL;

function handleApiError(err, retry, navigate) {
  if (!err.response) {
    toast.error("Tidak terhubung ke server.", {
      action: { label: "Coba lagi", onClick: retry },
      duration: 6000,
    });
  } else if (err.response.status === 401) {
    toast.error("Sesi habis. Silakan login ulang.", { duration: 5000 });
    navigate("/login");
  } else if (err.response.status === 503) {
    toast.error("Layanan AI tidak tersedia", {
      description:
        err.response.data?.detail ||
        "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar.",
      action: { label: "Coba lagi", onClick: retry },
      duration: 8000,
    });
  } else {
    toast.error("Terjadi kesalahan pada server. Silakan coba lagi.", {
      duration: 5000,
    });
  }
}

function AIChatPage() {
  const { getAuthHeader } = useAuth();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [selectedConvId, setSelectedConvId] = useState(null);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [creating, setCreating] = useState(false);
  const [sidebarSheetOpen, setSidebarSheetOpen] = useState(false);

  const fetchConversations = async () => {
    setLoadingConversations(true);
    try {
      const res = await axios.get(`${API_URL}/api/ai/conversations`, {
        headers: getAuthHeader(),
      });
      setConversations(res.data);
      if (res.data.length > 0) {
        setSelectedConvId(res.data[0].id);
      } else {
        setSelectedConvId(null);
      }
    } catch (err) {
      handleApiError(err, fetchConversations, navigate);
    } finally {
      setLoadingConversations(false);
    }
  };

  useEffect(() => {
    fetchConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleNewConversation = async () => {
    setCreating(true);
    try {
      const res = await axios.post(
        `${API_URL}/api/ai/conversations`,
        {},
        { headers: getAuthHeader() }
      );
      const newConv = res.data;
      setConversations(prev => [newConv, ...prev]);
      setSelectedConvId(newConv.id);
    } catch (err) {
      handleApiError(err, handleNewConversation, navigate);
    } finally {
      setCreating(false);
    }
  };

  const selectedConv = conversations.find(c => c.id === selectedConvId);

  const sidebarProps = {
    conversations,
    selectedConvId,
    onSelectConversation: (id) => {
      setSelectedConvId(id);
      setSidebarSheetOpen(false);
    },
    onNewConversation: handleNewConversation,
    loading: loadingConversations,
    creating,
  };

  return (
    <div>
      <div className="mb-4">
        <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white">
          Riwayat Percakapan AI
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Kelola percakapan AI Anda lintas sesi
        </p>
      </div>

      {/* Mobile sidebar trigger */}
      <button
        onClick={() => setSidebarSheetOpen(true)}
        className="lg:hidden p-2 text-slate-400 hover:text-white mb-4"
        aria-label="Buka daftar percakapan"
      >
        <PanelLeftOpen className="w-5 h-5" />
      </button>

      <div className="flex gap-0 h-[calc(100vh-112px)]">
        {/* Desktop sidebar */}
        <div className="hidden lg:flex">
          <ConversationSidebar {...sidebarProps} />
        </div>

        {/* Mobile Sheet sidebar */}
        <Sheet open={sidebarSheetOpen} onOpenChange={setSidebarSheetOpen}>
          <SheetContent side="left" className="p-0 w-72 bg-[#0B1221]">
            <ConversationSidebar {...sidebarProps} />
          </SheetContent>
        </Sheet>

        <ConversationPanel
          conversationId={selectedConvId}
          conversationTitle={selectedConv?.title || "Percakapan tanpa judul"}
          onNewConversation={handleNewConversation}
          creating={creating}
        />
      </div>
    </div>
  );
}

export default AIChatPage;
