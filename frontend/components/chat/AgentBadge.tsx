"use client";

import { MapPin, CreditCard, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentBadgeProps {
  agentType: "travel_support" | "booking_payments" | "policy";
  className?: string;
}

export function AgentBadge({ agentType, className }: AgentBadgeProps) {
  const agentConfig = {
    travel_support: {
      label: "Travel Support",
      icon: MapPin,
      colorClass: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border border-blue-200/50",
      iconColorClass: "text-blue-600 dark:text-blue-400",
    },
    booking_payments: {
      label: "Booking & Payments",
      icon: CreditCard,
      colorClass: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200/50",
      iconColorClass: "text-emerald-600 dark:text-emerald-400",
    },
    policy: {
      label: "Policy",
      icon: Shield,
      colorClass: "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400 border border-violet-200/50",
      iconColorClass: "text-violet-600 dark:text-violet-400",
    },
  };

  const config = agentConfig[agentType];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium",
        config.colorClass,
        className
      )}
      aria-label={`Agent: ${config.label}`}
    >
      <Icon className={cn("size-3", config.iconColorClass)} />
      <span>{config.label}</span>
    </div>
  );
}

