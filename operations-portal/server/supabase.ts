import { createClient } from '@supabase/supabase-js';
import { ENV } from './_core/env';

/**
 * Supabase client for server-side operations
 * Provides access to PostgreSQL database, Auth, Storage, and Real-time
 */

const supabaseUrl = process.env.SUPABASE_URL || '';
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY || '';

if (!supabaseUrl || !supabaseServiceKey) {
  console.warn('[Supabase] Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables');
}

// Server-side client with service role key (bypasses RLS)
export const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false,
  },
});

// Create client with user's JWT for RLS-protected operations
export const createSupabaseClient = (accessToken: string) => {
  return createClient(supabaseUrl, supabaseServiceKey, {
    global: {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  });
};

/**
 * Database helper functions
 */

export interface Portfolio {
  id: string;
  investor_id: string;
  agent: 'alpha' | 'beta' | 'gamma' | 'delta' | 'epsilon';
  value: number;
  initial_investment: number;
  return_30d: number;
  sharpe_ratio: number;
  created_at: string;
  updated_at: string;
}

export interface Loan {
  id: string;
  portfolio_id: string;
  amount: number;
  ltv: number;
  term_months: number;
  fee_rate: number;
  status: 'pending' | 'active' | 'paid' | 'defaulted';
  created_at: string;
  updated_at: string;
}

export interface EsgData {
  id: string;
  ticker: string;
  esg_rating: string;
  carbon_intensity: number;
  controversy_score: number;
  updated_at: string;
}

// Portfolio queries
export async function getPortfolios() {
  const { data, error } = await supabaseAdmin
    .from('portfolios')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data as Portfolio[];
}

export async function getPortfolioById(id: string) {
  const { data, error } = await supabaseAdmin
    .from('portfolios')
    .select('*')
    .eq('id', id)
    .single();

  if (error) throw error;
  return data as Portfolio;
}

export async function createPortfolio(portfolio: Omit<Portfolio, 'id' | 'created_at' | 'updated_at'>) {
  const { data, error } = await supabaseAdmin
    .from('portfolios')
    .insert(portfolio)
    .select()
    .single();

  if (error) throw error;
  return data as Portfolio;
}

// Loan queries
export async function getLoans() {
  const { data, error } = await supabaseAdmin
    .from('loans')
    .select('*, portfolios(*)')
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
}

export async function getLoanById(id: string) {
  const { data, error } = await supabaseAdmin
    .from('loans')
    .select('*, portfolios(*)')
    .eq('id', id)
    .single();

  if (error) throw error;
  return data;
}

// ESG queries
export async function getEsgData() {
  const { data, error } = await supabaseAdmin
    .from('esg_data')
    .select('*')
    .order('updated_at', { ascending: false });

  if (error) throw error;
  return data as EsgData[];
}

export async function getEsgDataByTicker(ticker: string) {
  const { data, error } = await supabaseAdmin
    .from('esg_data')
    .select('*')
    .eq('ticker', ticker)
    .single();

  if (error) throw error;
  return data as EsgData;
}
