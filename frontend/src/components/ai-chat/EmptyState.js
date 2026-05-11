import { MessageSquare, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

function EmptyState({ onNewConversation, creating }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
      <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
        <MessageSquare className="w-8 h-8 text-cyan-400/60" />
      </div>
      <div className="text-center">
        <p className="text-base font-normal text-slate-300">Belum ada percakapan</p>
        <p className="text-sm text-slate-500 mt-1">
          Mulai percakapan baru untuk bertanya kepada AI.
        </p>
      </div>
      <Button
        onClick={onNewConversation}
        disabled={creating}
        className="bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] border border-cyan-400/20"
      >
        {creating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
        Mulai Percakapan
      </Button>
    </div>
  );
}

export default EmptyState;
