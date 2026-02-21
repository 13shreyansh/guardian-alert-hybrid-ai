// MOCK LOGIC - Will be replaced with real FunctionGemma + Gemini hybrid AI brain

export interface EmergencyAnalysisResult {
  action: "send_alert" | "log_only";
  emergencyType: string;
  aiSource: "local_ai" | "cloud_ai";
  responseTimeMs: number;
  aiConfidence: number;
}

export const analyzeEmergency = (
  soundDescription: string,
  volumeLevel: string,
  confidence: number,
  durationSeconds: number
): EmergencyAnalysisResult => {
  const desc = soundDescription.toLowerCase();

  // False alarm detection
  if (desc.includes("dog") || desc.includes("bark") || desc.includes("traffic")) {
    return {
      action: "log_only",
      emergencyType: "false_alarm",
      aiSource: "local_ai",
      responseTimeMs: 35,
      aiConfidence: 0.92,
    };
  }

  // High confidence + high volume → fast local decision
  if (confidence > 0.8 && volumeLevel === "high") {
    return {
      action: "send_alert",
      emergencyType: soundDescription,
      aiSource: "local_ai",
      responseTimeMs: 40,
      aiConfidence: 0.95,
    };
  }

  // Medium confidence → cloud verification
  if (confidence >= 0.5 && confidence <= 0.8) {
    return {
      action: "send_alert",
      emergencyType: soundDescription,
      aiSource: "cloud_ai",
      responseTimeMs: 1200,
      aiConfidence: 0.88,
    };
  }

  // Default fallback
  return {
    action: "send_alert",
    emergencyType: soundDescription,
    aiSource: "cloud_ai",
    responseTimeMs: 1500,
    aiConfidence: 0.70,
  };
};
