import React from "react";
import { formatRelativeTime } from "@/lib/formatRelativeTime";

const ConversationListItem = React.memo(function ConversationListItem({ conversation, isSelected, onClick }) {
  return (
    <li>
      <button
        onClick={onClick}
        aria-pressed={isSelected}
        aria-label={`Pilih percakapan: ${conversation.title || "Percakapan tanpa judul"}`}
        className={`w-full flex flex-col gap-1 px-3 py-3 rounded-lg transition-colors duration-200 text-left ${
          isSelected
            ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
            : "text-slate-400 hover:text-white hover:bg-white/5"
        }`}
      >
        <span className="text-sm font-normal truncate w-full">
          {conversation.title || "Percakapan tanpa judul"}
        </span>
        <span className="text-[11px] font-mono text-slate-500">
          {formatRelativeTime(conversation.last_message_at)}
        </span>
      </button>
    </li>
  );
});

export default ConversationListItem;
