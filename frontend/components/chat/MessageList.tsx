"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Message } from "@/lib/api";
import { parseMarkdown } from "@/lib/markdown";

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading = false }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p>Start a conversation by typing a message below.</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full w-full">
      <div className="flex flex-col gap-4 p-4">
        {messages.map((message, index) => {
          const isLastMessage = index === messages.length - 1;
          const isEmptyAssistant = message.role === "assistant" && !message.content.trim();
          const showThinking = isEmptyAssistant && isLoading;

          return (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <Card
                className={`max-w-[80%] p-3 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <div className="text-sm font-medium mb-1 opacity-70">
                  {message.role === "user" ? "You" : "Assistant"}
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
                          <div className="text-foreground leading-relaxed whitespace-pre-wrap">
                            {message.content}
                          </div>
                        );
                      } catch (error) {
                        console.error('Markdown parsing error:', error);
                        return (
                          <div className="text-foreground leading-relaxed whitespace-pre-wrap">
                            {message.content}
                          </div>
                        );
                      }
                    })()}
                  </div>
                ) : (
                  <div className="text-sm whitespace-pre-wrap break-words">
                    {message.content}
                  </div>
                )}
              </Card>
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}

