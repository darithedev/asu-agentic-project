"use client";

import { useState, KeyboardEvent, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const placeholderSuggestions = [
  "What are some travel tips for Tokyo?",
  "How much does a flight to Paris cost?",
  "What is your cancellation policy?",
  "Tell me about New York City",
];

export function MessageInput({ onSend, disabled = false }: MessageInputProps) {
  const [message, setMessage] = useState("");
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Rotate placeholder suggestions
  useEffect(() => {
    if (message.trim()) return;
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % placeholderSuggestions.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [message]);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  return (
    <div className="flex gap-2 p-3 sm:p-4 border-t border-orange-200/60 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={placeholderSuggestions[placeholderIndex]}
          disabled={disabled}
          rows={1}
          className={cn(
            "w-full resize-none rounded-lg border border-orange-200/60 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm dark:text-gray-100",
            "placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 focus-visible:border-primary/50",
            "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted",
            "min-h-[40px] max-h-[120px] overflow-y-auto",
            "transition-all shadow-sm"
          )}
          aria-label="Message input"
          aria-describedby="input-hint"
        />
        <div
          id="input-hint"
          className="sr-only"
        >
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
      <Button
        onClick={handleSend}
        disabled={disabled || !message.trim()}
        size="default"
        className="shrink-0"
        aria-label="Send message"
      >
        {disabled ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Send className="size-4" />
        )}
        <span className="hidden sm:inline">Send</span>
      </Button>
    </div>
  );
}

