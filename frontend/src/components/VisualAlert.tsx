import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";

type EmergencyType = "fire" | "earthquake" | "flood";

interface VisualAlertProps {
  emergencyType: EmergencyType;
  onDismiss: () => void;
  extraMessage?: string;
  aiDecision?: { aiSource: string; responseTimeMs: number } | null;
}

const emergencyConfig = {
  fire: {
    icon: "🔥",
    title: "FIRE ALERT",
    action: "EVACUATE NOW",
  },
  earthquake: {
    icon: "🌍",
    title: "EARTHQUAKE",
    action: "DROP, COVER, HOLD",
  },
  flood: {
    icon: "🌊",
    title: "FLOOD ALERT",
    action: "MOVE TO HIGH GROUND",
  },
};

const VisualAlert = ({ emergencyType, onDismiss, extraMessage, aiDecision }: VisualAlertProps) => {
  const vibrationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const vibrationPattern = [500, 200, 500, 200, 500];
    
    if (navigator.vibrate) {
      navigator.vibrate(vibrationPattern);
    }

    vibrationIntervalRef.current = setInterval(() => {
      if (navigator.vibrate) {
        navigator.vibrate(vibrationPattern);
      }
    }, 2000);

    return () => {
      if (vibrationIntervalRef.current) {
        clearInterval(vibrationIntervalRef.current);
      }
      if (navigator.vibrate) {
        navigator.vibrate(0);
      }
    };
  }, []);

  const handleDismiss = () => {
    if (vibrationIntervalRef.current) {
      clearInterval(vibrationIntervalRef.current);
    }
    if (navigator.vibrate) {
      navigator.vibrate(0);
    }
    onDismiss();
  };

  const config = emergencyConfig[emergencyType];

  return (
    <div 
      className="fixed inset-0 z-[9999] flex flex-col items-center justify-center animate-emergency-flash"
      style={{ minHeight: "100dvh" }}
    >
      <div className="flex flex-col items-center justify-center gap-6 text-center px-6">
        <span 
          className="leading-none"
          style={{ fontSize: "clamp(60px, 15vw, 80px)" }}
        >
          {config.icon}
        </span>
        
        <h1 
          className="font-bold text-white leading-tight"
          style={{ 
            fontSize: "clamp(32px, 10vw, 48px)",
            textShadow: "2px 2px 4px rgba(0, 0, 0, 0.8)",
          }}
        >
          {config.title}
        </h1>
        
        <p 
          className="text-white font-semibold"
          style={{ 
            fontSize: "clamp(18px, 5vw, 24px)",
            textShadow: "1px 1px 3px rgba(0, 0, 0, 0.8)",
          }}
        >
          {config.action}
        </p>
        
        {extraMessage && (
          <p 
            className="text-white/90 font-medium"
            style={{ 
              fontSize: "clamp(16px, 4vw, 20px)",
              textShadow: "1px 1px 3px rgba(0, 0, 0, 0.8)",
            }}
          >
            {extraMessage}
          </p>
        )}

        {/* AI Decision Badge */}
        {aiDecision && (
          <div 
            className="mt-2 inline-flex items-center gap-2 rounded-full px-4 py-1.5"
            style={{ 
              backgroundColor: aiDecision.aiSource === "local_ai" ? "rgba(59,130,246,0.25)" : "rgba(249,115,22,0.25)",
              backdropFilter: "blur(4px)",
            }}
          >
            <span 
              className="text-sm font-semibold text-white"
            >
              {aiDecision.aiSource === "local_ai" ? "🔵 Local AI" : "🟠 Cloud AI"} — {aiDecision.responseTimeMs}ms
            </span>
          </div>
        )}

        <Button
          onClick={handleDismiss}
          className="mt-8 bg-white text-gray-900 hover:bg-gray-100 font-bold text-lg rounded-xl min-h-[56px]"
          style={{ 
            padding: "16px 64px",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
          }}
        >
          I'm Safe
        </Button>
      </div>
    </div>
  );
};

export default VisualAlert;
