'use client';
import React, { useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  Activity, 
  Network, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  BarChart2, 
  Clock, 
  HelpCircle, 
  ShieldCheck,
  ArrowDown,
  ArrowUp,
  Server,
  Wifi,
  AlertCircle
} from 'lucide-react';
import { 
  Area, 
  AreaChart, 
  Bar, 
  BarChart, 
  ResponsiveContainer, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Legend, 
  Cell, 
  Pie, 
  PieChart,
  Tooltip as RechartsTooltip,
  ReferenceLine,
  Label
} from 'recharts';
import { useMemo, useState } from 'react';
import { cn } from '@/lib/utils';

export interface TrafficDataPoint {
  timestamp: string;
  incoming: number;
  outgoing: number;
  threats: number;
  protocolBreakdown: {
    tcp: number;
    udp: number;
    icmp: number;
    other: number;
  };
  threatTypes: {
    malware: number;
    intrusion: number;
    exploit: number;
    other: number;
  };
}

interface TrafficStatsProps {
  data: TrafficDataPoint[];
}

const timeRanges = [
  { value: '1h', label: '1H', minutes: 60 },
  { value: '6h', label: '6H', minutes: 360 },
  { value: '12h', label: '12H', minutes: 720 },
  { value: '1d', label: '24H', minutes: 1440 },
];

const COLORS = {
  incoming: '#3b82f6',
  outgoing: '#8b5cf6',
  threats: '#ef4444',
  tcp: '#3b82f6',
  udp: '#8b5cf6',
  icmp: '#10b981',
  other: '#6b7280',
  malware: '#ef4444',
  intrusion: '#f59e0b',
  exploit: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6'
};

