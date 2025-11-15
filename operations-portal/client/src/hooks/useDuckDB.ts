import { useState, useCallback } from 'react';
import * as duckdb from '@duckdb/duckdb-wasm';
import duckdb_wasm from '@duckdb/duckdb-wasm/dist/duckdb-mvp.wasm?url';
import mvp_worker from '@duckdb/duckdb-wasm/dist/duckdb-browser-mvp.worker.js?url';
import duckdb_wasm_eh from '@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url';
import eh_worker from '@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url';

export interface DuckDBState {
  db: duckdb.AsyncDuckDB | null;
  conn: duckdb.AsyncDuckDBConnection | null;
  isInitializing: boolean;
  isInitialized: boolean;
  error: string | null;
}

export function useDuckDB() {
  const [state, setState] = useState<DuckDBState>({
    db: null,
    conn: null,
    isInitializing: false,
    isInitialized: false,
    error: null,
  });

  const initialize = useCallback(async () => {
    if (state.isInitialized || state.isInitializing) {
      return;
    }

    setState(prev => ({ ...prev, isInitializing: true, error: null }));

    try {
      // Select bundle based on browser capabilities
      const MANUAL_BUNDLES: duckdb.DuckDBBundles = {
        mvp: {
          mainModule: duckdb_wasm,
          mainWorker: mvp_worker,
        },
        eh: {
          mainModule: duckdb_wasm_eh,
          mainWorker: eh_worker,
        },
      };

      // Select a bundle based on browser capabilities
      const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);

      // Instantiate the worker
      const worker = new Worker(bundle.mainWorker!);
      const logger = new duckdb.ConsoleLogger();
      const db = new duckdb.AsyncDuckDB(logger, worker);
      await db.instantiate(bundle.mainModule, bundle.pthreadWorker);

      // Create a connection
      const conn = await db.connect();

      setState({
        db,
        conn,
        isInitializing: false,
        isInitialized: true,
        error: null,
      });

      console.log('✅ DuckDB WASM initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize DuckDB WASM:', error);
      setState(prev => ({
        ...prev,
        isInitializing: false,
        error: error instanceof Error ? error.message : 'Failed to initialize DuckDB',
      }));
    }
  }, [state.isInitialized, state.isInitializing]);

  const query = useCallback(
    async (sql: string): Promise<any[]> => {
      if (!state.conn) {
        throw new Error('DuckDB not initialized. Call initialize() first.');
      }

      try {
        const result = await state.conn.query(sql);
        return result.toArray().map(row => row.toJSON());
      } catch (error) {
        console.error('Query error:', error);
        throw error;
      }
    },
    [state.conn]
  );

  const loadParquetFile = useCallback(
    async (tableName: string, fileUrl: string) => {
      if (!state.conn || !state.db) {
        throw new Error('DuckDB not initialized');
      }

      try {
        console.log(`📥 Fetching Parquet file from: ${fileUrl}`);
        
        // Fetch the Parquet file from S3/HTTP
        const response = await fetch(fileUrl);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const arrayBuffer = await response.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        
        console.log(`📦 Downloaded ${uint8Array.length} bytes, registering with DuckDB...`);
        
        // Register the file with DuckDB WASM
        await state.db.registerFileBuffer(`${tableName}.parquet`, uint8Array);
        
        // Create table from the registered file
        await state.conn.query(`
          CREATE OR REPLACE TABLE ${tableName} AS 
          SELECT * FROM read_parquet('${tableName}.parquet')
        `);
        
        console.log(`✅ Loaded ${tableName} from ${fileUrl}`);
      } catch (error) {
        console.error(`❌ Failed to load ${tableName}:`, error);
        throw error;
      }
    },
    [state.conn, state.db]
  );

  const close = useCallback(async () => {
    if (state.conn) {
      await state.conn.close();
    }
    if (state.db) {
      await state.db.terminate();
    }
    setState({
      db: null,
      conn: null,
      isInitializing: false,
      isInitialized: false,
      error: null,
    });
  }, [state.conn, state.db]);

  return {
    ...state,
    initialize,
    query,
    loadParquetFile,
    close,
  };
}
