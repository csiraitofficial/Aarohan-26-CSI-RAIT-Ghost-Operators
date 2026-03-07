'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { cn } from '@/lib/utils';
import { LayoutDashboard, Shield, Activity, Network, Settings, AlertTriangle, Link as LinkIcon } from 'lucide-react';

const navItems = [
  { name: 'Dashboard', href: '/?tab=overview', value: 'overview', icon: LayoutDashboard },
  { name: 'Threat Detection', href: '/?tab=detection', value: 'detection', icon: Shield },
  { name: 'Blockchain Security', href: '/?tab=blockchain', value: 'blockchain', icon: LinkIcon },
  { name: 'Network Traffic', href: '/?tab=traffic', value: 'traffic', icon: Network },
  { name: 'System Health', href: '/?tab=system', value: 'system', icon: Activity },
  { name: 'Alerts', href: '/?tab=alerts', value: 'alerts', icon: AlertTriangle },
  { name: 'Settings', href: '/?tab=settings', value: 'settings', icon: Settings },
];

export function Sidebar() {
  const searchParams = useSearchParams();
  const currentTab = searchParams.get('tab') || 'overview';

  return (
    <aside className="hidden w-64 border-r bg-background md:block">
      <div className="flex h-16 items-center border-b px-6">
        <h2 className="text-lg font-semibold">NIDS</h2>
      </div>
      <nav className="space-y-1 p-4">
        {navItems.map((item) => {
          const isActive = currentTab === item.value;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center rounded-lg px-4 py-3 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
