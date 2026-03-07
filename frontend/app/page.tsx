'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { DashboardLayout } from './components/dashboard/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, AlertTriangle, Network, Shield, Loader2, HardDrive, Link as LinkIcon, Settings as SettingsIcon } from 'lucide-react';
import { OverviewChart } from './components/dashboard/OverviewChart';
import { AlertsTable } from './components/dashboard/AlertsTable';
import { TrafficStats } from './components/dashboard/TrafficStats';
import { SystemMetrics } from './components/dashboard/SystemMetrics';
import { DetectionPanel } from './components/dashboard/DetectionPanel';
import { SettingsPanel } from './components/dashboard/SettingsPanel';
import { BlockchainPanel } from './components/dashboard/BlockchainPanel';
import { useNIDSData } from '@/lib/hooks/useNIDSData';

export default function DashboardPage() {
  const { alerts, trafficData, metrics, isLoading, error } = useNIDSData();
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState('overview');

  // Handle URL tab parameter
  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam && ['overview', 'alerts', 'traffic', 'detection', 'system', 'settings', 'blockchain'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  // Adapt basic traffic data to the schema expected by TrafficStats
  const trafficDataEnriched = trafficData.map(t => ({
    ...t,
    protocolBreakdown: { tcp: 0, udp: 0, icmp: 0, other: 0 },
    threatTypes: { malware: 0, intrusion: 0, exploit: 0, other: t.threats },
  }));

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center text-red-500">
        <AlertTriangle className="mr-2 h-5 w-5" />
        <span>{error}</span>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="alerts" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Alerts
            {alerts.length > 0 && (
              <span className="ml-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                {alerts.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="blockchain" className="flex items-center gap-2">
            <LinkIcon className="h-4 w-4" />
            Blockchain
          </TabsTrigger>
          <TabsTrigger value="traffic" className="flex items-center gap-2">
            <Network className="h-4 w-4" />
            Traffic
          </TabsTrigger>
          <TabsTrigger value="detection" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Detection
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center gap-2">
            <HardDrive className="h-4 w-4" />
            System
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <SettingsIcon className="h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{alerts.length}</div>
                <p className="text-xs text-muted-foreground">
                  {alerts.filter(a => a.severity === 'high' || a.severity === 'critical').length} critical
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network Traffic</CardTitle>
                <Network className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Math.round(trafficData.reduce((sum, t) => sum + t.incoming + t.outgoing, 0) / 1000)}k
                </div>
                <p className="text-xs text-muted-foreground">
                  {trafficData[0]?.threats || 0} threats blocked
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Math.round(metrics.cpu)}%</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.cpu > 80 ? 'High' : metrics.cpu > 50 ? 'Moderate' : 'Low'} load
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Math.round(metrics.memory)}%</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.memory > 80 ? 'High' : 'Normal'} usage
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Traffic Overview</CardTitle>
              </CardHeader>
              <CardContent className="pl-2">
                <OverviewChart data={trafficData} />
              </CardContent>
            </Card>
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Recent Alerts</CardTitle>
                <CardDescription>Latest security events</CardDescription>
              </CardHeader>
              <CardContent>
                <AlertsTable alerts={alerts.slice(0, 5)} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Security Alerts</CardTitle>
              <CardDescription>View and manage security events</CardDescription>
            </CardHeader>
            <CardContent>
              <AlertsTable alerts={alerts} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="blockchain">
          <BlockchainPanel />
        </TabsContent>

        <TabsContent value="traffic">
          <TrafficStats data={trafficDataEnriched as any} />
        </TabsContent>

        <TabsContent value="detection">
          <DetectionPanel />
        </TabsContent>

        <TabsContent value="system">
          <SystemMetrics metrics={metrics} />
        </TabsContent>

        <TabsContent value="settings">
          <SettingsPanel />
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  );
}
