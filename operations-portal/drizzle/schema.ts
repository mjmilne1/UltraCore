import { int, mysqlEnum, mysqlTable, text, timestamp, varchar, decimal, boolean } from "drizzle-orm/mysql-core";

/**
 * UltraCore Operations Portal Database Schema
 * Comprehensive schema for portfolios, ESG, loans, RL agents, and system management
 */

// ============================================================================
// USERS & AUTHENTICATION
// ============================================================================

export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin", "operations", "analyst"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

// ============================================================================
// PORTFOLIOS
// ============================================================================

export const portfolios = mysqlTable("portfolios", {
  id: varchar("id", { length: 64 }).primaryKey(),
  investorId: int("investor_id").notNull(),
  investorName: varchar("investor_name", { length: 255 }).notNull(),
  agent: mysqlEnum("agent", ["alpha", "beta", "gamma", "delta", "epsilon"]).notNull(),
  value: decimal("value", { precision: 15, scale: 2 }).notNull(),
  initialInvestment: decimal("initial_investment", { precision: 15, scale: 2 }).notNull(),
  return30d: decimal("return_30d", { precision: 8, scale: 4 }),
  return1y: decimal("return_1y", { precision: 8, scale: 4 }),
  sharpeRatio: decimal("sharpe_ratio", { precision: 8, scale: 4 }),
  volatility: decimal("volatility", { precision: 8, scale: 4 }),
  maxDrawdown: decimal("max_drawdown", { precision: 8, scale: 4 }),
  status: mysqlEnum("status", ["active", "paused", "closed"]).default("active").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export type Portfolio = typeof portfolios.$inferSelect;
export type InsertPortfolio = typeof portfolios.$inferInsert;

export const portfolioHoldings = mysqlTable("portfolio_holdings", {
  id: int("id").autoincrement().primaryKey(),
  portfolioId: varchar("portfolio_id", { length: 64 }).notNull(),
  ticker: varchar("ticker", { length: 20 }).notNull(),
  weight: decimal("weight", { precision: 8, scale: 6 }).notNull(),
  value: decimal("value", { precision: 15, scale: 2 }).notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export type PortfolioHolding = typeof portfolioHoldings.$inferSelect;

// ============================================================================
// ESG DATA
// ============================================================================

export const esgData = mysqlTable("esg_data", {
  id: int("id").autoincrement().primaryKey(),
  ticker: varchar("ticker", { length: 20 }).notNull().unique(),
  name: varchar("name", { length: 255 }).notNull(),
  esgRating: varchar("esg_rating", { length: 10 }),
  esgScore: int("esg_score"),
  environmentScore: int("environment_score"),
  socialScore: int("social_score"),
  governanceScore: int("governance_score"),
  carbonIntensity: decimal("carbon_intensity", { precision: 10, scale: 2 }),
  controversyScore: int("controversy_score"),
  provider: varchar("provider", { length: 50 }),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export type EsgData = typeof esgData.$inferSelect;
export type InsertEsgData = typeof esgData.$inferInsert;

// ============================================================================
// ULTRAGROW LOANS
// ============================================================================

export const loans = mysqlTable("loans", {
  id: varchar("id", { length: 64 }).primaryKey(),
  portfolioId: varchar("portfolio_id", { length: 64 }).notNull(),
  investorId: int("investor_id").notNull(),
  amount: decimal("amount", { precision: 15, scale: 2 }).notNull(),
  portfolioValue: decimal("portfolio_value", { precision: 15, scale: 2 }).notNull(),
  ltv: decimal("ltv", { precision: 5, scale: 4 }).notNull(),
  termMonths: int("term_months").notNull(),
  feeRate: decimal("fee_rate", { precision: 5, scale: 4 }).notNull(),
  monthlyPayment: decimal("monthly_payment", { precision: 15, scale: 2 }).notNull(),
  remainingBalance: decimal("remaining_balance", { precision: 15, scale: 2 }).notNull(),
  status: mysqlEnum("status", ["pending", "active", "paid", "defaulted", "liquidated"]).default("pending").notNull(),
  approvedBy: int("approved_by"),
  approvedAt: timestamp("approved_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export type Loan = typeof loans.$inferSelect;
export type InsertLoan = typeof loans.$inferInsert;

export const loanPayments = mysqlTable("loan_payments", {
  id: int("id").autoincrement().primaryKey(),
  loanId: varchar("loan_id", { length: 64 }).notNull(),
  amount: decimal("amount", { precision: 15, scale: 2 }).notNull(),
  principal: decimal("principal", { precision: 15, scale: 2 }).notNull(),
  fee: decimal("fee", { precision: 15, scale: 2 }).notNull(),
  dueDate: timestamp("due_date").notNull(),
  paidDate: timestamp("paid_date"),
  status: mysqlEnum("status", ["pending", "paid", "late", "missed"]).default("pending").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type LoanPayment = typeof loanPayments.$inferSelect;

// ============================================================================
// RL AGENTS & TRAINING
// ============================================================================

export const rlAgents = mysqlTable("rl_agents", {
  id: int("id").autoincrement().primaryKey(),
  name: mysqlEnum("name", ["alpha", "beta", "gamma", "delta", "epsilon"]).notNull().unique(),
  displayName: varchar("display_name", { length: 100 }).notNull(),
  objective: text("objective").notNull(),
  modelVersion: varchar("model_version", { length: 50 }).notNull(),
  status: mysqlEnum("status", ["training", "deployed", "paused", "deprecated"]).default("deployed").notNull(),
  episodesTrained: int("episodes_trained").default(0).notNull(),
  avgReward: decimal("avg_reward", { precision: 10, scale: 4 }),
  lastTrainedAt: timestamp("last_trained_at"),
  deployedAt: timestamp("deployed_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export type RlAgent = typeof rlAgents.$inferSelect;
export type InsertRlAgent = typeof rlAgents.$inferInsert;

export const trainingRuns = mysqlTable("training_runs", {
  id: int("id").autoincrement().primaryKey(),
  agentName: mysqlEnum("agent_name", ["alpha", "beta", "gamma", "delta", "epsilon"]).notNull(),
  episodes: int("episodes").notNull(),
  avgReward: decimal("avg_reward", { precision: 10, scale: 4 }),
  finalReward: decimal("final_reward", { precision: 10, scale: 4 }),
  duration: int("duration"),
  status: mysqlEnum("status", ["running", "completed", "failed"]).default("running").notNull(),
  startedAt: timestamp("started_at").defaultNow().notNull(),
  completedAt: timestamp("completed_at"),
});

export type TrainingRun = typeof trainingRuns.$inferSelect;

// ============================================================================
// KAFKA EVENTS (Metadata only - actual events in Kafka)
// ============================================================================

export const kafkaTopics = mysqlTable("kafka_topics", {
  id: int("id").autoincrement().primaryKey(),
  name: varchar("name", { length: 255 }).notNull().unique(),
  description: text("description"),
  partitions: int("partitions").default(1).notNull(),
  replicationFactor: int("replication_factor").default(1).notNull(),
  enabled: boolean("enabled").default(true).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type KafkaTopic = typeof kafkaTopics.$inferSelect;

// ============================================================================
// DATA MESH PRODUCTS
// ============================================================================

export const dataProducts = mysqlTable("data_products", {
  id: int("id").autoincrement().primaryKey(),
  name: varchar("name", { length: 255 }).notNull().unique(),
  description: text("description"),
  category: mysqlEnum("category", ["portfolio", "esg", "market", "risk", "performance"]).notNull(),
  s3Path: varchar("s3_path", { length: 500 }).notNull(),
  format: varchar("format", { length: 50 }).notNull(),
  schema: text("schema"),
  rowCount: int("row_count"),
  sizeBytes: int("size_bytes"),
  owner: varchar("owner", { length: 100 }),
  status: mysqlEnum("status", ["active", "deprecated", "archived"]).default("active").notNull(),
  lastUpdated: timestamp("last_updated").defaultNow().onUpdateNow().notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type DataProduct = typeof dataProducts.$inferSelect;
export type InsertDataProduct = typeof dataProducts.$inferInsert;

// ============================================================================
// MCP TOOLS REGISTRY
// ============================================================================

export const mcpTools = mysqlTable("mcp_tools", {
  id: int("id").autoincrement().primaryKey(),
  name: varchar("name", { length: 255 }).notNull().unique(),
  description: text("description").notNull(),
  category: mysqlEnum("category", ["portfolio", "esg", "loan", "agent", "data", "system"]).notNull(),
  inputSchema: text("input_schema").notNull(),
  enabled: boolean("enabled").default(true).notNull(),
  executionCount: int("execution_count").default(0).notNull(),
  lastExecuted: timestamp("last_executed"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type McpTool = typeof mcpTools.$inferSelect;

export const mcpExecutions = mysqlTable("mcp_executions", {
  id: int("id").autoincrement().primaryKey(),
  toolId: int("tool_id").notNull(),
  toolName: varchar("tool_name", { length: 255 }).notNull(),
  input: text("input").notNull(),
  output: text("output"),
  status: mysqlEnum("status", ["success", "error", "timeout"]).notNull(),
  duration: int("duration"),
  executedBy: varchar("executed_by", { length: 100 }),
  executedAt: timestamp("executed_at").defaultNow().notNull(),
});

export type McpExecution = typeof mcpExecutions.$inferSelect;

// ============================================================================
// AUDIT LOG
// ============================================================================

export const auditLog = mysqlTable("audit_log", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("user_id"),
  action: varchar("action", { length: 100 }).notNull(),
  resource: varchar("resource", { length: 100 }).notNull(),
  resourceId: varchar("resource_id", { length: 64 }),
  details: text("details"),
  ipAddress: varchar("ip_address", { length: 45 }),
  userAgent: text("user_agent"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type AuditLog = typeof auditLog.$inferSelect;
