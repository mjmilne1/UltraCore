-- UltraCore Database Initialization

-- Create event store table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    aggregate_id VARCHAR(255) NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    correlation_id VARCHAR(255),
    causation_id VARCHAR(255),
    version INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(aggregate_type, event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id);

-- Create materialized view for aggregate state
CREATE MATERIALIZED VIEW IF NOT EXISTS aggregate_state AS
SELECT 
    aggregate_id,
    aggregate_type,
    MAX(timestamp) as last_updated,
    COUNT(*) as event_count
FROM events
GROUP BY aggregate_id, aggregate_type;

CREATE UNIQUE INDEX IF NOT EXISTS idx_aggregate_state ON aggregate_state(aggregate_id, aggregate_type);

-- Create audit log table (for compliance)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    changes JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ultracore;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ultracore;
