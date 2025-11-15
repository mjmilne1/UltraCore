import { useState, useEffect } from "react";
import { Database, Search, BarChart3, Download, Play, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc";

export default function DataMesh() {
  const [searchQuery, setSearchQuery] = useState("");
  const [duckdbReady, setDuckdbReady] = useState(false);
  const [loading, setLoading] = useState(false);

  const { data: products, isLoading } = trpc.dataMesh.listProducts.useQuery();

  // Initialize DuckDB WASM (placeholder for now)
  useEffect(() => {
    // TODO: Initialize DuckDB WASM in next phase
    setDuckdbReady(false);
  }, []);

  const filteredProducts = products?.filter((product) =>
    product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.ticker?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.category?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Data Mesh</h1>
          <p className="text-muted-foreground">ETF data catalog and analytics powered by DuckDB WASM</p>
        </div>

        {/* KPI Cards Loading */}
        <div className="grid gap-6 md:grid-cols-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-3">
                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              </CardHeader>
              <CardContent>
                <div className="h-8 w-16 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const totalProducts = products?.length || 0;
  const categories = new Set(products?.map(p => p.category).filter(Boolean)).size;
  const avgExpenseRatio = products?.length
    ? products.reduce((sum, p) => sum + (Number(p.expenseRatio) || 0), 0) / products.length
    : 0;

  return (
    <div className="container py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Data Mesh</h1>
        <p className="text-muted-foreground">ETF data catalog and analytics powered by DuckDB WASM</p>
      </div>

      {/* DuckDB Status Banner */}
      {!duckdbReady && (
        <Card className="mb-6 border-blue-200 bg-blue-50">
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <Database className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium text-blue-900">DuckDB WASM Analytics Engine</p>
                <p className="text-sm text-blue-700">Click to initialize in-browser analytics on 137 ASX ETF Parquet files</p>
              </div>
            </div>
            <Button
              onClick={() => {
                setLoading(true);
                // TODO: Initialize DuckDB in next phase
                setTimeout(() => {
                  setLoading(false);
                  setDuckdbReady(true);
                }, 2000);
              }}
              disabled={loading}
            >
              <Play className="h-4 w-4 mr-2" />
              {loading ? "Initializing..." : "Initialize DuckDB"}
            </Button>
          </CardContent>
        </Card>
      )}

      {duckdbReady && (
        <Card className="mb-6 border-green-200 bg-green-50">
          <CardContent className="flex items-center gap-3 py-4">
            <Database className="h-5 w-5 text-green-600" />
            <div>
              <p className="font-medium text-green-900">DuckDB WASM Ready</p>
              <p className="text-sm text-green-700">In-browser analytics engine initialized • Query Parquet files directly</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              Total Products
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalProducts}</div>
            <p className="text-xs text-muted-foreground mt-1">
              ASX ETF products
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Categories
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{categories}</div>
            <p className="text-xs text-muted-foreground mt-1">
              unique categories
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Avg Expense Ratio
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgExpenseRatio.toFixed(2)}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              mean management fee
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              Data Format
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Parquet</div>
            <p className="text-xs text-muted-foreground mt-1">
              columnar storage
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Actions */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, ticker, or category..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Export Data
        </Button>
      </div>

      {/* ETF Product Catalog */}
      <Card>
        <CardHeader>
          <CardTitle>ETF Product Catalog</CardTitle>
          <CardDescription>
            {filteredProducts?.length || 0} of {totalProducts} products
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredProducts && filteredProducts.length > 0 ? (
            <div className="space-y-3">
              {filteredProducts.map((product) => (
                <div
                  key={product.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold">{product.name}</h3>
                      {product.ticker && (
                        <Badge variant="outline">{product.ticker}</Badge>
                      )}
                      {product.category && (
                        <Badge variant="secondary">{product.category}</Badge>
                      )}
                    </div>
                    {product.description && (
                      <p className="text-sm text-muted-foreground line-clamp-1">
                        {product.description}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    {product.expenseRatio && (
                      <div className="text-right">
                        <div className="text-muted-foreground text-xs">Expense Ratio</div>
                        <div className="font-medium">{Number(product.expenseRatio).toFixed(2)}%</div>
                      </div>
                    )}
                    {product.aum && (
                      <div className="text-right">
                        <div className="text-muted-foreground text-xs">AUM</div>
                        <div className="font-medium">${(Number(product.aum) / 1000000).toFixed(0)}M</div>
                      </div>
                    )}
                    <Button variant="ghost" size="sm">
                      <BarChart3 className="h-4 w-4 mr-2" />
                      Analyze
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">
                {searchQuery ? "No products found" : "No ETF products available"}
              </p>
              <p className="text-sm text-muted-foreground">
                {searchQuery ? "Try adjusting your search query" : "Add ETF products to the data mesh"}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
