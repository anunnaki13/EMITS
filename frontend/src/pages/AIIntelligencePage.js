import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Bot,
  Send,
  Loader2,
  Sparkles,
  Beaker,
  AlertTriangle,
  FileText,
  TrendingUp,
  Trash2,
  Settings,
  ChevronRight,
  Zap,
  Brain,
  BarChart3
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MODULE_INFO = {
  general: {
    name: "General Intelligence",
    icon: Brain,
    color: "cyan",
    description: "Tanya apa saja tentang data bahan bakar",
    placeholder: "Contoh: Berapa total penerimaan batubara bulan ini?"
  },
  blending: {
    name: "Smart Blending Optimizer",
    icon: Beaker,
    color: "emerald",
    description: "Optimasi campuran batubara & biomassa",
    placeholder: "Contoh: Carikan kombinasi campuran untuk target GCV 4200 Kcal/kg"
  },
  boiler_risk: {
    name: "Boiler Risk Warning",
    icon: AlertTriangle,
    color: "red",
    description: "Deteksi risiko kerusakan boiler",
    placeholder: "Contoh: Analisis risiko slagging dan fouling dari data terbaru"
  },
  contract: {
    name: "Contract Compliance",
    icon: FileText,
    color: "blue",
    description: "Monitoring kontrak & PO",
    placeholder: "Contoh: Supplier mana yang hampir habis kuotanya?"
  },
  logistics: {
    name: "Logistics Analysis",
    icon: TrendingUp,
    color: "amber",
    description: "Efisiensi & analisis losses",
    placeholder: "Contoh: Analisis supplier dengan losses tertinggi"
  }
};

