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
  const currentConversationIdRef = useRef<string | undefined>();
  const isLoadingConversationRef = useRef<boolean>(false);
  
  // Keep ref in sync with state
  useEffect(() => {
    currentConversationIdRef.current = currentConversationId;
  }, [currentConversationId]);

  // Auto-save conversation after messages change
  useEffect(() => {
    // Don't auto-save if we're loading a conversation or if messages are empty
    if (messages.length === 0 || isLoadingConversationRef.current) return;

    // Don't auto-save if we don't have a conversation ID yet
    if (!currentConversationIdRef.current) return;

    // Clear existing timeout
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }

    // Capture the current conversation ID and messages at the time of scheduling
    // Make a deep copy of messages to prevent reference sharing issues
    // This prevents race conditions when switching conversations
    const conversationIdToSave = currentConversationIdRef.current;
    const messagesToSave = messages.map(msg => ({ ...msg }));
    const sessionIdToSave = sessionId;

    // Auto-save after 1 second of inactivity
    autoSaveTimeoutRef.current = setTimeout(() => {
      // Double-check that we're still saving the same conversation
      // If the conversation changed, don't save
      if (currentConversationIdRef.current !== conversationIdToSave) {
        console.log(`Skipping auto-save: conversation changed from ${conversationIdToSave} to ${currentConversationIdRef.current}`);
        return;
      }

      // Double-check that we're not loading a conversation
      if (isLoadingConversationRef.current) {
        console.log('Skipping auto-save: conversation is being loaded');
        return;
      }

      // Verify we have messages to save
      if (!messagesToSave || messagesToSave.length === 0) {
        console.log('Skipping auto-save: no messages to save');
        return;
      }

      try {
        console.log(`Auto-saving conversation ${conversationIdToSave} with ${messagesToSave.length} messages`);
        const conversation = saveConversation({
          id: conversationIdToSave,
          title: "",
          messages: messagesToSave,
          sessionId: sessionIdToSave,
        });
        
        // Only update if we're still on the same conversation
        if (currentConversationIdRef.current === conversationIdToSave) {
          setCurrentConversationId(conversation.id);
          currentConversationIdRef.current = conversation.id;
        }
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
            
            // Cancel any pending auto-save since we're saving immediately after completion
            // This prevents duplicate conversations from being created
            if (autoSaveTimeoutRef.current) {
              clearTimeout(autoSaveTimeoutRef.current);
              autoSaveTimeoutRef.current = undefined;
            }
            
            // Save conversation immediately after completion
            // Use setTimeout to ensure state has updated
            setTimeout(() => {
              setMessages((currentMessages) => {
                try {
                  // Make a deep copy of messages to prevent reference sharing
                  const messagesCopy = currentMessages.map(msg => ({ ...msg }));
                  const conversation = saveConversation({
                    id: currentConversationIdRef.current,
                    title: "",
                    messages: messagesCopy,
                    sessionId: newSessionId,
                  });
                  setCurrentConversationId(conversation.id);
                  currentConversationIdRef.current = conversation.id;
                } catch (error) {
                  console.error("Error saving conversation after completion:", error);
                }
                return currentMessages;
              });
            }, 200);
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

  const handleClear = useCallback(() => {
    // Clear any pending auto-save to prevent it from saving the old conversation
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
      autoSaveTimeoutRef.current = undefined;
    }
    
    // Set loading flag to prevent auto-save from triggering
    isLoadingConversationRef.current = true;
    
    setMessages([]);
    setSessionId(undefined);
    setCurrentAgentType(undefined);
    setCurrentConversationId(undefined);
    currentConversationIdRef.current = undefined;
    
    // Allow auto-save after a short delay to ensure state has settled
    setTimeout(() => {
      isLoadingConversationRef.current = false;
    }, 500);
  }, []);

  const handleNewConversation = useCallback(() => {
    handleClear();
  }, [handleClear]);

  const handleSelectConversation = useCallback((conversation: Conversation) => {
    // Don't reload if it's already the current conversation
    if (currentConversationId === conversation.id) {
      return;
    }
    
    // Clear any pending auto-save
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
    
    // Set flag to prevent auto-save during load
    isLoadingConversationRef.current = true;
    
    // Fetch the conversation fresh from storage to ensure we have the latest data
    // This prevents issues with stale conversation objects from the sidebar
    const freshConversation = getConversation(conversation.id);
    
    if (!freshConversation) {
      console.error(`Conversation ${conversation.id} not found in storage`);
      isLoadingConversationRef.current = false;
      return;
    }
    
    // Verify we're loading the correct conversation
    if (freshConversation.id !== conversation.id) {
      console.error(`Conversation ID mismatch: expected ${conversation.id}, got ${freshConversation.id}`);
      isLoadingConversationRef.current = false;
      return;
    }
    
    // Load conversation messages (make a deep copy to avoid mutations)
    // Ensure all messages have proper content (handle any missing or malformed data)
    const messagesCopy = freshConversation.messages
      .map(msg => ({
        ...msg,
        content: String(msg.content || ""), // Ensure content is always a string
        role: msg.role || "user", // Ensure role is set
        timestamp: msg.timestamp || new Date().toISOString(), // Ensure timestamp exists
        agent_type: msg.agent_type, // Preserve agent_type if present
      }))
      .filter(msg => {
        // Filter out completely invalid messages
        return msg.role && (msg.content !== undefined && msg.content !== null);
      });
    
    // Log first message content to verify we're loading the right conversation
    const firstUserMsg = messagesCopy.find(m => m.role === "user");
    console.log(`Loading conversation ${freshConversation.id} (title: "${freshConversation.title}") with ${messagesCopy.length} messages. First message: "${firstUserMsg?.content?.substring(0, 50) || 'none'}"`);
    
    // Set messages using a function to ensure we're setting the exact array
    setMessages(() => messagesCopy);
    setSessionId(freshConversation.sessionId);
    setCurrentConversationId(freshConversation.id);
    currentConversationIdRef.current = freshConversation.id;
    setCurrentAgentType(undefined);
    
    // Allow auto-save after a delay to ensure state has settled
    // Use a longer timeout to prevent auto-save from triggering immediately after loading
    setTimeout(() => {
      isLoadingConversationRef.current = false;
    }, 2000);
  }, [currentConversationId]);

  return (
    <div className="flex h-[calc(100vh-2rem)] sm:h-[calc(100vh-4rem)] md:h-[calc(100vh-3rem)] w-full max-w-7xl mx-auto bg-white dark:bg-gray-900 rounded-lg sm:rounded-xl shadow-xl shadow-blue-100/50 dark:shadow-black/50 border border-orange-200/60 dark:border-gray-700 overflow-hidden">
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
        "border-0 border-l border-orange-200/60 dark:border-gray-700",
        "bg-white dark:bg-gray-900"
      )}>
      <div className="flex items-center justify-between p-3 sm:p-4 border-b border-orange-200/60 dark:border-gray-700 bg-gradient-to-r from-blue-50/30 to-white dark:from-gray-800 dark:to-gray-900">
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

