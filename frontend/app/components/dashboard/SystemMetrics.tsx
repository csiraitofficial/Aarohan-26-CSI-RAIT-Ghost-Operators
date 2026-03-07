import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Activity, HardDrive, Cpu, Wifi, AlertTriangle, HelpCircle, TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SystemMetricsData {
  cpu: number;
  memory: number;
  disk: number;
  networkIn: number;
  networkOut: number;
}

interface SystemMetricsProps {
  metrics: SystemMetricsData;
}

const MetricCard = ({
  title,
  value,
  icon: Icon,
  thresholds = { warning: 70, critical: 90 },
  format = (v: number) => `${Math.round(v)}%`,
  description,
  trend,
}: {
  title: string;
  value: number;
  icon: React.ElementType;
  thresholds?: { warning: number; critical: number };
  format?: (value: number) => string;
  description?: string;
  trend?: 'up' | 'down' | 'stable';
}) => {
  const statusColor = (() => {
    if (value >= thresholds.critical) return 'text-red-500';
    if (value >= thresholds.warning) return 'text-yellow-500';
    return 'text-green-500';
  })();

  const statusBadge = (() => {
    if (value >= thresholds.critical) return <Badge variant="destructive">Critical</Badge>;
    if (value >= thresholds.warning) return <Badge variant="secondary">Warning</Badge>;
    return <Badge variant="outline" className="text-green-600">Normal</Badge>;
  })();

  const trendIcon = {
    up: <TrendingUp className="h-4 w-4 text-red-500" />,
    down: <TrendingDown className="h-4 w-4 text-green-500" />,
    stable: <Activity className="h-4 w-4 text-blue-500" />,
  }[trend || 'stable'];

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
            {description && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent className="max-w-[200px]">
                  <p className="text-xs">{description}</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
          <div className="text-2xl font-bold">{format(value)}</div>
        </div>
        <div className={cn("p-2 rounded-full", {
          'bg-red-500/10': statusColor === 'text-red-500',
          'bg-yellow-500/10': statusColor === 'text-yellow-500',
          'bg-green-500/10': statusColor === 'text-green-500',
        })}>
          <Icon className={cn("h-5 w-5", statusColor)} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between mt-2">
          <Progress value={value} className="h-2 flex-1 mr-2" />
          {statusBadge}
        </div>
        {trend && (
          <div className="flex items-center mt-1 text-xs text-muted-foreground">
            {trendIcon}
            <span className="ml-1">
              {trend === 'up' ? 'Increasing' : trend === 'down' ? 'Decreasing' : 'Stable'}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export function SystemMetrics({ metrics }: SystemMetricsProps) {

  return (
    <TooltipProvider>
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <MetricCard
            title="CPU Usage"
            value={metrics.cpu}
            icon={Cpu}
            thresholds={{ warning: 70, critical: 90 }}
            description="CPU utilization across all cores"
            trend={metrics.cpu > 80 ? 'up' : metrics.cpu < 30 ? 'down' : 'stable'}
          />
          
          <MetricCard
            title="Memory Usage"
            value={metrics.memory}
            icon={Activity}
            thresholds={{ warning: 80, critical: 95 }}
            description="Physical memory usage"
            trend={metrics.memory > 85 ? 'up' : metrics.memory < 50 ? 'down' : 'stable'}
          />
          
          <MetricCard
            title="Disk Usage"
            value={metrics.disk}
            icon={HardDrive}
            thresholds={{ warning: 85, critical: 95 }}
            description="Root filesystem usage"
            trend={metrics.disk > 90 ? 'up' : 'stable'}
          />
        </div>

        <Card className="overflow-hidden">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Network Performance</CardTitle>
                <CardDescription>Real-time network interface statistics</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span>Active</span>
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Wifi className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">Incoming Traffic</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono">
                      {Math.round(metrics.networkIn / 1000)}k
                    </span>
                    <span className="text-xs text-muted-foreground">packets/s</span>
                  </div>
                </div>
                <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div 
                    className="h-full bg-blue-500 transition-all duration-300"
                    style={{ width: `${Math.min(metrics.networkIn / 1000, 100)}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>0</span>
                  <span>Peak: {Math.round(metrics.networkIn * 1.2 / 1000)}k</span>
                  <span>100k</span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Wifi className="h-4 w-4 text-purple-500" />
                    <span className="text-sm font-medium">Outgoing Traffic</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono">
                      {Math.round(metrics.networkOut / 1000)}k
                    </span>
                    <span className="text-xs text-muted-foreground">packets/s</span>
                  </div>
                </div>
                <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div 
                    className="h-full bg-purple-500 transition-all duration-300"
                    style={{ width: `${Math.min(metrics.networkOut / 1000, 100)}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>0</span>
                  <span>Peak: {Math.round(metrics.networkOut * 1.2 / 1000)}k</span>
                  <span>100k</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Overall system performance indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-500">98.5%</div>
                <p className="text-xs text-muted-foreground">System Uptime</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-500">1.2ms</div>
                <p className="text-xs text-muted-foreground">Avg Response Time</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-500">99.9%</div>
                <p className="text-xs text-muted-foreground">Detection Accuracy</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  );
}
