"use client";

import { useState, useCallback } from "react";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { Card } from "@/components/ui/card";
import { streamChatMessage, Message, ChatRequest } from "@/lib/api";

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [currentMessage, setCurrentMessage] = useState("");

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

      // Create placeholder assistant message for streaming
      const assistantMsg: Message = {
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setCurrentMessage("");

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
          (fullMessage: string, newSessionId: string) => {
            setMessages((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  content: fullMessage,
                };
              }
              return updated;
            });
            setSessionId(newSessionId);
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

  return (
    <Card className="flex flex-col h-[600px] w-full max-w-4xl mx-auto">
      <div className="p-4 border-b">
        <h1 className="text-xl font-semibold">Travel Agency Customer Service</h1>
        <p className="text-sm text-muted-foreground">
          Ask about destinations, bookings, payments, or policies
        </p>
      </div>
      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} />
      </div>
      <MessageInput onSend={handleSend} disabled={isLoading} />
    </Card>
  );
}

