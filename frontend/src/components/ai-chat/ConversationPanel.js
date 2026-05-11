import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import ConversationPanelHeader from "@/components/ai-chat/ConversationPanelHeader";
import MessageList from "@/components/ai-chat/MessageList";
import MessageInputBar from "@/components/ai-chat/MessageInputBar";
import EmptyState from "@/components/ai-chat/EmptyState";

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

function ConversationPanel({ conversationId, conversationTitle, onNewConversation, creating }) {
  const { getAuthHeader } = useAuth();
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [sending, setSending] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [oldestMessageId, setOldestMessageId] = useState(null);
  const [inputValue, setInputValue] = useState("");

  const fetchMessages = useCallback(async (convId) => {
    setLoading(true);
    setMessages([]);
    setHasMore(false);
    setOldestMessageId(null);
    try {
      const res = await axios.get(
        `${API_URL}/api/ai/conversations/${convId}/messages?limit=20`,
        { headers: getAuthHeader() }
      );
      const data = res.data;
      setMessages(data);
      setHasMore(data.length === 20);
      if (data.length > 0) setOldestMessageId(data[0].id);
    } catch (err) {
      if (err.response?.status === 404) {
        setMessages([]);
      } else {
        handleApiError(err, () => fetchMessages(convId), navigate);
      }
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [getAuthHeader, navigate]);

  useEffect(() => {
    if (conversationId) {
      fetchMessages(conversationId);
    } else {
      setMessages([]);
      setLoading(false);
    }
  }, [conversationId, fetchMessages]);

  const handleLoadOlder = useCallback(async () => {
    if (!conversationId || !oldestMessageId || loadingOlder) return;
    setLoadingOlder(true);
    try {
      const res = await axios.get(
        `${API_URL}/api/ai/conversations/${conversationId}/messages?before=${oldestMessageId}&limit=20`,
        { headers: getAuthHeader() }
      );
      const older = res.data;
      setMessages(prev => [...older, ...prev]);
      setHasMore(older.length === 20);
      if (older.length > 0) setOldestMessageId(older[0].id);
    } catch (err) {
      handleApiError(err, handleLoadOlder, navigate);
    } finally {
      setLoadingOlder(false);
    }
  }, [conversationId, oldestMessageId, loadingOlder, getAuthHeader, navigate]);

  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || sending || !conversationId) return;
    const content = inputValue.trim();
    setInputValue("");

    // Optimistic user message
    const optimisticMsg = {
      id: `optimistic-${Date.now()}`,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, optimisticMsg]);
    setSending(true);

    try {
      const res = await axios.post(
        `${API_URL}/api/ai/conversations/${conversationId}/messages`,
        { content },
        { headers: getAuthHeader() }
      );
      setMessages(prev => [...prev, res.data]);
    } catch (err) {
      // Remove optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== optimisticMsg.id));
      handleApiError(
        err,
        () => {
          setInputValue(content);
        },
        navigate
      );
    } finally {
      setSending(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [inputValue, sending, conversationId, getAuthHeader, navigate]);

  if (!conversationId) {
    return (
      <section
        aria-label="Panel percakapan"
        className="flex-1 min-w-0 flex flex-col h-full bg-slate-950/40 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden"
      >
        <EmptyState onNewConversation={onNewConversation} creating={creating} />
      </section>
    );
  }

  return (
    <section
      aria-label="Panel percakapan"
      className="flex-1 min-w-0 flex flex-col h-full bg-slate-950/40 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden"
    >
      <ConversationPanelHeader title={conversationTitle} />
      <MessageList
        messages={messages}
        loading={loading}
        loadingOlder={loadingOlder}
        hasMore={hasMore}
        onLoadOlder={handleLoadOlder}
        sending={sending}
      />
      <MessageInputBar
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSend}
        disabled={sending || loading}
        inputRef={inputRef}
      />
    </section>
  );
}

export default ConversationPanel;
