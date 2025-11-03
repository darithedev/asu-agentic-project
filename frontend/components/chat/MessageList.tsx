"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Message } from "@/lib/api";
import { parseMarkdown } from "@/lib/markdown";
import { AgentBadge } from "./AgentBadge";
import { cn } from "@/lib/utils";

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

function formatTimestamp(timestamp?: string): string {
  if (!timestamp) return "";
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const hours = Math.floor(diffMins / 60);
    if (hours < 24) return `${hours}h ago`;
    
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

const exampleQueries = [
  { text: "What are some travel tips for Tokyo?", agent: "travel_support" },
  { text: "How much does a flight to Paris cost?", agent: "booking_payments" },
  { text: "What is your cancellation policy?", agent: "policy" },
];

export function MessageList({ messages, isLoading = false }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    const scrollContainer = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement;
    if (scrollContainer) {
      // Use requestAnimationFrame to ensure DOM is updated
      requestAnimationFrame(() => {
        scrollContainer.scrollTo({
          top: scrollContainer.scrollHeight,
          behavior: 'smooth'
        });
      });
    }
  }, [messages.length, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center max-w-md space-y-4">
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Welcome to Travel Agency Customer Service</h3>
            <p className="text-sm text-muted-foreground">
              Ask me about destinations, bookings, payments, or policies. I'll route your question to the right specialist!
            </p>
          </div>
          <div className="space-y-2 pt-4">
            <p className="text-xs font-medium text-muted-foreground">Try asking:</p>
            <div className="flex flex-col gap-2">
              {exampleQueries.map((query, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    // This would be handled by parent component
                    const event = new CustomEvent('suggestQuery', { detail: query.text });
                    window.dispatchEvent(event);
                  }}
                  className="text-left text-sm p-3 rounded-lg border border-orange-200/60 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-gray-700 hover:border-orange-300/70 dark:hover:border-gray-600 transition-all shadow-sm hover:shadow-md text-foreground"
                >
                  {query.text}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full w-full" ref={scrollAreaRef}>
      <div className="flex flex-col gap-3 sm:gap-4 p-3 sm:p-4">
        {messages.map((message, index) => {
          const isEmptyAssistant = message.role === "assistant" && !message.content.trim();
          const showThinking = isEmptyAssistant && isLoading;
          const timestamp = formatTimestamp(message.timestamp);

          return (
            <div
              key={index}
              className={cn(
                "flex animate-in fade-in slide-in-from-bottom-2 duration-300",
                message.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              <Card
                className={cn(
                  "p-3 sm:p-4 transition-all",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground max-w-[90%] sm:max-w-[80%] shadow-sm shadow-blue-200/30"
                    : "bg-white dark:bg-gray-800 max-w-[90%] sm:max-w-[80%] shadow-sm shadow-gray-200/50 dark:shadow-black/30 border border-orange-200/50 dark:border-gray-700",
                  "rounded-2xl",
                  "hover:shadow-md hover:shadow-blue-100/40"
                )}
              >
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs sm:text-sm font-medium opacity-80">
                      {message.role === "user" ? "You" : "Assistant"}
                    </span>
                    {message.role === "assistant" && message.agent_type && (
                      <AgentBadge agentType={message.agent_type} />
                    )}
                  </div>
                  {timestamp && (
                    <span className="text-xs opacity-60">{timestamp}</span>
                  )}
                </div>
                {showThinking ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="flex gap-1 px-2">
                      <span className="thinking-dot"></span>
                      <span className="thinking-dot"></span>
                      <span className="thinking-dot"></span>
                    </div>
                    <span>Thinking...</span>
                  </div>
                ) : message.role === "assistant" ? (
                  <div className="text-sm markdown-content">
                    {(() => {
                      try {
                        const parsed = parseMarkdown(message.content);
                        return parsed.length > 0 ? parsed : (
                          <div className="text-foreground leading-relaxed whitespace-pre-wrap break-words">
                            {message.content}
                          </div>
                        );
                      } catch (error) {
                        console.error('Markdown parsing error:', error);
                        return (
                          <div className="text-foreground leading-relaxed whitespace-pre-wrap break-words">
                            {message.content}
                          </div>
                        );
                      }
                    })()}
                  </div>
                ) : (
                  <div className="text-sm whitespace-pre-wrap break-words leading-relaxed">
                    {message.content}
                  </div>
                )}
              </Card>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
    </ScrollArea>
  );
}

