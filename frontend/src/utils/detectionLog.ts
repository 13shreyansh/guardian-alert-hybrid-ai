import { type EmergencyAnalysisResult } from "@/services/hybridAIService";

export interface DetectionLogEntry {
  id: number;
  type: "fire" | "earthquake" | "flood" | "false_alarm";
  timestamp: number;
  source: "automatic" | "manual" | "ai_filtered";
  description: string;
  actionTaken: string;
  status: "resolved" | "pending" | "filtered";
  aiDecision?: EmergencyAnalysisResult;
}

const STORAGE_KEY = "guardian_detection_log";
const MAX_ENTRIES = 50;

export const getDetectionLog = (): DetectionLogEntry[] => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error("Failed to parse detection log:", e);
  }
  return [];
};

export const addDetectionEntry = (
  type: DetectionLogEntry["type"],
  source: DetectionLogEntry["source"],
  contactCount: number = 0
): DetectionLogEntry[] => {
  const log = getDetectionLog();
  
  const description = source === "automatic" 
    ? `${type === "fire" ? "Fire alarm" : type === "earthquake" ? "Earthquake" : "Flood warning"} detected`
    : "Manual emergency report";
  
  const actionTaken = contactCount > 0 
    ? `Alert triggered, SMS sent to ${contactCount} contact${contactCount > 1 ? "s" : ""}`
    : "Alert triggered";
  
  const newEntry: DetectionLogEntry = {
    id: Date.now(),
    type,
    timestamp: Date.now(),
    source,
    description,
    actionTaken,
    status: "resolved",
  };
  
  // Add to beginning, keep only MAX_ENTRIES
  const updated = [newEntry, ...log].slice(0, MAX_ENTRIES);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
};

export const addFalseAlarmEntry = (
  soundDescription: string,
  aiDecision: EmergencyAnalysisResult
): DetectionLogEntry[] => {
  const log = getDetectionLog();
  
  const newEntry: DetectionLogEntry = {
    id: Date.now(),
    type: "false_alarm",
    timestamp: Date.now(),
    source: "ai_filtered",
    description: `Filtered: "${soundDescription}" identified as false alarm`,
    actionTaken: `AI Brain (${aiDecision.aiSource}) filtered in ${aiDecision.responseTimeMs}ms — no alert sent`,
    status: "filtered",
    aiDecision,
  };
  
  const updated = [newEntry, ...log].slice(0, MAX_ENTRIES);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
};

export const clearDetectionLog = () => {
  localStorage.removeItem(STORAGE_KEY);
};

export const formatDetectionTime = (timestamp: number): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
};

export const formatDetectionLabel = (type: DetectionLogEntry["type"]): string => {
  switch (type) {
    case "fire":
      return "🔥 Fire alarm detected";
    case "earthquake":
      return "🌍 Earthquake alert";
    case "flood":
      return "🌊 Flood warning";
    case "false_alarm":
      return "🧠 Filtered false alarm";
    default:
      return "Alert triggered";
  }
};
