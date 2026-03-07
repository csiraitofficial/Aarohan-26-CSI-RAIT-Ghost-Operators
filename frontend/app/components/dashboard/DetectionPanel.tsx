"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AlertTriangle, Brain, Shield, HelpCircle, RefreshCw } from "lucide-react";
import { fetchStats } from "@/lib/api";

interface RuleStat {
  id: string;
  name: string;
  enabled: boolean;
  matches: number;
  severity?: string;
}

export function DetectionPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mlStats, setMlStats] = useState<any>({});
  const [sigStats, setSigStats] = useState<{ enabled_rules?: RuleStat[]; enabled_rules_count?: number; total_rules?: number; top_rules?: any[] }>({});
  const [detectionRates, setDetectionRates] = useState<any>({});

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const stats = await fetchStats();
      setMlStats(stats.ml_stats || {});
      setSigStats(stats.signature_stats || {});
      setDetectionRates(stats.detection_rates || {});
    } catch (e: any) {
      setError(e?.message || "Failed to load detection stats");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <TooltipProvider>
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div>
                <CardTitle className="text-sm font-medium">ML Detections</CardTitle>
                <CardDescription>Anomaly detection via model</CardDescription>
              </div>
              <Brain className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{mlStats?.anomalies_detected ?? 0}</div>
              <p className="text-xs text-muted-foreground">Model: {mlStats?.model_type || "-"}</p>
              <div className="mt-2 text-xs text-muted-foreground">
                <span>Last test F1: {mlStats?.last_metrics?.f1?.toFixed?.(3) || "-"}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div>
                <CardTitle className="text-sm font-medium">Signature Matches</CardTitle>
                <CardDescription>Rule-based detections</CardDescription>
              </div>
              <Shield className="h-5 w-5 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{
                (() => {
                  const rules = Array.isArray(sigStats?.top_rules) ? sigStats.top_rules : [];
                  const sum = rules.reduce((s: number, r: any) => s + (r?.matches ?? r?.matches_count ?? 0), 0);
                  return sum;
                })()
              }</div>
              <p className="text-xs text-muted-foreground">Enabled rules: {sigStats?.enabled_rules_count ?? (Array.isArray(sigStats?.enabled_rules) ? sigStats.enabled_rules.length : 0)} / {sigStats?.total_rules ?? "-"}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div>
                <CardTitle className="text-sm font-medium">Detection Rates</CardTitle>
                <CardDescription>Performance snapshot</CardDescription>
              </div>
              <AlertTriangle className="h-5 w-5 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <div className="text-muted-foreground">ML</div>
                  <div className="font-semibold">{(detectionRates?.ml_detection_rate ?? 0).toFixed(3)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Signature</div>
                  <div className="font-semibold">{(detectionRates?.signature_detection_rate ?? 0).toFixed(3)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Overall</div>
                  <div className="font-semibold">{(detectionRates?.overall_detection_rate ?? 0).toFixed(3)}</div>
                </div>
              </div>
              <Button size="sm" variant="outline" className="mt-3" onClick={load} disabled={loading}>
                <RefreshCw className="mr-2 h-3.5 w-3.5 animate-spin" style={{ animationPlayState: loading ? "running" : "paused" }} />
                Refresh
              </Button>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Enabled Signature Rules</CardTitle>
            <CardDescription>Current active detection rules</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rule</TableHead>
                    <TableHead className="w-[140px]">Matches</TableHead>
                    <TableHead className="w-[120px] text-right">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(sigStats?.enabled_rules ?? []).map((r: RuleStat) => (
                    <TableRow key={r.id}>
                      <TableCell>{r.name || r.id}</TableCell>
                      <TableCell>{r.matches ?? 0}</TableCell>
                      <TableCell className="text-right">
                        {r.enabled ? (
                          <Badge variant="outline" className="text-emerald-600">Enabled</Badge>
                        ) : (
                          <Badge variant="destructive">Disabled</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {(sigStats?.enabled_rules?.length ?? 0) === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-muted-foreground text-sm py-6">
                        No enabled rules
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {error && (
          <div className="text-sm text-red-500">{error}</div>
        )}
      </div>
    </TooltipProvider>
  );
}
