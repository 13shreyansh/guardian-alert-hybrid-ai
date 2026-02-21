import { Brain, Zap, Filter, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { type EmergencyAnalysisResult } from "@/services/hybridAIService";

export interface AIBrainStats {
  lastDecision: EmergencyAnalysisResult | null;
  lastSoundName: string | null;
  localCount: number;
  cloudCount: number;
  falseAlarmCount: number;
}

interface AIBrainMonitorProps {
  stats: AIBrainStats;
}

const AIBrainMonitor = ({ stats }: AIBrainMonitorProps) => {
  const { lastDecision, lastSoundName, localCount, cloudCount, falseAlarmCount } = stats;
  const totalDecisions = localCount + cloudCount;

  const lastDecisionText = lastDecision
    ? lastDecision.action === "send_alert"
      ? `${lastSoundName} → Emergency Alert Sent`
      : `${lastSoundName} → Filtered as False Alarm`
    : "No decisions yet";

  const isLocal = lastDecision?.aiSource === "local_ai";

  return (
    <Card className="border-border/50 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <Brain className="w-4 h-4 text-primary" />
          Hybrid AI Brain
          <span className="flex items-center gap-1 ml-auto">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-normal text-emerald-600 dark:text-emerald-400">Active</span>
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Last Decision */}
        <div className="flex items-start gap-2">
          <Activity className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
          <div>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Last Decision</p>
            <p className="text-sm font-medium text-foreground">{lastDecisionText}</p>
          </div>
        </div>

        {/* AI Source + Response Time */}
        {lastDecision && (
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-muted-foreground" />
              <Badge
                variant="secondary"
                className={
                  isLocal
                    ? "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30 text-xs"
                    : "bg-orange-500/15 text-orange-700 dark:text-orange-400 border-orange-500/30 text-xs"
                }
              >
                {isLocal ? "Local AI (FunctionGemma)" : "Cloud AI (Gemini)"}
              </Badge>
            </div>
            <span
              className="text-xs font-mono font-semibold text-emerald-600 dark:text-emerald-400"
            >
              {lastDecision.responseTimeMs}ms
            </span>
          </div>
        )}

        {/* Stats Row */}
        <div className="flex items-center justify-between pt-2 border-t border-border text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <span className="font-semibold text-foreground">{localCount}</span> Local
          </div>
          <span className="text-border">|</span>
          <div className="flex items-center gap-1">
            <span className="font-semibold text-foreground">{cloudCount}</span> Cloud
          </div>
          <span className="text-border">|</span>
          <div className="flex items-center gap-1">
            <Filter className="w-3 h-3" />
            <span className="font-semibold text-foreground">{falseAlarmCount}</span> Filtered
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AIBrainMonitor;
