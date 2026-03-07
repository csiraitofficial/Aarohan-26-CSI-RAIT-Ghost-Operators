"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { startSniffer, stopSniffer, updateSnifferConfig } from "@/lib/api";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { HelpCircle, Play, Square, Save, Activity, Shield } from "lucide-react";

export function SettingsPanel() {
  const [iface, setIface] = useState<string>("Loopback Pseudo-Interface 1");
  const [pktCount, setPktCount] = useState<number>(1000);
  const [timeout, setTimeoutVal] = useState<number>(30);
  const [bpf, setBpf] = useState<string>("");

  const [modelPath, setModelPath] = useState<string>("app/ml_models/nids_model.joblib");
  const [confidence, setConfidence] = useState<number>(0.8);

  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>("");

  const handleStart = async () => {
    try {
      setBusy(true);
      setMessage("");
      const config = {
        interface: iface,
        packet_count: pktCount,
        timeout: timeout,
        filter: bpf || undefined,
      };
      await startSniffer(config);
      setMessage("Sniffer started successfully");
    } catch (e: any) {
      setMessage(e?.message || "Failed to start sniffer");
    } finally {
      setBusy(false);
    }
  };

  const handleStop = async () => {
    try {
      setBusy(true);
      setMessage("");
      await stopSniffer();
      setMessage("Sniffer stopped successfully");
    } catch (e: any) {
      setMessage(e?.message || "Failed to stop sniffer");
    } finally {
      setBusy(false);
    }
  };

  const handleSaveConfigs = async () => {
    try {
      setBusy(true);
      setMessage("");
      await updateSnifferConfig({
        interface: iface,
        packet_count: pktCount,
        timeout: timeout,
        filter: bpf || undefined,
      });
      // ML config update not implemented on backend route yet
      setMessage("Sniffer configuration updated");
    } catch (e: any) {
      setMessage(e?.message || "Failed to update configuration");
    } finally {
      setBusy(false);
    }
  };

  return (
    <TooltipProvider>
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              Sniffer Settings
            </CardTitle>
            <CardDescription>Configure network capture engine</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="iface">Network Interface</Label>
              <Input id="iface" value={iface} onChange={(e) => setIface(e.target.value)} placeholder="e.g. eth0, wlan0" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="pkt">Max Packets</Label>
                <Input id="pkt" type="number" value={pktCount} onChange={(e) => setPktCount(parseInt(e.target.value || "0"))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timeout">Timeout (seconds)</Label>
                <Input id="timeout" type="number" value={timeout} onChange={(e) => setTimeoutVal(parseInt(e.target.value || "0"))} />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="bpf">BPF Filter String</Label>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">Optional Berkeley Packet Filter (e.g., "tcp port 80")</p>
                  </TooltipContent>
                </Tooltip>
              </div>
              <Input id="bpf" value={bpf} onChange={(e) => setBpf(e.target.value)} placeholder="e.g. tcp or udp port 53" />
            </div>
            <div className="flex items-center gap-3 pt-2">
              <Button onClick={handleStart} disabled={busy} className="bg-green-600 hover:bg-green-700">
                <Play className="mr-2 h-4 w-4" /> Start Capture
              </Button>
              <Button variant="destructive" onClick={handleStop} disabled={busy}>
                <Square className="mr-2 h-4 w-4" /> Stop Capture
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              ML & Detection
            </CardTitle>
            <CardDescription>Machine Learning model parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="model">Model File Path</Label>
              <Input id="model" value={modelPath} onChange={(e) => setModelPath(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="conf">Confidence Threshold</Label>
              <div className="flex items-center gap-4">
                <Input
                  id="conf"
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={confidence}
                  onChange={(e) => setConfidence(parseFloat(e.target.value))}
                  className="flex-1"
                />
                <Badge variant="secondary" className="w-12 justify-center">{confidence}</Badge>
              </div>
            </div>
            <div className="flex flex-col gap-4 pt-2">
              <Button variant="outline" onClick={handleSaveConfigs} disabled={busy}>
                <Save className="mr-2 h-4 w-4" /> Update Configurations
              </Button>
              {message && (
                <div className={`text-sm px-3 py-2 rounded-md ${message.includes('Failed') ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500'}`}>
                  {message}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  );
}

