import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc";
import { Plus, Search, TrendingUp, TrendingDown, ArrowUpDown } from "lucide-react";
import { useState } from "react";
import { useLocation } from "wouter";

export default function Portfolios() {
  const [, setLocation] = useLocation();
  const [searchQuery, setSearchQuery] = useState("");
  
  // Fetch portfolios using tRPC
  const { data: portfolios, isLoading } = trpc.portfolio.list.useQuery();

  // Filter portfolios based on search
  const filteredPortfolios = portfolios?.filter(portfolio =>
    portfolio.investorName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    portfolio.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate summary stats
  const totalValue = portfolios?.reduce((sum, p) => sum + Number(p.value), 0) || 0;
  const activeCount = portfolios?.filter(p => p.status === 'active').length || 0;
  const avgReturn = portfolios?.reduce((sum, p) => sum + Number(p.return30d || 0), 0) / (portfolios?.length || 1);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolios</h1>
          <p className="text-muted-foreground mt-2">
            Manage investment portfolios and monitor performance
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Portfolio
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total AUM</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalValue)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Across {portfolios?.length || 0} portfolios
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Portfolios</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCount}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Currently managed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Return Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercent(avgReturn)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Year to date
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Portfolio List</CardTitle>
          <CardDescription>
            View and manage all investment portfolios
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search portfolios..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">Loading portfolios...</div>
            </div>
          ) : filteredPortfolios && filteredPortfolios.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Total Value</TableHead>
                  <TableHead className="text-right">Return Rate</TableHead>
                  <TableHead className="text-right">Risk Level</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPortfolios.map((portfolio) => (
                  <TableRow 
                    key={portfolio.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => setLocation(`/portfolios/${portfolio.id}`)}
                  >
                    <TableCell>
                      <div>
                        <div className="font-medium">{portfolio.investorName}</div>
                        <div className="text-sm text-muted-foreground">
                          {portfolio.id}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{portfolio.agent}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge 
                        variant={portfolio.status === 'active' ? 'default' : 'secondary'}
                      >
                        {portfolio.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(Number(portfolio.value))}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        {Number(portfolio.return30d || 0) >= 0 ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-600" />
                        )}
                        <span className={Number(portfolio.return30d || 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatPercent(Number(portfolio.return30d || 0))}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge 
                        variant="outline"
                        className={
                          Number(portfolio.volatility || 0) > 0.3 ? 'border-red-500 text-red-600' :
                          Number(portfolio.volatility || 0) > 0.15 ? 'border-yellow-500 text-yellow-600' :
                          'border-green-500 text-green-600'
                        }
                      >
                        {Number(portfolio.volatility || 0) > 0.3 ? 'High' : Number(portfolio.volatility || 0) > 0.15 ? 'Medium' : 'Low'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setLocation(`/portfolios/${portfolio.id}`);
                        }}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <ArrowUpDown className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No portfolios found</h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchQuery ? 'Try adjusting your search query' : 'Get started by creating your first portfolio'}
              </p>
              {!searchQuery && (
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Portfolio
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
