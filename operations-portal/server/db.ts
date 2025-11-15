import { eq, desc, and, gte, lte } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import {
  InsertUser,
  users,
  portfolios,
  Portfolio,
  InsertPortfolio,
  portfolioHoldings,
  esgData,
  EsgData,
  InsertEsgData,
  loans,
  Loan,
  InsertLoan,
  loanPayments,
  rlAgents,
  RlAgent,
  InsertRlAgent,
  trainingRuns,
  kafkaTopics,
  dataProducts,
  DataProduct,
  InsertDataProduct,
  mcpTools,
  mcpExecutions,
  auditLog,
} from "../drizzle/schema";
import { ENV } from "./_core/env";

let _db: ReturnType<typeof drizzle> | null = null;

export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

// ============================================================================
// USER MANAGEMENT
// ============================================================================

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = "admin";
      updateSet.role = "admin";
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

// ============================================================================
// PORTFOLIO MANAGEMENT
// ============================================================================

export async function getPortfolios() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(portfolios).orderBy(desc(portfolios.createdAt));
}

export async function getPortfolioById(id: string) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(portfolios).where(eq(portfolios.id, id)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function getPortfoliosByAgent(agent: string) {
  const db = await getDb();
  if (!db) return [];

  return await db
    .select()
    .from(portfolios)
    .where(eq(portfolios.agent, agent as any))
    .orderBy(desc(portfolios.value));
}

export async function createPortfolio(portfolio: InsertPortfolio) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db.insert(portfolios).values(portfolio);
  return portfolio;
}

export async function updatePortfolio(id: string, updates: Partial<Portfolio>) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db.update(portfolios).set(updates).where(eq(portfolios.id, id));
}

export async function getPortfolioHoldings(portfolioId: string) {
  const db = await getDb();
  if (!db) return [];

  return await db
    .select()
    .from(portfolioHoldings)
    .where(eq(portfolioHoldings.portfolioId, portfolioId))
    .orderBy(desc(portfolioHoldings.weight));
}

// ============================================================================
// ESG DATA
// ============================================================================

export async function getEsgData() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(esgData).orderBy(desc(esgData.updatedAt));
}

export async function getEsgDataByTicker(ticker: string) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(esgData).where(eq(esgData.ticker, ticker)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function upsertEsgData(data: InsertEsgData) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db
    .insert(esgData)
    .values(data)
    .onDuplicateKeyUpdate({
      set: {
        name: data.name,
        esgRating: data.esgRating,
        esgScore: data.esgScore,
        environmentScore: data.environmentScore,
        socialScore: data.socialScore,
        governanceScore: data.governanceScore,
        carbonIntensity: data.carbonIntensity,
        controversyScore: data.controversyScore,
        provider: data.provider,
        updatedAt: new Date(),
      },
    });
}

// ============================================================================
// ULTRAGROW LOANS
// ============================================================================

export async function getLoans() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(loans).orderBy(desc(loans.createdAt));
}

export async function getLoanById(id: string) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(loans).where(eq(loans.id, id)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function getLoansByPortfolio(portfolioId: string) {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(loans).where(eq(loans.portfolioId, portfolioId));
}

export async function createLoan(loan: InsertLoan) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db.insert(loans).values(loan);
  return loan;
}

export async function updateLoan(id: string, updates: Partial<Loan>) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db.update(loans).set(updates).where(eq(loans.id, id));
}

export async function getLoanPayments(loanId: string) {
  const db = await getDb();
  if (!db) return [];

  return await db
    .select()
    .from(loanPayments)
    .where(eq(loanPayments.loanId, loanId))
    .orderBy(loanPayments.dueDate);
}

// ============================================================================
// RL AGENTS
// ============================================================================

export async function getRlAgents() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(rlAgents).orderBy(rlAgents.name);
}

