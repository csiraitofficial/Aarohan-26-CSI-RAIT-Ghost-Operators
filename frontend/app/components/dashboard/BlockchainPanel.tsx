"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fetchBlockchainStatus } from "@/lib/api";
import { Link, ExternalLink, Globe, Shield, Database, Activity, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export function BlockchainPanel() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadData = async () => {
        try {
            setLoading(true);
            const res = await fetchBlockchainStatus();
            setData(res);
        } catch (err: any) {
            setError(err.message || "Failed to load blockchain data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading && !data) {
        return (
            <div className="flex items-center justify-center p-12">
                <Activity className="h-8 w-8 animate-spin text-primary mr-3" />
                <span className="text-lg font-medium">Querying Distributed Ledger...</span>
            </div>
        );
    }

    if (error && !data) {
        return (
            <Card className="border-destructive/50 bg-destructive/5">
                <CardContent className="p-6">
                    <div className="flex items-center gap-3 text-destructive">
                        <Shield className="h-6 w-6" />
                        <p className="font-semibold">{error}</p>
                    </div>
                    <Button onClick={loadData} variant="outline" className="mt-4">Retry Connection</Button>
                </CardContent>
            </Card>
        );
    }

    const getExplorerUrl = (txHash: string) => {
        return `https://amoy.polygonscan.com/tx/${txHash}`;
    };

    const getAddressUrl = (address: string) => {
        return `https://amoy.polygonscan.com/address/${address}`;
    };

    return (
        <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <Card className="relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Globe className="h-24 w-24" />
                    </div>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Node Connection</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-2xl font-bold">{data?.network || "Unknown"}</p>
                                <p className="text-xs text-muted-foreground mt-1">Status:
                                    <span className={data?.is_connected ? "text-green-500 font-bold ml-1" : "text-red-500 font-bold ml-1"}>
                                        {data?.is_connected ? "Connected" : "Disconnected"}
                                    </span>
                                </p>
                            </div>
                            <Badge variant={data?.is_connected ? "secondary" : "destructive"} className="h-8">
                                {data?.is_connected ? "Active" : "Offline"}
                            </Badge>
                        </div>
                        <p className="text-[10px] font-mono mt-4 text-muted-foreground truncate">{data?.rpc_url}</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Smart Contracts</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-[10px] uppercase font-bold text-muted-foreground">Threat Logger</label>
                            <div className="flex items-center justify-between group">
                                <code className="text-[11px] bg-muted p-1 rounded font-mono truncate mr-2 flex-1">
                                    {data?.contract_address || "Not Configured"}
                                </code>
                                {data?.contract_address && (
                                    <a href={getAddressUrl(data.contract_address)} target="_blank" rel="noopener noreferrer">
                                        <ExternalLink className="h-3.5 w-3.5 text-primary hover:scale-110 transition-transform" />
                                    </a>
                                )}
                            </div>
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] uppercase font-bold text-muted-foreground">Global Consensus</label>
                            <div className="flex items-center justify-between group">
                                <code className="text-[11px] bg-muted p-1 rounded font-mono truncate mr-2 flex-1">
                                    {data?.consensus_address || "Not Configured"}
                                </code>
                                {data?.consensus_address && (
                                    <a href={getAddressUrl(data.consensus_address)} target="_blank" rel="noopener noreferrer">
                                        <ExternalLink className="h-3.5 w-3.5 text-primary hover:scale-110 transition-transform" />
                                    </a>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Immutable Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex flex-col gap-2">
                            <div className="flex items-center justify-between py-1 border-b border-dashed">
                                <span className="text-xs text-muted-foreground">Reporting Enabled</span>
                                <Badge variant={data?.enabled ? "default" : "outline"}>{data?.enabled ? "YES" : "NO"}</Badge>
                            </div>
                            <div className="flex items-center justify-between py-1 border-b border-dashed">
                                <span className="text-xs text-muted-foreground">Consensus Mode</span>
                                <span className="text-xs font-bold">PoA / Delegated</span>
                            </div>
                            <div className="flex items-center justify-between py-1">
                                <span className="text-xs text-muted-foreground">System Reputation</span>
                                <span className="text-xs text-green-500 font-bold">Excellent (+4.2)</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="flex items-center gap-2">
                                <Database className="h-5 w-5 text-primary" />
                                Recent Blockchain Transactions
                            </CardTitle>
                            <CardDescription>View cryptographically signed records of security events</CardDescription>
                        </div>
                        <Button variant="outline" size="sm" onClick={loadData}>
                            <Activity className="h-3.5 w-3.5 mr-2" />
                            Refresh Ledger
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    {(!data?.recent_transactions || data.recent_transactions.length === 0) ? (
                        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                            <Clock className="h-12 w-12 mb-4 opacity-10" />
                            <p>No transactions recorded in this session</p>
                            <p className="text-xs">Blockchain reporting only triggers on High/Critical threats</p>
                        </div>
                    ) : (
                        <div className="relative overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Execution Time</TableHead>
                                        <TableHead>Function Call</TableHead>
                                        <TableHead>Transaction Hash</TableHead>
                                        <TableHead className="text-right">Explorer</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {data.recent_transactions.map((tx: any, idx: number) => (
                                        <TableRow key={idx}>
                                            <TableCell className="text-xs font-medium">
                                                {formatDistanceToNow(new Date(tx.timestamp), { addSuffix: true })}
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="secondary" className="font-mono text-[10px]">
                                                    {tx.type || "storeAlert"}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="max-w-[200px]">
                                                <code className="text-[11px] text-muted-foreground truncate block">
                                                    {tx.hash}
                                                </code>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <a
                                                    href={getExplorerUrl(tx.hash)}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-primary hover:underline flex items-center justify-end gap-1 text-xs"
                                                >
                                                    View <ExternalLink className="h-3 w-3" />
                                                </a>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
