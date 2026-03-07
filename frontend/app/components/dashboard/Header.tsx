'use client';

import { Bell, Search, Menu, Network } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ThemeToggle } from '@/components/theme-toggle';
import { Badge } from '@/components/ui/badge';
import { useNIDSData } from '@/lib/hooks/useNIDSData';

export function Header() {
  const { alerts } = useNIDSData();
  const criticalAlerts = alerts.filter(alert =>
    alert.severity === 'critical' || alert.severity === 'high'
  ).length;

  return (
    <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 transition-colors duration-200">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="md:hidden hover:bg-accent/50">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle sidebar</span>
        </Button>
        <div className="hidden md:flex items-center gap-2">
          <Network className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-semibold">NIDS Dashboard</h1>
        </div>
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search alerts, traffic, or devices..."
            className="w-full rounded-lg bg-background pl-9 pr-4 py-2 transition-all duration-200 focus:ring-2 focus:ring-primary/50"
          />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="relative hover:bg-accent/50 transition-colors"
          onClick={() => {
            // TODO: Implement notifications panel
            console.log('Notifications clicked');
          }}
        >
          <Bell className="h-5 w-5" />
          {criticalAlerts > 0 && (
            <Badge
              variant="destructive"
              className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 flex items-center justify-center"
            >
              {criticalAlerts}
            </Badge>
          )}
          <span className="sr-only">View notifications</span>
        </Button>
        <ThemeToggle />
      </div>
    </header>
  );
}
