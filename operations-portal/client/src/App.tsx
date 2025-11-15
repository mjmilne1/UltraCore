import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import DashboardLayout from "./components/DashboardLayout";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import Portfolios from "./pages/Portfolios";
import PortfolioDetail from "./pages/PortfolioDetail";
import ESG from "./pages/ESG";
import Loans from "./pages/Loans";
import Agents from "./pages/Agents";
import Kafka from "./pages/Kafka";
import DataMesh from "./pages/DataMesh";
import MCP from "./pages/MCP";

function Router() {
  return (
    <Switch>
      {/* All routes wrapped in DashboardLayout for authenticated access */}
      <Route path="/">
        <DashboardLayout>
          <Home />
        </DashboardLayout>
      </Route>
      <Route path="/portfolios">
        <DashboardLayout>
          <Portfolios />
        </DashboardLayout>
      </Route>
      <Route path="/portfolios/:id">
        <DashboardLayout>
          <PortfolioDetail />
        </DashboardLayout>
      </Route>
      <Route path="/esg">
        <DashboardLayout>
          <ESG />
        </DashboardLayout>
      </Route>
      <Route path="/loans">
        <DashboardLayout>
          <Loans />
        </DashboardLayout>
      </Route>
      <Route path="/agents">
        <DashboardLayout>
          <Agents />
        </DashboardLayout>
      </Route>
      <Route path="/kafka">
        <DashboardLayout>
          <Kafka />
        </DashboardLayout>
      </Route>
      <Route path="/data-mesh">
        <DashboardLayout>
          <DataMesh />
        </DashboardLayout>
      </Route>
      <Route path="/mcp">
        <DashboardLayout>
          <MCP />
        </DashboardLayout>
      </Route>
      <Route path="/404" component={NotFound} />
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
