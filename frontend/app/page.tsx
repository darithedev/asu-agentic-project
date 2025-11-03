import { ChatInterface } from "@/components/chat/ChatInterface";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 p-4 dark:bg-black">
      <ChatInterface />
    </div>
  );
}
