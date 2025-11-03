import { ChatInterface } from "@/components/chat/ChatInterface";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-blue-50/50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 p-2 sm:p-4 md:p-6 relative overflow-hidden">
      {/* Subtle cloud-like shapes for depth - light mode only */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none dark:hidden">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-100/30 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-50/40 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-50/20 rounded-full blur-3xl"></div>
      </div>
      {/* Dark mode subtle glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none hidden dark:block">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-950/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-900/10 rounded-full blur-3xl"></div>
      </div>
      <div className="w-full max-w-full h-full animate-in fade-in duration-500 relative z-10">
        <ChatInterface />
      </div>
    </div>
  );
}
