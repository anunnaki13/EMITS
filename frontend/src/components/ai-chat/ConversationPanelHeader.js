import { MessageSquare } from "lucide-react";

function ConversationPanelHeader({ title }) {
  return (
    <div className="flex-shrink-0 h-12 flex items-center px-4 border-b border-white/5 bg-[#0B1221]/60 backdrop-blur-xl">
      <div className="flex items-center gap-2 min-w-0">
        <MessageSquare className="w-4 h-4 text-cyan-400 flex-shrink-0" />
        <h2 className="font-heading font-normal text-white text-sm truncate">
          {title || "Percakapan tanpa judul"}
        </h2>
      </div>
    </div>
  );
}

export default ConversationPanelHeader;
