import { format, formatDistanceToNow } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AlertTriangle, Shield, Info, Search, Filter, X, Clock, Check, Ban } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useState, useMemo } from 'react';
import { blockIP } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export type AlertType = 'threat' | 'warning' | 'info';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  timestamp: string;
  source: string;
  acknowledged?: boolean;
}

interface AlertsTableProps {
  alerts: Alert[];
  maxItems?: number;
}

const severityOrder: Record<AlertSeverity, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1
};

const typeIcons = {
  threat: <AlertTriangle className="h-4 w-4 text-red-500" />,
  warning: <Shield className="h-4 w-4 text-yellow-500" />,
  info: <Info className="h-4 w-4 text-blue-500" />,
};

const severityBadges: Record<AlertSeverity, { label: string; className: string }> = {
  critical: { label: 'Critical', className: 'bg-red-500/15 text-red-500 hover:bg-red-500/20' },
  high: { label: 'High', className: 'bg-orange-500/15 text-orange-500 hover:bg-orange-500/20' },
  medium: { label: 'Medium', className: 'bg-yellow-500/15 text-yellow-500 hover:bg-yellow-500/20' },
  low: { label: 'Low', className: 'bg-blue-500/15 text-blue-500 hover:bg-blue-500/20' },
};

const formatRelativeTime = (dateString: string) => {
  const date = new Date(dateString);
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:underline cursor-help">
          <Clock className="h-3.5 w-3.5" />
          {formatDistanceToNow(date, { addSuffix: true })}
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <p>{format(date, 'PPpp')}</p>
      </TooltipContent>
    </Tooltip>
  );
};

