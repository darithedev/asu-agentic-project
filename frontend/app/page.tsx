import { ChatInterface } from "@/components/chat/ChatInterface";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-muted/20 p-2 sm:p-4 md:p-6">
      <div className="w-full h-full animate-in fade-in duration-500">
        <ChatInterface />
      </div>
    </div>
  );
}
