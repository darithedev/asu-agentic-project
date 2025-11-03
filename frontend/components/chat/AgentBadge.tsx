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
      colorClass: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
      iconColorClass: "text-blue-600 dark:text-blue-400",
    },
    booking_payments: {
      label: "Booking & Payments",
      icon: CreditCard,
      colorClass: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
      iconColorClass: "text-green-600 dark:text-green-400",
    },
    policy: {
      label: "Policy",
      icon: Shield,
      colorClass: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
      iconColorClass: "text-purple-600 dark:text-purple-400",
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