export const TrafficStats: React.FC<TrafficStatsProps> = ({ data }) => {
  const [timeRange, setTimeRange] = useState('6h');
  const [activeTab, setActiveTab] = useState('overview');
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const filteredData = useMemo(() => {
    if (!isClient) return [];
    const minutes = timeRanges.find(range => range.value === timeRange)?.minutes || 360;
    const cutoff = new Date();
    cutoff.setMinutes(cutoff.getMinutes() - minutes);
    return data.filter(item => new Date(item.timestamp) >= cutoff);
  }, [data, timeRange, isClient]);

  const latestData = filteredData[filteredData.length - 1];
  const previousData = filteredData[filteredData.length - 2];

  const totalIncoming = filteredData.reduce((sum, item) => sum + item.incoming, 0);
  const totalOutgoing = filteredData.reduce((sum, item) => sum + item.outgoing, 0);
  const totalThreats = filteredData.reduce((sum, item) => sum + item.threats, 0);
  const avgThreatsPerHour = totalThreats / (filteredData.length || 1);

  const incomingChange = previousData
    ? ((latestData?.incoming || 0) - (previousData?.incoming || 0)) / (previousData?.incoming || 1) * 100
    : 0;
  const outgoingChange = previousData
    ? ((latestData?.outgoing || 0) - (previousData?.outgoing || 0)) / (previousData?.outgoing || 1) * 100
    : 0;

  const protocolData = [
    { name: 'TCP', value: latestData?.protocolBreakdown?.tcp || 0, color: COLORS.tcp },
    { name: 'UDP', value: latestData?.protocolBreakdown?.udp || 0, color: COLORS.udp },
    { name: 'ICMP', value: latestData?.protocolBreakdown?.icmp || 0, color: COLORS.icmp },
    { name: 'Other', value: latestData?.protocolBreakdown?.other || 0, color: COLORS.other },
  ];

  const threatData = [
    { name: 'Malware', value: latestData?.threatTypes?.malware || 0, color: COLORS.malware },
    { name: 'Intrusion', value: latestData?.threatTypes?.intrusion || 0, color: COLORS.intrusion },
    { name: 'Exploit', value: latestData?.threatTypes?.exploit || 0, color: COLORS.exploit },
    { name: 'Other', value: latestData?.threatTypes?.other || 0, color: COLORS.other },
  ];

  const trafficChartData = useMemo(() => {
    if (!isClient) return [];
    return filteredData.map(item => ({
      time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      timestamp: new Date(item.timestamp).getTime(),
      incoming: item.incoming,
      outgoing: item.outgoing,
      threats: item.threats,
      total: item.incoming + item.outgoing,
      threatPercentage: (item.threats / (item.incoming + item.outgoing + 1)) * 100
    }));
  }, [filteredData, isClient]);

  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = 25 + innerRadius + (outerRadius - innerRadius);
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="#6b7280"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-xs"
      >
        {`${name} ${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border rounded-lg p-4 shadow-lg">
          <p className="font-medium text-sm text-muted-foreground">
            {new Date(payload[0].payload.timestamp).toLocaleTimeString()}
          </p>
          <div className="mt-2 space-y-1">
            {payload.map((entry: any, index: number) => (
              <div key={`tooltip-${index}`} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div 
                    className="w-3 h-3 rounded-full mr-2" 
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-sm">{entry.name}:</span>
                </div>
                <span className="font-medium ml-2">
                  {entry.name === 'Threat %' 
                    ? `${entry.value.toFixed(1)}%`
                    : entry.value.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center">
            <Wifi className="h-5 w-5 mr-2 text-primary" />
            Network Traffic Analytics
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time monitoring and analysis of network traffic patterns
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {timeRanges.map((range) => (
            <Button
              key={range.value}
              variant={timeRange === range.value ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeRange(range.value)}
              className="h-8 px-3 text-xs"
            >
              {timeRange === range.value && (
                <Clock className="mr-1 h-3 w-3" />
              )}
              {range.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 rounded-full bg-blue-100 dark:bg-blue-900/50">
                <ArrowDown className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              </div>
              <CardTitle className="text-sm font-medium">Incoming Traffic</CardTitle>
            </div>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-[250px]">
                <p>Total incoming network traffic (download) in the selected time range. This includes all data received by your network.</p>
              </TooltipContent>
            </Tooltip>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline space-x-1">
              <div className="text-2xl font-bold">
                {totalIncoming >= 1000 ? `${(totalIncoming / 1000).toFixed(1)}` : totalIncoming}
              </div>
              <span className="text-sm text-muted-foreground">
                {totalIncoming >= 1000 ? 'GB' : 'MB'}
              </span>
            </div>
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              {incomingChange > 0 ? (
                <TrendingUp className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <TrendingDown className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={incomingChange > 0 ? 'text-green-500' : 'text-red-500'}>
                {Math.abs(incomingChange).toFixed(1)}%
              </span>
              <span className="ml-1">vs previous period</span>
            </div>
            <div className="mt-2">
              <Progress 
                value={Math.min(100, (latestData?.incoming || 0) / 1000)} 
                className="h-2 bg-gray-100 dark:bg-gray-800"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>0 MB</span>
                <span>1 GB</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 rounded-full bg-purple-100 dark:bg-purple-900/50">
                <ArrowUp className="h-4 w-4 text-purple-600 dark:text-purple-400" />
              </div>
              <CardTitle className="text-sm font-medium">Outgoing Traffic</CardTitle>
            </div>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-[250px]">
                <p>Total outgoing network traffic (upload) in the selected time range. This includes all data sent from your network.</p>
              </TooltipContent>
            </Tooltip>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline space-x-1">
              <div className="text-2xl font-bold">
                {totalOutgoing >= 1000 ? `${(totalOutgoing / 1000).toFixed(1)}` : totalOutgoing}
              </div>
              <span className="text-sm text-muted-foreground">
                {totalOutgoing >= 1000 ? 'GB' : 'MB'}
              </span>
            </div>
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              {outgoingChange > 0 ? (
                <TrendingUp className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <TrendingDown className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={outgoingChange > 0 ? 'text-green-500' : 'text-red-500'}>
                {Math.abs(outgoingChange).toFixed(1)}%
              </span>
              <span className="ml-1">vs previous period</span>
            </div>
            <div className="mt-2">
              <Progress 
                value={Math.min(100, (latestData?.outgoing || 0) / 500)} 
                className="h-2 bg-gray-100 dark:bg-gray-800"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>0 MB</span>
                <span>500 MB</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 rounded-full bg-red-100 dark:bg-red-900/50">
                <ShieldCheck className="h-4 w-4 text-red-600 dark:text-red-400" />
              </div>
              <CardTitle className="text-sm font-medium">Threats Blocked</CardTitle>
            </div>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-[250px]">
                <p>Total number of threats detected and blocked in the selected time range.</p>
              </TooltipContent>
            </Tooltip>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalThreats}</div>
            <span className="text-sm text-muted-foreground">threats</span>
            <p className="text-xs text-muted-foreground mt-1">
              ~{avgThreatsPerHour.toFixed(1)} threats per hour
            </p>
            <div className="mt-2">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>Threat Level</span>
                <span className={totalThreats > 50 ? 'text-red-500 font-medium' : totalThreats > 20 ? 'text-amber-500' : 'text-green-500'}>
                  {totalThreats > 50 ? 'High' : totalThreats > 20 ? 'Medium' : 'Low'}
                </span>
              </div>
              <Progress 
                value={Math.min(100, (totalThreats / 100) * 100)} 
                className="h-2 bg-gray-100 dark:bg-gray-800"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <Badge variant="secondary" className="h-4 w-4 p-0" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">99.9%</div>
            <p className="text-xs text-muted-foreground">
              +0.1% from last hour
            </p>
            <div className="mt-2">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>System Health</span>
                <span className="text-green-500 font-medium">Excellent</span>
              </div>
              <Progress 
                value={99.9} 
                className="h-2 bg-gray-100 dark:bg-gray-800"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="traffic">Traffic Analysis</TabsTrigger>
          <TabsTrigger value="protocols">Protocols</TabsTrigger>
          <TabsTrigger value="threats">Threats</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Traffic Overview</CardTitle>
                  <CardDescription>Real-time network traffic visualization</CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm" className="h-8">
                    <Clock className="mr-2 h-3.5 w-3.5" />
                    Live
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trafficChartData}>
                  <defs>
                    <linearGradient id="colorIncoming" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.incoming} stopOpacity={0.8} />
                      <stop offset="95%" stopColor={COLORS.incoming} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorOutgoing" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.outgoing} stopOpacity={0.8} />
                      <stop offset="95%" stopColor={COLORS.outgoing} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="time" 
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => value >= 1000 ? `${value / 1000}k` : value}
                  />
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <RechartsTooltip 
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-background p-4 border rounded-lg shadow-lg">
                            <p className="text-sm text-muted-foreground">
                              {payload[0].payload.time}
                            </p>
                            <div className="mt-2 space-y-1">
                              {payload.map((entry, index) => (
                                <div key={`tooltip-${index}`} className="flex items-center">
                                  <div 
                                    className="w-3 h-3 rounded-full mr-2" 
                                    style={{ backgroundColor: entry.color }}
                                  />
                                  <span className="text-sm">
                                    {entry.name}: {entry.value}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="incoming"
                    stroke={COLORS.incoming}
                    fillOpacity={1}
                    fill="url(#colorIncoming)"
                    name="Incoming"
                  />
                  <Area
                    type="monotone"
                    dataKey="outgoing"
                    stroke={COLORS.outgoing}
                    fillOpacity={1}
                    fill="url(#colorOutgoing)"
                    name="Outgoing"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="traffic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Traffic Distribution</CardTitle>
              <CardDescription>Breakdown of incoming vs outgoing traffic</CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-full">
                <div className="flex flex-col">
                  <div className="text-lg font-medium mb-4">Traffic Volume</div>
                  <div className="flex-1">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Incoming', value: totalIncoming, color: COLORS.incoming },
                            { name: 'Outgoing', value: totalOutgoing, color: COLORS.outgoing },
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={true}
                          label={renderCustomizedLabel}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {[
                            { name: 'Incoming', value: totalIncoming, color: COLORS.incoming },
                            { name: 'Outgoing', value: totalOutgoing, color: COLORS.outgoing },
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <RechartsTooltip 
                          formatter={(value, name) => [value, name]}
                        />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div className="space-y-6">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Incoming Traffic</span>
                      <span className="text-sm">
                        {totalIncoming >= 1000 ? `${(totalIncoming / 1000).toFixed(1)}k` : totalIncoming}
                        <span className="text-muted-foreground"> packets</span>
                      </span>
                    </div>
                    <Progress 
                      value={(totalIncoming / (totalIncoming + totalOutgoing || 1)) * 100} 
                      className="h-2" 
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Outgoing Traffic</span>
                      <span className="text-sm">
                        {totalOutgoing >= 1000 ? `${(totalOutgoing / 1000).toFixed(1)}k` : totalOutgoing}
                        <span className="text-muted-foreground"> packets</span>
                      </span>
                    </div>
                    <Progress 
                      value={(totalOutgoing / (totalIncoming + totalOutgoing || 1)) * 100} 
                      className="h-2" 
                    />
                  </div>
                  <div className="pt-4 border-t">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Total Traffic</span>
                      <span className="text-sm font-medium">
                        {totalIncoming + totalOutgoing >= 1000 
                          ? `${((totalIncoming + totalOutgoing) / 1000).toFixed(1)}k` 
                          : totalIncoming + totalOutgoing}
                        <span className="text-muted-foreground"> packets</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="protocols">
          <Card>
            <CardHeader>
              <CardTitle>Protocol Distribution</CardTitle>
              <CardDescription>Breakdown of network protocols in use</CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-full">
                <div className="flex flex-col">
                  <div className="text-lg font-medium mb-4">Protocols</div>
                  <div className="flex-1">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={protocolData}
                          cx="50%"
                          cy="50%"
                          labelLine={true}
                          label={renderCustomizedLabel}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {protocolData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <RechartsTooltip 
                          formatter={(value: any, name: any) => [value, name]}
                        />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="text-lg font-medium mb-2">Protocol Usage</div>
                  {protocolData.map((protocol) => (
                    <div key={protocol.name} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div 
                            className="w-3 h-3 rounded-full mr-2" 
                            style={{ backgroundColor: protocol.color }}
                          />
                          <span className="text-sm">{protocol.name}</span>
                        </div>
                        <span className="text-sm font-medium">
                          {protocol.value} <span className="text-muted-foreground">packets</span>
                        </span>
                      </div>
                      <Progress 
                        value={(protocol.value / protocolData.reduce((sum, p) => sum + p.value, 1)) * 100} 
                        className="h-2"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="threats">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Threat Analysis</CardTitle>
                  <CardDescription>Breakdown of detected threats</CardDescription>
                </div>
                <Badge variant="destructive" className="px-3 py-1">
                  <AlertTriangle className="h-4 w-4 mr-1" />
                  {totalThreats} Threats Detected
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <div className="text-lg font-medium">Threat Types</div>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={threatData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <RechartsTooltip />
                        <Bar dataKey="value" name="Threats">
                          {threatData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div className="space-y-6">
                  <div>
                    <div className="text-lg font-medium mb-4">Threat Distribution</div>
                    <div className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={threatData}
                            cx="50%"
                            cy="50%"
                            labelLine={true}
                            label={renderCustomizedLabel}
                            outerRadius={60}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {threatData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <RechartsTooltip formatter={(value: any, name: any) => [value, name]} />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};


