"use client";

import { useEffect, useState, useCallback } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Trash2, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Conversation,
  getConversations,
  deleteConversation,
  clearAllConversations,
} from "@/lib/conversation-storage";

interface ChatSidebarProps {
  currentConversationId?: string;
  onSelectConversation: (conversation: Conversation) => void;
  onNewConversation: () => void;
}

export function ChatSidebar({
  currentConversationId,
  onSelectConversation,
  onNewConversation,
}: ChatSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  // Load conversations
  const loadConversations = useCallback(() => {
    requestAnimationFrame(() => {
      const allConversations = getConversations();
      setConversations(allConversations);
    });
  }, []);

  useEffect(() => {
    loadConversations();

    // Listen for storage changes (from other tabs/windows)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "travel_agency_conversations") {
        loadConversations();
      }
    };

    // Listen for custom event (same tab updates)
    const handleConversationsUpdated = () => {
      loadConversations();
    };

    window.addEventListener("storage", handleStorageChange);
    window.addEventListener("conversationsUpdated", handleConversationsUpdated);
    
    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("conversationsUpdated", handleConversationsUpdated);
    };
  }, [loadConversations]);

  // Refresh conversations when they might have changed
  const refreshConversations = useCallback(() => {
    loadConversations();
  }, [loadConversations]);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    deleteConversation(id);
    refreshConversations();
    // If deleting current conversation, start new one
    if (id === currentConversationId) {
      onNewConversation();
    }
  };

  const handleClearAll = () => {
    if (confirm("Are you sure you want to delete all conversations?")) {
      clearAllConversations();
      refreshConversations();
      onNewConversation();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 border-r border-orange-200/60 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-orange-200/60 dark:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Chats
          </h2>
          {conversations.length > 0 && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClearAll}
              className="h-6 w-6"
              aria-label="Clear all conversations"
            >
              <Trash2 className="size-3" />
            </Button>
          )}
        </div>
        <Button
          onClick={onNewConversation}
          className="w-full justify-start gap-2"
          variant="outline"
          size="sm"
        >
          <Plus className="size-4" />
          New Chat
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-2">
          {conversations.length === 0 ? (
            <div className="text-center py-8 px-4">
              <p className="text-sm text-muted-foreground">
                No conversations yet. Start a new chat!
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {conversations.map((conversation, index) => {
                const isActive = conversation.id === currentConversationId;
                // Ensure unique key - ID should always be present, but fallback for safety
                const uniqueKey = conversation.id || `conv-${index}-${conversation.createdAt || Date.now()}`;
                return (
                  <div
                    key={uniqueKey}
                    className={cn(
                      "group relative rounded-lg transition-all",
                      isActive
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "hover:bg-muted"
                    )}
                  >
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onSelectConversation(conversation);
                      }}
                      className={cn(
                        "w-full text-left p-3 rounded-lg transition-all",
                        "flex items-start justify-between gap-2",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
                      )}
                    >
                      <span
                        className={cn(
                          "text-sm flex-1 min-w-0 break-words line-clamp-2 leading-relaxed",
                          isActive ? "text-primary-foreground font-medium" : "text-foreground"
                        )}
                        title={conversation.title}
                        style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}
                      >
                        {conversation.title || "New Chat"}
                      </span>
                      {isActive && (
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-l-[6px] border-l-primary-foreground border-t-[6px] border-t-transparent border-b-[6px] border-b-transparent"></div>
                      )}
                    </button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => handleDelete(e, conversation.id)}
                      className={cn(
                        "absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity",
                        isActive && "text-primary-foreground hover:text-primary-foreground hover:bg-primary/20"
                      )}
                      aria-label="Delete conversation"
                    >
                      <Trash2 className="size-3" />
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