export function AlertsTable({ alerts, maxItems = 20 }: AlertsTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<AlertType | 'all'>('all');
  const [acknowledgedFilter, setAcknowledgedFilter] = useState<boolean | 'all'>('all');
  const { toast } = useToast();

  const filteredAlerts = useMemo(() => {
    return alerts
      .filter(alert => {
        const matchesSearch = alert.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
          alert.source.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter;
        const matchesType = typeFilter === 'all' || alert.type === typeFilter;
        const matchesAcknowledged = acknowledgedFilter === 'all' ||
          (acknowledgedFilter === true ? alert.acknowledged : !alert.acknowledged);

        return matchesSearch && matchesSeverity && matchesType && matchesAcknowledged;
      })
      .sort((a, b) => {
        // Sort by severity first (critical to low)
        if (severityOrder[a.severity] !== severityOrder[b.severity]) {
          return severityOrder[b.severity] - severityOrder[a.severity];
        }
        // Then by timestamp (newest first)
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      })
      .slice(0, maxItems);
  }, [alerts, searchQuery, severityFilter, typeFilter, acknowledgedFilter, maxItems]);

  const handleAcknowledge = (id: string) => {
    // In a real app, this would update the alert in the backend
    console.log(`Acknowledged alert ${id}`);
    toast({
      title: "Alert Acknowledged",
      description: "The alert has been marked as acknowledged.",
    });
  };

  const handleBlockIP = async (ip: string) => {
    try {
      await blockIP(ip);
      toast({
        title: "IP Blocked",
        description: `Successfully blocked IP address: ${ip}`,
      });
    } catch (error) {
      toast({
        title: "Block Failed",
        description: `Failed to block IP: ${ip}. It may be whitelisted or system error.`,
        variant: "destructive",
      });
      console.error("Error blocking IP:", error);
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSeverityFilter('all');
    setTypeFilter('all');
    setAcknowledgedFilter('all');
  };

  const hasActiveFilters = searchQuery || severityFilter !== 'all' || typeFilter !== 'all' || acknowledgedFilter !== 'all';

  if (alerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Security Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Shield className="h-16 w-16 mb-4 opacity-20" />
            <p className="text-lg font-medium">No alerts detected</p>
            <p className="text-sm">Your network is currently secure</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <TooltipProvider>
      <Card className="overflow-hidden">
        <CardHeader className="border-b">
          <div className="flex flex-col space-y-2 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
            <div>
              <CardTitle>Security Alerts</CardTitle>
              <p className="text-sm text-muted-foreground">
                Showing {filteredAlerts.length} of {alerts.length} total alerts
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" className="h-8">
                <Filter className="mr-2 h-3.5 w-3.5" />
                <span>Filter</span>
              </Button>
              <Button variant="outline" size="sm" className="h-8">
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search alerts..."
              className="w-full bg-background pl-8"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-2 top-0.5 h-8 px-2 text-xs text-muted-foreground"
                onClick={clearFilters}
              >
                Clear filters
                <X className="ml-1 h-3.5 w-3.5" />
              </Button>
            )}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-muted-foreground">Severity:</span>
              <div className="flex space-x-1">
                {(['all', 'critical', 'high', 'medium', 'low'] as const).map((sev) => {
                  const isActive = severityFilter === sev;
                  return (
                    <Button
                      key={sev}
                      variant={isActive ? 'secondary' : 'ghost'}
                      size="sm"
                      className={`h-7 px-2 text-xs ${isActive ? 'bg-accent' : 'opacity-70'}`}
                      onClick={() => setSeverityFilter(sev === 'all' ? 'all' : sev)}
                    >
                      {sev === 'all' ? 'All' : sev.charAt(0).toUpperCase() + sev.slice(1)}
                      {sev !== 'all' && (
                        <span className="ml-1 rounded-full bg-foreground/10 px-1.5 py-0.5 text-xs">
                          {alerts.filter(a => a.severity === sev).length}
                        </span>
                      )}
                    </Button>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-xs text-muted-foreground">Type:</span>
              <div className="flex space-x-1">
                {['all', 'threat', 'warning', 'info'].map((type) => {
                  const isActive = typeFilter === type;
                  return (
                    <Button
                      key={type}
                      variant={isActive ? 'secondary' : 'ghost'}
                      size="sm"
                      className={`h-7 px-2 text-xs ${isActive ? 'bg-accent' : 'opacity-70'}`}
                      onClick={() => setTypeFilter(type as AlertType | 'all')}
                    >
                      {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
                    </Button>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-xs text-muted-foreground">Status:</span>
              <div className="flex space-x-1">
                {['all', true, false].map((status) => {
                  const label = status === 'all' ? 'All' : status ? 'Acknowledged' : 'New';
                  const isActive = acknowledgedFilter === status;
                  return (
                    <Button
                      key={String(status)}
                      variant={isActive ? 'secondary' : 'ghost'}
                      size="sm"
                      className={`h-7 px-2 text-xs ${isActive ? 'bg-accent' : 'opacity-70'}`}
                      onClick={() => setAcknowledgedFilter(status as boolean | 'all')}
                    >
                      {label}
                    </Button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <CardContent className="p-0">
          <div className="relative overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px] px-3">Type</TableHead>
                  <TableHead className="w-[100px]">Severity</TableHead>
                  <TableHead>Message</TableHead>
                  <TableHead className="w-[120px]">Source</TableHead>
                  <TableHead className="w-[140px] text-right">Time</TableHead>
                  <TableHead className="w-[40px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAlerts.length > 0 ? (
                  filteredAlerts.map((alert) => (
                    <TableRow
                      key={alert.id}
                      className={cn(
                        'group hover:bg-accent/50 transition-colors',
                        alert.acknowledged && 'opacity-70 hover:opacity-100'
                      )}
                    >
                      <TableCell className="px-3">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="flex items-center justify-center">
                              {typeIcons[alert.type]}
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{alert.type.charAt(0).toUpperCase() + alert.type.slice(1)}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn(
                            'whitespace-nowrap',
                            severityBadges[alert.severity].className
                          )}
                        >
                          {alert.severity.charAt(0).toUpperCase() + alert.severity.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[300px]">
                        <div className="flex items-center">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <p className="truncate font-medium">
                                {alert.message}
                              </p>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-[300px]">
                              <p className="break-words">{alert.message}</p>
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {alert.source}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {formatRelativeTime(alert.timestamp)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end space-x-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-red-500 opacity-0 group-hover:opacity-100 hover:text-red-700 hover:bg-red-50"
                                onClick={() => handleBlockIP(alert.source)}
                              >
                                <Ban className="h-4 w-4" />
                                <span className="sr-only">Block IP</span>
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Block IP Address</p>
                            </TooltipContent>
                          </Tooltip>

                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 opacity-0 group-hover:opacity-100"
                                onClick={() => handleAcknowledge(alert.id)}
                              >
                                <Check className="h-4 w-4" />
                                <span className="sr-only">Acknowledge</span>
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Acknowledge alert</p>
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      <div className="flex flex-col items-center justify-center py-6">
                        <Search className="h-10 w-10 text-muted-foreground mb-2" />
                        <p className="text-sm font-medium">No alerts found</p>
                        <p className="text-xs text-muted-foreground">
                          Try adjusting your search or filter criteria
                        </p>
                        {hasActiveFilters && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="mt-2 h-8 text-xs"
                            onClick={clearFilters}
                          >
                            Clear all filters
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>

        {filteredAlerts.length > 0 && (
          <div className="border-t px-4 py-2">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing <span className="font-medium">{filteredAlerts.length}</span> of{' '}
                <span className="font-medium">{alerts.length}</span> alerts
              </p>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" className="h-8">
                  Previous
                </Button>
                <Button variant="outline" size="sm" className="h-8">
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </TooltipProvider>
  );
}
