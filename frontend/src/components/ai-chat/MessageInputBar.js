import { useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

function MessageInputBar({ value, onChange, onSend, disabled, inputRef: externalRef }) {
  const internalRef = useRef(null);
  const ref = externalRef || internalRef;

  // Auto-grow textarea
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }, [value, ref]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) onSend();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!disabled && value.trim()) onSend();
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex-shrink-0 p-4 border-t border-white/5 bg-[#0B1221]/80 backdrop-blur-xl"
    >
      <div className="flex gap-2 items-end">
        <Textarea
          ref={ref}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ketik pesan..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none min-h-[44px] max-h-[120px] bg-slate-950/50 border-slate-800 text-slate-100 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 placeholder:text-slate-600 rounded-xl"
          aria-label="Ketik pesan Anda"
        />
        <Button
          type="submit"
          disabled={disabled || !value.trim()}
          size="icon"
          className="h-[44px] w-[44px] flex-shrink-0 bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] border border-cyan-400/20 rounded-xl"
          aria-label="Kirim pesan"
        >
          {disabled ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
    </form>
  );
}

export default MessageInputBar;
