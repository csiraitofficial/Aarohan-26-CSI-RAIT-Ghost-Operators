import { useState, useEffect } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { format } from 'date-fns';

interface OverviewChartProps {
  data: Array<{
    timestamp: string;
    incoming: number;
    outgoing: number;
    threats: number;
  }>;
}

export function OverviewChart({ data }: OverviewChartProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Network Traffic Overview</CardTitle>
        </CardHeader>
        <CardContent className="h-80 flex items-center justify-center">
          <div className="text-muted-foreground">Loading chart...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Network Traffic Overview</CardTitle>
      </CardHeader>
      <CardContent className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) => {
                try {
                  return format(new Date(value), 'HH:mm');
                } catch (e) {
                  return '';
                }
              }}
            />
            <YAxis />
            <Tooltip
              labelFormatter={(value) => {
                try {
                  return format(new Date(value), 'PPpp');
                } catch (e) {
                  return '';
                }
              }}
              formatter={(value, name) => [value, name === 'incoming' ? 'Incoming' : name === 'outgoing' ? 'Outgoing' : 'Threats']}
            />
            <Area
              type="monotone"
              dataKey="incoming"
              stackId="1"
              stroke="#8884d8"
              fill="#8884d8"
              fillOpacity={0.3}
            />
            <Area
              type="monotone"
              dataKey="outgoing"
              stackId="1"
              stroke="#82ca9d"
              fill="#82ca9d"
              fillOpacity={0.3}
            />
            <Area
              type="monotone"
              dataKey="threats"
              stackId="1"
              stroke="#ff4d4f"
              fill="#ff4d4f"
              fillOpacity={0.3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
