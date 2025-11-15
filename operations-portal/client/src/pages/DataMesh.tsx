import { useState } from "react";
import { Database, Search, BarChart3, Download, Play, AlertCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc";
import { useDuckDB } from "@/hooks/useDuckDB";
import { toast } from "sonner";

export default function DataMesh() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [queryResult, setQueryResult] = useState<any[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const { data: products, isLoading } = trpc.dataMesh.listProducts.useQuery();
  const { isInitialized, isInitializing, error, initialize, loadParquetFile, query } = useDuckDB();

  const handleInitializeDuckDB = async () => {
    try {
      toast.info('🔧 Initializing DuckDB WASM in your browser...');
      await initialize();
      toast.success('✅ DuckDB WASM ready! You can now analyze ETF data locally.');
    } catch (err) {
      toast.error('❌ Failed to initialize DuckDB WASM');
      console.error(err);
    }
  };

  const handleAnalyzeETF = async (product: any) => {
    if (!isInitialized) {
      toast.error('⚠️ Please initialize DuckDB first by clicking "Initialize DuckDB" button');
      return;
    }

    setIsLoadingData(true);
    setSelectedProduct(product);

    try {
      // Use the S3 URL from the database
      if (!product.s3Path) {
        throw new Error('No S3 URL found for this ETF');
      }
      
      toast.info(`📊 Loading ${product.ticker} historical data (OHLCV) from S3...`, { duration: 2000 });
      
      // Load the Parquet file from S3 into DuckDB
      await loadParquetFile(product.ticker, product.s3Path);
      
      toast.info(`🔍 Querying ${product.ticker} data with SQL...`, { duration: 1500 });
      
      // Query the first 100 rows
      const result = await query(`
        SELECT * FROM ${product.ticker} 
        ORDER BY date DESC 
        LIMIT 100
      `);
      
      setQueryResult(result);
      toast.success(`✅ Loaded ${result.length} rows from ${product.ticker} • All processing done in your browser!`);
    } catch (err) {
      console.error('Failed to load ETF data:', err);
      toast.error(`❌ Failed to load ${product.ticker} data. File may not exist.`);
    } finally {
      setIsLoadingData(false);
    }
  };

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
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Data Mesh</h1>
        <p className="text-muted-foreground">ETF data catalog and analytics powered by DuckDB WASM</p>
      </div>

      {/* DuckDB Status Banner */}
      {!isInitialized && (
        <Card className="mb-6 border-blue-200 bg-blue-50">
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <Database className="h-5 w-5 text-blue-600" />
              <div>
                <p className="font-medium text-blue-900">DuckDB WASM Analytics Engine</p>
                <p className="text-sm text-blue-700">
                  Click to initialize in-browser analytics on {totalProducts} ASX ETF Parquet files
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  💡 <strong>What is this?</strong> DuckDB WASM runs SQL queries directly in your browser—no server needed!
                </p>
                {error && (
                  <p className="text-sm text-red-600 mt-1">Error: {error}</p>
                )}
              </div>
            </div>
            <Button
              onClick={handleInitializeDuckDB}
              disabled={isInitializing}
            >
              {isInitializing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Initializing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Initialize DuckDB
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* DuckDB Ready Banner with Instructions */}
      {isInitialized && (
        <Card className="mb-6 border-green-200 bg-green-50">
          <CardContent className="py-4">
            <div className="flex items-start gap-3 mb-3">
              <Database className="h-5 w-5 text-green-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-green-900">✅ DuckDB WASM Ready</p>
                <p className="text-sm text-green-700">In-browser analytics engine initialized • Zero backend load • Query {totalProducts} ETF Parquet files directly</p>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-green-200">
              <p className="text-sm font-medium text-green-900 mb-2">📊 What you can do now:</p>
              <ul className="text-sm text-green-700 space-y-1 ml-4">
                <li>• <strong>Click "Analyze"</strong> on any ETF below to load its historical OHLCV data (Open, High, Low, Close, Volume)</li>
                <li>• <strong>Run SQL queries</strong> on Parquet files (e.g., SELECT * FROM etf_data LIMIT 10)</li>
                <li>• <strong>Compare performance</strong> across multiple ETFs with JOIN queries</li>
                <li>• <strong>Calculate metrics</strong> like returns, volatility, and correlations in real-time</li>
              </ul>
              
              <div className="mt-3 p-3 bg-white rounded border border-green-200">
                <p className="text-xs font-mono text-green-800">
                  💡 Example: SELECT ticker, AVG(close) as avg_price FROM etf_data GROUP BY ticker
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Query Results Display */}
      {queryResult.length > 0 && selectedProduct && (
        <Card className="mb-6 border-purple-200 bg-purple-50">
          <CardContent className="py-4">
            <div className="flex items-start gap-3 mb-3">
              <BarChart3 className="h-5 w-5 text-purple-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-purple-900">
                  📈 {selectedProduct.ticker} Data Loaded ({queryResult.length} rows)
                </p>
                <p className="text-sm text-purple-700">
                  Historical OHLCV data queried from Parquet file • All processing done locally in your browser
                </p>
              </div>
            </div>
            
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-purple-200">
                    {Object.keys(queryResult[0] || {}).slice(0, 7).map((key) => (
                      <th key={key} className="text-left p-2 font-medium text-purple-900">{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {queryResult.slice(0, 5).map((row, idx) => (
                    <tr key={idx} className="border-b border-purple-100">
                      {Object.values(row).slice(0, 7).map((val: any, i) => (
                        <td key={i} className="p-2 text-purple-800">
                          {typeof val === 'number' ? val.toFixed(2) : String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-purple-600 mt-2">
                Showing first 5 of {queryResult.length} rows
              </p>
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
              <Database className="h-4 w-4" />
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
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleAnalyzeETF(product)}
                      disabled={!isInitialized || isLoadingData}
                      title={!isInitialized ? "Initialize DuckDB first" : "Load and query Parquet file in browser"}
                    >
                      {isLoadingData && selectedProduct?.id === product.id ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Loading...
                        </>
                      ) : (
                        <>
                          <BarChart3 className="h-4 w-4 mr-2" />
                          Analyze
                        </>
                      )}
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
