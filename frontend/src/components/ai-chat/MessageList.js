import { useRef, useEffect, useCallback } from "react";
import { Bot, Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import MessageBubble from "@/components/ai-chat/MessageBubble";

function MessageBubbleSkeleton({ align }) {
  return (
    <div className={`flex ${align === "end" ? "justify-end" : "justify-start"}`}>
      <Skeleton className="h-16 w-[60%] rounded-xl" />
    </div>
  );
}

function MessageList({ messages, loading, loadingOlder, hasMore, onLoadOlder, sending }) {
  const containerRef = useRef(null);
  const chatEndRef = useRef(null);
  const topSentinelRef = useRef(null);
  const prevScrollHeightRef = useRef(null);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    if (!loading) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, loading]);

  // Preserve scroll position on lazy-load prepend
  useEffect(() => {
    if (prevScrollHeightRef.current !== null && containerRef.current) {
      containerRef.current.scrollTop =
        containerRef.current.scrollHeight - prevScrollHeightRef.current;
      prevScrollHeightRef.current = null;
    }
  }, [messages]);

  // IntersectionObserver for scroll-to-top lazy load
  const handleLoadOlder = useCallback(() => {
    if (containerRef.current) {
      prevScrollHeightRef.current = containerRef.current.scrollHeight;
    }
    onLoadOlder();
  }, [onLoadOlder]);

  useEffect(() => {
    const sentinel = topSentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasMore && !loadingOlder) {
          handleLoadOlder();
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loadingOlder, handleLoadOlder]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto overflow-x-hidden p-4"
      role="log"
      aria-label="Pesan percakapan"
      aria-live="polite"
    >
      {/* Top sentinel for lazy-load */}
      {hasMore && <div ref={topSentinelRef} className="h-1" />}

      {loadingOlder && (
        <div className="flex justify-center items-center py-2">
          <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
          <span className="text-[11px] text-slate-500 ml-2">Memuat pesan lebih lama...</span>
        </div>
      )}

      {!hasMore && messages.length > 0 && (
        <p className="text-center text-[11px] font-mono text-slate-600 py-2">
          Awal percakapan
        </p>
      )}

      {loading ? (
        <div className="space-y-4">
          <MessageBubbleSkeleton align="end" />
          <MessageBubbleSkeleton align="start" />
          <MessageBubbleSkeleton align="end" />
        </div>
      ) : (
        <div className="space-y-4">
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </div>
      )}

      {sending && (
        <div aria-live="polite" aria-label="AI sedang memproses" className="flex items-center gap-2 mt-4 pl-2">
          <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
            <Bot className="w-4 h-4 text-cyan-400" />
          </div>
          <span className="text-[11px] text-slate-500 italic animate-pulse">
            AI sedang mengetik...
          </span>
        </div>
      )}

      <div ref={chatEndRef} />
    </div>
  );
}

export default MessageList;
