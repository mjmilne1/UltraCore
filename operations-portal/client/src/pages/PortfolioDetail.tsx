import { useRoute, useLocation } from "wouter";
import { ArrowLeft, TrendingUp, TrendingDown, Activity, DollarSign, Target, AlertTriangle } from "lucide-react";
import { useEffect, useRef } from "react";
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { trpc } from "@/lib/trpc";

export default function PortfolioDetail() {
  const [, params] = useRoute("/portfolios/:id");
  const [, setLocation] = useLocation();
  const portfolioId = params?.id || "";

  // Fetch portfolio data
  const { data: portfolio, isLoading: portfolioLoading } = trpc.portfolio.getById.useQuery({ id: portfolioId });
  const { data: holdings, isLoading: holdingsLoading } = trpc.portfolio.getHoldings.useQuery({ portfolioId });
  const { data: agent } = trpc.rlAgent.getByName.useQuery(
    { name: portfolio?.agent || "alpha" },
    { enabled: !!portfolio }
  );

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value / 100);
  };

  // Chart ref
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstanceRef = useRef<Chart | null>(null);

  // Generate mock historical data based on current portfolio values
  useEffect(() => {
    if (!portfolio || !chartRef.current) return;

    const currentValue = Number(portfolio.value);
    const initialValue = Number(portfolio.initialInvestment);
    const return30d = Number(portfolio.return30d || 0) / 100;

    // Generate 30 days of historical data
    const days = 30;
    const labels: string[] = [];
    const values: number[] = [];

    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));

      // Simulate realistic price movement
      const progress = (days - i) / days;
      const randomWalk = (Math.random() - 0.5) * 0.02; // ±2% daily volatility
      const trendValue = initialValue * (1 + return30d * progress);
      const dailyValue = trendValue * (1 + randomWalk);
      values.push(dailyValue);
    }

    // Ensure last value matches current value
    values[values.length - 1] = currentValue;

    // Destroy existing chart
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }

    // Create new chart
    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    chartInstanceRef.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Portfolio Value',
            data: values,
            borderColor: return30d >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
            backgroundColor: return30d >= 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: (context: any) => {
                return `Value: ${formatCurrency(context.parsed.y)}`;
              },
            },
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              maxTicksLimit: 8,
            },
          },
          y: {
            grid: {
              color: 'rgba(0, 0, 0, 0.05)',
            },
            ticks: {
              callback: (value: any) => {
                return formatCurrency(value as number);
              },
            },
          },
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false,
        },
      },
    });

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, [portfolio]);

  if (portfolioLoading) {
    return (
      <div className="container py-8">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="icon" onClick={() => setLocation("/portfolios")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        </div>
        <div className="grid gap-6 md:grid-cols-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-3">
                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              </CardHeader>
              <CardContent>
                <div className="h-8 w-32 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="container py-8">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="icon" onClick={() => setLocation("/portfolios")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-bold">Portfolio Not Found</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">The portfolio you're looking for doesn't exist.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalHoldingsValue = holdings?.reduce((sum, h) => sum + Number(h.value), 0) || 0;

  return (
    <div className="container py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => setLocation("/portfolios")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{portfolio.investorName}</h1>
            <p className="text-muted-foreground">{portfolio.id}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={portfolio.status === 'active' ? 'default' : 'secondary'}>
            {portfolio.status}
          </Badge>
          <Badge variant="outline">{portfolio.agent}</Badge>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Portfolio Value
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(Number(portfolio.value))}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Initial: {formatCurrency(Number(portfolio.initialInvestment))}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              30-Day Return
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold flex items-center gap-2 ${Number(portfolio.return30d || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {Number(portfolio.return30d || 0) >= 0 ? (
                <TrendingUp className="h-5 w-5" />
              ) : (
                <TrendingDown className="h-5 w-5" />
              )}
              {formatPercent(Number(portfolio.return30d || 0))}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              1Y: {formatPercent(Number(portfolio.return1y || 0))}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Sharpe Ratio
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Number(portfolio.sharpeRatio || 0).toFixed(2)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Risk-adjusted return
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Volatility
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercent(Number(portfolio.volatility || 0))}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Max DD: {formatPercent(Number(portfolio.maxDrawdown || 0))}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Holdings Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Portfolio Holdings</CardTitle>
            <CardDescription>
              {holdings?.length || 0} positions • Total value: {formatCurrency(totalHoldingsValue)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {holdingsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-12 bg-muted animate-pulse rounded" />
                ))}
              </div>
            ) : holdings && holdings.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ticker</TableHead>
                    <TableHead className="text-right">Weight</TableHead>
                    <TableHead className="text-right">Value</TableHead>
                    <TableHead className="text-right">Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {holdings.map((holding) => (
                    <TableRow key={holding.id}>
                      <TableCell className="font-medium">{holding.ticker}</TableCell>
                      <TableCell className="text-right">
                        {formatPercent(Number(holding.weight) * 100)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(Number(holding.value))}
                      </TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">
                        {new Date(holding.updatedAt).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No holdings found
              </div>
            )}
          </CardContent>
        </Card>

        {/* RL Agent Info */}
        <Card>
          <CardHeader>
            <CardTitle>RL Agent</CardTitle>
            <CardDescription>
              Managing this portfolio
            </CardDescription>
          </CardHeader>
          <CardContent>
            {agent ? (
              <div className="space-y-4">
                <div>
                  <div className="text-lg font-semibold mb-1">{agent.displayName}</div>
                  <Badge variant="outline" className="mb-3">{agent.modelVersion}</Badge>
                  <p className="text-sm text-muted-foreground">{agent.objective}</p>
                </div>

                <div className="space-y-2 pt-4 border-t">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Status</span>
                    <Badge variant={agent.status === 'deployed' ? 'default' : 'secondary'}>
                      {agent.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Episodes Trained</span>
                    <span className="font-medium">{agent.episodesTrained.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Avg Reward</span>
                    <span className="font-medium">{Number(agent.avgReward).toFixed(2)}</span>
                  </div>
                  {agent.lastTrainedAt && (
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Last Trained</span>
                      <span className="font-medium">
                        {new Date(agent.lastTrainedAt).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                <Button className="w-full mt-4" variant="outline">
                  View Agent Details
                </Button>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Agent information unavailable</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Performance Chart Placeholder */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Performance History</CardTitle>
          <CardDescription>
            Portfolio value over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <canvas ref={chartRef} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
