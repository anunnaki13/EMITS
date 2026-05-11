import { Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import ConversationListItem from "@/components/ai-chat/ConversationListItem";

function ConversationListItemSkeleton() {
  return (
    <div className="px-3 py-3 space-y-2">
      <Skeleton className="h-4 w-3/4 rounded" />
      <Skeleton className="h-3 w-1/3 rounded" />
    </div>
  );
}

function ConversationSidebar({ conversations, selectedConvId, onSelectConversation, onNewConversation, loading, creating }) {
  return (
    <aside
      role="complementary"
      aria-label="Daftar percakapan"
      className="w-72 flex-shrink-0 bg-[#0B1221]/95 backdrop-blur-xl border-r border-white/5 flex flex-col h-full"
    >
      <div className="p-4 border-b border-white/5 flex-shrink-0">
        <p className="text-[11px] font-mono uppercase tracking-wider text-slate-600 mb-3">
          Percakapan Saya
        </p>
        <Button
          onClick={onNewConversation}
          disabled={creating}
          className="w-full bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] border border-cyan-400/20"
        >
          {creating ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Plus className="w-4 h-4 mr-2" />
          )}
          Percakapan Baru
        </Button>
      </div>

      <nav
        aria-label="Riwayat percakapan"
        className="flex-1 overflow-y-auto p-2 space-y-1"
      >
        {loading ? (
          <>
            <ConversationListItemSkeleton />
            <ConversationListItemSkeleton />
            <ConversationListItemSkeleton />
          </>
        ) : conversations.length === 0 ? null : (
          <ul role="list">
            {conversations.map(conv => (
              <ConversationListItem
                key={conv.id}
                conversation={conv}
                isSelected={conv.id === selectedConvId}
                onClick={() => onSelectConversation(conv.id)}
              />
            ))}
          </ul>
        )}
      </nav>
    </aside>
  );
}

export default ConversationSidebar;
