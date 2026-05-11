import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot } from "lucide-react";
import { formatRelativeTime } from "@/lib/formatRelativeTime";

const MessageBubble = React.memo(function MessageBubble({ message }) {
  if (message.role === "user") {
    return (
      <article aria-label="Pesan Anda" className="flex justify-end animate-fade-in">
        <div className="max-w-[75%] flex flex-col items-end gap-1">
          <div className="bg-cyan-500/20 border border-cyan-500/30 rounded-xl rounded-tr-sm px-3 py-2">
            <p className="text-sm text-slate-100 leading-relaxed whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>
          <span className="text-[11px] font-mono text-slate-600">
            {formatRelativeTime(message.created_at)}
          </span>
        </div>
      </article>
    );
  }

  return (
    <article aria-label="Respons AI" className="flex justify-start animate-fade-in">
      <div className="max-w-[75%] flex gap-2">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0 mt-1">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div className="flex flex-col gap-1">
          <div className="bg-slate-900/60 border border-white/10 rounded-xl rounded-tl-sm px-3 py-2">
            <div className="ai-chat-response">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
          <span className="text-[11px] font-mono text-slate-600">
            {formatRelativeTime(message.created_at)}
          </span>
        </div>
      </div>
    </article>
  );
});

export default MessageBubble;