export async function getRlAgentByName(name: string) {
  const db = await getDb();
  if (!db) return null;

  const result = await db
    .select()
    .from(rlAgents)
    .where(eq(rlAgents.name, name as any))
    .limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function upsertRlAgent(agent: InsertRlAgent) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db
    .insert(rlAgents)
    .values(agent)
    .onDuplicateKeyUpdate({
      set: {
        displayName: agent.displayName,
        objective: agent.objective,
        modelVersion: agent.modelVersion,
        status: agent.status,
        episodesTrained: agent.episodesTrained,
        avgReward: agent.avgReward,
        lastTrainedAt: agent.lastTrainedAt,
        deployedAt: agent.deployedAt,
        updatedAt: new Date(),
      },
    });
}

export async function getTrainingRuns(agentName?: string) {
  const db = await getDb();
  if (!db) return [];

  if (agentName) {
    return await db
      .select()
      .from(trainingRuns)
      .where(eq(trainingRuns.agentName, agentName as any))
      .orderBy(desc(trainingRuns.startedAt));
  }

  return await db.select().from(trainingRuns).orderBy(desc(trainingRuns.startedAt));
}

// ============================================================================
// KAFKA TOPICS
// ============================================================================

export async function getKafkaTopics() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(kafkaTopics).orderBy(kafkaTopics.name);
}

// ============================================================================
// DATA MESH
// ============================================================================

export async function getDataProducts() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(dataProducts).orderBy(desc(dataProducts.lastUpdated));
}

export async function getDataProductByName(name: string) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(dataProducts).where(eq(dataProducts.name, name)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function upsertDataProduct(product: InsertDataProduct) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db
    .insert(dataProducts)
    .values(product)
    .onDuplicateKeyUpdate({
      set: {
        description: product.description,
        category: product.category,
        s3Path: product.s3Path,
        format: product.format,
        schema: product.schema,
        rowCount: product.rowCount,
        sizeBytes: product.sizeBytes,
        owner: product.owner,
        status: product.status,
        lastUpdated: new Date(),
      },
    });
}

// ============================================================================
// MCP TOOLS
// ============================================================================

export async function getMcpTools() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(mcpTools).orderBy(mcpTools.category, mcpTools.name);
}

export async function getMcpToolByName(name: string) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(mcpTools).where(eq(mcpTools.name, name)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function getMcpExecutions(toolId?: number, limit: number = 100) {
  const db = await getDb();
  if (!db) return [];

  if (toolId) {
    return await db
      .select()
      .from(mcpExecutions)
      .where(eq(mcpExecutions.toolId, toolId))
      .orderBy(desc(mcpExecutions.executedAt))
      .limit(limit);
  }

  return await db.select().from(mcpExecutions).orderBy(desc(mcpExecutions.executedAt)).limit(limit);
}

// ============================================================================
// AUDIT LOG
// ============================================================================

export async function logAudit(log: {
  userId?: number;
  action: string;
  resource: string;
  resourceId?: string;
  details?: string;
  ipAddress?: string;
  userAgent?: string;
}) {
  const db = await getDb();
  if (!db) return;

  await db.insert(auditLog).values(log);
}

export async function getAuditLogs(filters?: {
  userId?: number;
  resource?: string;
  startDate?: Date;
  endDate?: Date;
  limit?: number;
}) {
  const db = await getDb();
  if (!db) return [];

  let query = db.select().from(auditLog);

  const conditions = [];
  if (filters?.userId) {
    conditions.push(eq(auditLog.userId, filters.userId));
  }
  if (filters?.resource) {
    conditions.push(eq(auditLog.resource, filters.resource));
  }
  if (filters?.startDate) {
    conditions.push(gte(auditLog.createdAt, filters.startDate));
  }
  if (filters?.endDate) {
    conditions.push(lte(auditLog.createdAt, filters.endDate));
  }

  if (conditions.length > 0) {
    query = query.where(and(...conditions)) as any;
  }

  return await query.orderBy(desc(auditLog.createdAt)).limit(filters?.limit || 100);
}
