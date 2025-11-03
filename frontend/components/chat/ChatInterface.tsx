"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { ChatSidebar } from "./ChatSidebar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Trash2 } from "lucide-react";
import { streamChatMessage, Message, ChatRequest } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  Conversation,
  saveConversation,
  getConversation,
} from "@/lib/conversation-storage";

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [currentAgentType, setCurrentAgentType] = useState<string | undefined>();
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>();
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout>();

  // Auto-save conversation after messages change
  useEffect(() => {
    if (messages.length === 0) return;

    // Clear existing timeout
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }

    // Auto-save after 1 second of inactivity
    autoSaveTimeoutRef.current = setTimeout(() => {
      try {
        const conversation = saveConversation({
          id: currentConversationId,
          title: "",
          messages,
          sessionId,
        });
        setCurrentConversationId(conversation.id);
      } catch (error) {
        console.error("Error auto-saving conversation:", error);
      }
    }, 1000);

    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [messages, sessionId, currentConversationId]);

  const handleSend = useCallback(
    async (userMessage: string) => {
      // Add user message immediately
      const userMsg: Message = {
        role: "user",
        content: userMessage,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setCurrentAgentType(undefined);

      // Create placeholder assistant message for streaming
      const assistantMsg: Message = {
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Prepare request
      const request: ChatRequest = {
        message: userMessage,
        session_id: sessionId,
        conversation_history: messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        })),
      };

      try {
        await streamChatMessage(
          request,
          // onChunk: Update the last message as chunks arrive
          (chunk: string) => {
            setMessages((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  content: updated[lastIndex].content + chunk,
                };
              }
              return updated;
            });
          },
          // onComplete: Finalize the message
          (fullMessage: string, newSessionId: string, agentType?: string) => {
            setMessages((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  content: fullMessage,
                  agent_type: agentType as "travel_support" | "booking_payments" | "policy" | undefined,
                };
              }
              return updated;
            });
            setSessionId(newSessionId);
            if (agentType) {
              setCurrentAgentType(agentType);
            }
            setIsLoading(false);
          },
          // onError: Handle errors
          (error: Error) => {
            setMessages((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  content: `Error: ${error.message}. Please try again.`,
                };
              }
              return updated;
            });
            setIsLoading(false);
          }
        );
      } catch (error) {
        setMessages((prev) => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
            updated[lastIndex] = {
              ...updated[lastIndex],
              content: `Error: ${
                error instanceof Error ? error.message : "Unknown error"
              }. Please try again.`,
            };
          }
          return updated;
        });
        setIsLoading(false);
      }
    },
    [messages, sessionId]
  );

  // Handle example query clicks from MessageList
  useEffect(() => {
    const handleSuggestQuery = (event: CustomEvent<string>) => {
      handleSend(event.detail);
    };

    window.addEventListener('suggestQuery', handleSuggestQuery as EventListener);
    return () => {
      window.removeEventListener('suggestQuery', handleSuggestQuery as EventListener);
    };
  }, [handleSend]);

  const handleClear = () => {
    setMessages([]);
    setSessionId(undefined);
    setCurrentAgentType(undefined);
    setCurrentConversationId(undefined);
  };

  const handleNewConversation = () => {
    handleClear();
  };

  const handleSelectConversation = (conversation: Conversation) => {
    setMessages(conversation.messages);
    setSessionId(conversation.sessionId);
    setCurrentConversationId(conversation.id);
    setCurrentAgentType(undefined);
  };

  return (
    <div className="flex h-[calc(100vh-2rem)] sm:h-[calc(100vh-4rem)] md:h-[calc(100vh-3rem)] w-full max-w-7xl mx-auto bg-white rounded-lg sm:rounded-xl shadow-xl shadow-blue-100/50 border border-orange-200/60 overflow-hidden">
      {/* Sidebar */}
      <div className="hidden md:flex w-64 shrink-0">
        <ChatSidebar
          currentConversationId={currentConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />
      </div>

      {/* Main Chat Area */}
      <Card className={cn(
        "flex flex-col flex-1",
        "min-h-0",
        "rounded-none sm:rounded-l-none",
        "border-0 border-l border-orange-200/60",
        "bg-white"
      )}>
      <div className="flex items-center justify-between p-3 sm:p-4 border-b border-orange-200/60 bg-gradient-to-r from-blue-50/30 to-white">
        <div className="flex-1 min-w-0">
          <h1 className="text-lg sm:text-xl font-semibold truncate">
            Travel Agency Customer Service
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground truncate">
            Ask about destinations, bookings, payments, or policies
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <ThemeToggle />
          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClear}
              className="shrink-0"
              aria-label="Clear conversation"
            >
              <Trash2 className="size-4" />
            </Button>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-hidden min-h-0">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>
      <MessageInput onSend={handleSend} disabled={isLoading} />
      </Card>
    </div>
  );
}

