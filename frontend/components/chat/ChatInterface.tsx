"use client";

import { useState, useCallback, useEffect } from "react";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { streamChatMessage, Message, ChatRequest } from "@/lib/api";
import { cn } from "@/lib/utils";

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [currentAgentType, setCurrentAgentType] = useState<string | undefined>();

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
  };

  return (
    <Card className={cn(
      "flex flex-col w-full mx-auto",
      "h-screen sm:h-[600px] md:min-h-[600px] md:max-h-[800px]",
      "max-w-4xl",
      "rounded-lg sm:rounded-xl shadow-lg"
    )}>
      <div className="flex items-center justify-between p-3 sm:p-4 border-b bg-muted/30">
        <div className="flex-1 min-w-0">
          <h1 className="text-lg sm:text-xl font-semibold truncate">
            Travel Agency Customer Service
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground truncate">
            Ask about destinations, bookings, payments, or policies
          </p>
        </div>
        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClear}
            className="shrink-0 ml-2"
            aria-label="Clear conversation"
          >
            <Trash2 className="size-4" />
          </Button>
        )}
      </div>
      <div className="flex-1 overflow-hidden min-h-0">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>
      <MessageInput onSend={handleSend} disabled={isLoading} />
    </Card>
  );
}