const AIIntelligencePage = () => {
  const { user, getAuthHeader } = useAuth();
  const [activeModule, setActiveModule] = useState("general");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [quickData, setQuickData] = useState({});
  const [loadingQuick, setLoadingQuick] = useState(true);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fetchHistory();
    fetchQuickData();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/ai/history?limit=50`, {
        headers: getAuthHeader()
      });
      setChatHistory(response.data.reverse());
      if (response.data.length > 0) {
        setSessionId(response.data[0].session_id);
      }
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const fetchQuickData = async () => {
    try {
      const [blending, boiler, contract, logistics] = await Promise.all([
        axios.get(`${API_URL}/api/ai/quick/blending-suggestion`, { headers: getAuthHeader() }),
        axios.get(`${API_URL}/api/ai/quick/boiler-alerts`, { headers: getAuthHeader() }),
        axios.get(`${API_URL}/api/ai/quick/contract-status`, { headers: getAuthHeader() }),
        axios.get(`${API_URL}/api/ai/quick/logistics-losses`, { headers: getAuthHeader() })
      ]);
      setQuickData({
        blending: blending.data,
        boiler: boiler.data,
        contract: contract.data,
        logistics: logistics.data
      });
    } catch (error) {
      console.error("Error fetching quick data:", error);
    } finally {
      setLoadingQuick(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userQuery = query;
    setQuery("");
    setLoading(true);

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      query: userQuery,
      module: activeModule,
      isUser: true,
      created_at: new Date().toISOString()
    };
    setChatHistory(prev => [...prev, userMessage]);

    try {
      const response = await axios.post(`${API_URL}/api/ai/query`, {
        query: userQuery,
        module: activeModule,
        session_id: sessionId,
        parameters: activeModule === "blending" ? { target_gcv: 4000 } : null
      }, { headers: getAuthHeader() });

      // Add AI response to chat
      const aiMessage = {
        id: Date.now() + 1,
        response: response.data.response,
        module: activeModule,
        isUser: false,
        created_at: new Date().toISOString()
      };
      setChatHistory(prev => [...prev, aiMessage]);
      setSessionId(response.data.session_id);

    } catch (error) {
      toast.error(error.response?.data?.detail || "Gagal memproses query AI");
      // Remove user message on error
      setChatHistory(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const clearHistory = async () => {
    if (!window.confirm("Hapus semua riwayat chat?")) return;
    try {
      await axios.delete(`${API_URL}/api/ai/history`, { headers: getAuthHeader() });
      setChatHistory([]);
      setSessionId(null);
      toast.success("Riwayat chat dihapus");
    } catch (error) {
      toast.error("Gagal menghapus riwayat");
    }
  };

  const handleQuickQuery = (moduleKey, queryText) => {
    setActiveModule(moduleKey);
    setQuery(queryText);
    inputRef.current?.focus();
  };

  const ModuleCard = ({ moduleKey, info }) => {
    const Icon = info.icon;
    const isActive = activeModule === moduleKey;
    
    return (
      <button
        onClick={() => setActiveModule(moduleKey)}
        className={`p-3 rounded-xl border transition-all text-left w-full ${
          isActive 
            ? `bg-${info.color}-500/20 border-${info.color}-500/50` 
            : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg bg-${info.color}-500/20 flex items-center justify-center`}>
            <Icon className={`w-5 h-5 text-${info.color}-400`} />
          </div>
          <div className="min-w-0 flex-1">
            <p className={`text-sm font-medium ${isActive ? 'text-white' : 'text-slate-300'}`}>
              {info.name}
            </p>
            <p className="text-xs text-slate-500 truncate">{info.description}</p>
          </div>
          <ChevronRight className={`w-4 h-4 ${isActive ? `text-${info.color}-400` : 'text-slate-600'}`} />
        </div>
      </button>
    );
  };

  const QuickInsightCard = ({ title, value, subtitle, color, onClick }) => (
    <button
      onClick={onClick}
      className={`p-4 rounded-xl bg-${color}-500/10 border border-${color}-500/20 hover:border-${color}-500/40 transition-all text-left w-full`}
    >
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className={`text-sm text-${color}-400 font-medium`}>{title}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </button>
  );

  return (
    <div className="space-y-6" data-testid="ai-intelligence-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            Tenayan Fuel Intelligence Agent
          </h1>
          <p className="text-slate-400 mt-1">Asisten AI untuk analisis data bahan bakar</p>
        </div>
        {chatHistory.length > 0 && (
          <Button
            variant="outline"
            onClick={clearHistory}
            className="border-red-500/50 text-red-400 hover:bg-red-500/10"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Hapus Riwayat
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar - Modules */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="glass-card border-white/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                Pilih Modul AI
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(MODULE_INFO).map(([key, info]) => (
                <ModuleCard key={key} moduleKey={key} info={info} />
              ))}
            </CardContent>
          </Card>

          {/* Quick Insights */}
          <Card className="glass-card border-white/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-white flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                Quick Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {loadingQuick ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
                </div>
              ) : (
                <>
                  <QuickInsightCard
                    title="Boiler Alerts"
                    value={quickData.boiler?.total_alerts || 0}
                    subtitle="Risiko tinggi slagging/fouling"
                    color="red"
                    onClick={() => handleQuickQuery("boiler_risk", "Tampilkan semua alert risiko boiler saat ini")}
                  />
                  <QuickInsightCard
                    title="Critical PO"
                    value={quickData.contract?.contracts?.filter(c => c.status === "CRITICAL").length || 0}
                    subtitle="Kontrak hampir habis"
                    color="amber"
                    onClick={() => handleQuickQuery("contract", "List semua PO yang hampir habis kuotanya")}
                  />
                  <QuickInsightCard
                    title="Top Loss"
                    value={`${(quickData.logistics?.top_losses?.[0]?.avg_loss_pct || 0).toFixed(1)}%`}
                    subtitle={quickData.logistics?.top_losses?.[0]?.supplier?.substring(0, 20) || "-"}
                    color="blue"
                    onClick={() => handleQuickQuery("logistics", "Analisis supplier dengan losses tertinggi")}
                  />
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Main Chat Area */}
        <div className="lg:col-span-3">
          <Card className="glass-card border-white/10 h-[calc(100vh-220px)] flex flex-col">
            {/* Module Header */}
            <CardHeader className="pb-3 border-b border-slate-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {(() => {
                    const Icon = MODULE_INFO[activeModule].icon;
                    return (
                      <div className={`w-10 h-10 rounded-lg bg-${MODULE_INFO[activeModule].color}-500/20 flex items-center justify-center`}>
                        <Icon className={`w-5 h-5 text-${MODULE_INFO[activeModule].color}-400`} />
                      </div>
                    );
                  })()}
                  <div>
                    <CardTitle className="text-base text-white">
                      {MODULE_INFO[activeModule].name}
                    </CardTitle>
                    <p className="text-xs text-slate-500">{MODULE_INFO[activeModule].description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">Powered by</span>
                  <span className="text-xs text-cyan-400 font-medium">Gemini AI</span>
                </div>
              </div>
            </CardHeader>

            {/* Chat Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {chatHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <Bot className="w-16 h-16 text-slate-700 mx-auto mb-4" />
                    <p className="text-slate-400 mb-2">Selamat datang di Tenayan Fuel Intelligence Agent</p>
                    <p className="text-slate-500 text-sm mb-6">Pilih modul di samping, lalu ajukan pertanyaan Anda</p>
                    
                    {/* Suggested Queries */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                      <button
                        onClick={() => handleQuickQuery("blending", "Carikan kombinasi optimal untuk target GCV 4000 Kcal/kg dengan ash content minimal")}
                        className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 hover:border-emerald-500/40 text-left transition-all"
                      >
                        <p className="text-sm text-emerald-400 font-medium">🧪 Smart Blending</p>
                        <p className="text-xs text-slate-500">Optimasi campuran GCV 4000</p>
                      </button>
                      <button
                        onClick={() => handleQuickQuery("boiler_risk", "Analisis risiko slagging dan fouling dari semua kargo terbaru. Tampilkan alert board.")}
                        className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 hover:border-red-500/40 text-left transition-all"
                      >
                        <p className="text-sm text-red-400 font-medium">⚠️ Boiler Risk</p>
                        <p className="text-xs text-slate-500">Alert board risiko boiler</p>
                      </button>
                      <button
                        onClick={() => handleQuickQuery("contract", "Tampilkan status semua kontrak PO. Mana yang hampir habis dan mana yang GCV-nya defisit?")}
                        className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 hover:border-blue-500/40 text-left transition-all"
                      >
                        <p className="text-sm text-blue-400 font-medium">📄 Contract Status</p>
                        <p className="text-xs text-slate-500">Monitoring PO & kontrak</p>
                      </button>
                      <button
                        onClick={() => handleQuickQuery("logistics", "Analisis efisiensi logistik: losses tertinggi, durasi bongkar, dan anomali pengiriman")}
                        className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 hover:border-amber-500/40 text-left transition-all"
                      >
                        <p className="text-sm text-amber-400 font-medium">📊 Logistics Analysis</p>
                        <p className="text-xs text-slate-500">Efisiensi & losses</p>
                      </button>
                    </div>
                  </div>
                ) : (
                  chatHistory.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl p-4 ${
                          msg.isUser
                            ? 'bg-cyan-600 text-white'
                            : 'bg-slate-800/80 text-slate-200'
                        }`}
                      >
                        {msg.isUser ? (
                          <p className="text-sm">{msg.query}</p>
                        ) : (
                          <div className="ai-response-content">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                table: ({ children }) => (
                                  <div className="overflow-x-auto my-4 rounded-lg border border-slate-700">
                                    <table className="min-w-full text-sm">
                                      {children}
                                    </table>
                                  </div>
                                ),
                                thead: ({ children }) => (
                                  <thead className="bg-slate-700/50">
                                    {children}
                                  </thead>
                                ),
                                tbody: ({ children }) => (
                                  <tbody className="divide-y divide-slate-700">
                                    {children}
                                  </tbody>
                                ),
                                tr: ({ children }) => (
                                  <tr className="hover:bg-slate-800/50">
                                    {children}
                                  </tr>
                                ),
                                th: ({ children }) => (
                                  <th className="px-3 py-2 text-left text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                                    {children}
                                  </th>
                                ),
                                td: ({ children }) => (
                                  <td className="px-3 py-2 text-sm text-slate-300 whitespace-nowrap">
                                    {children}
                                  </td>
                                ),
                                code: ({ inline, children }) => (
                                  inline ? (
                                    <code className="bg-slate-900 px-1.5 py-0.5 rounded text-cyan-400 text-xs font-mono">
                                      {children}
                                    </code>
                                  ) : (
                                    <code className="text-cyan-400 text-xs font-mono">
                                      {children}
                                    </code>
                                  )
                                ),
                                pre: ({ children }) => (
                                  <pre className="bg-slate-900 p-4 rounded-lg overflow-x-auto text-sm my-3 border border-slate-700">
                                    {children}
                                  </pre>
                                ),
                                ul: ({ children }) => (
                                  <ul className="list-disc list-outside ml-5 space-y-1 my-3 text-slate-300">
                                    {children}
                                  </ul>
                                ),
                                ol: ({ children }) => (
                                  <ol className="list-decimal list-outside ml-5 space-y-1 my-3 text-slate-300">
                                    {children}
                                  </ol>
                                ),
                                li: ({ children }) => (
                                  <li className="text-sm leading-relaxed">
                                    {children}
                                  </li>
                                ),
                                p: ({ children }) => (
                                  <p className="text-sm leading-relaxed my-2 text-slate-200">
                                    {children}
                                  </p>
                                ),
                                h1: ({ children }) => (
                                  <h1 className="text-xl font-bold text-white mt-6 mb-3 pb-2 border-b border-slate-700">{children}</h1>
                                ),
                                h2: ({ children }) => (
                                  <h2 className="text-lg font-bold text-white mt-5 mb-2">{children}</h2>
                                ),
                                h3: ({ children }) => (
                                  <h3 className="text-base font-semibold text-cyan-400 mt-4 mb-2">{children}</h3>
                                ),
                                h4: ({ children }) => (
                                  <h4 className="text-sm font-semibold text-slate-200 mt-3 mb-1">{children}</h4>
                                ),
                                strong: ({ children }) => (
                                  <strong className="text-cyan-400 font-semibold">{children}</strong>
                                ),
                                em: ({ children }) => (
                                  <em className="text-slate-400 italic">{children}</em>
                                ),
                                blockquote: ({ children }) => (
                                  <blockquote className="border-l-4 border-cyan-500 pl-4 my-3 text-slate-400 italic">
                                    {children}
                                  </blockquote>
                                ),
                                hr: () => (
                                  <hr className="my-4 border-slate-700" />
                                ),
                                a: ({ href, children }) => (
                                  <a href={href} className="text-cyan-400 hover:text-cyan-300 underline" target="_blank" rel="noopener noreferrer">
                                    {children}
                                  </a>
                                ),
                              }}
                            >
                              {msg.response}
                            </ReactMarkdown>
                          </div>
                        )}
                        <p className="text-[10px] mt-2 opacity-50">
                          {new Date(msg.created_at).toLocaleString('id-ID')}
                        </p>
                      </div>
                    </div>
                  ))
                )}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800/80 rounded-2xl p-4 flex items-center gap-3">
                      <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
                      <span className="text-slate-400 text-sm">AI sedang menganalisis data...</span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="p-4 border-t border-slate-800">
              <form onSubmit={handleSubmit} className="flex gap-3">
                <div className="flex-1 relative">
                  <Textarea
                    ref={inputRef}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={MODULE_INFO[activeModule].placeholder}
                    className="bg-slate-900/50 border-slate-700 text-white min-h-[50px] max-h-[120px] pr-12 resize-none"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                    data-testid="ai-query-input"
                  />
                </div>
                <Button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="bg-cyan-600 hover:bg-cyan-500 h-auto px-6"
                  data-testid="ai-submit-btn"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </Button>
              </form>
              <p className="text-[10px] text-slate-600 mt-2 text-center">
                Tekan Enter untuk kirim, Shift+Enter untuk baris baru
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AIIntelligencePage;
