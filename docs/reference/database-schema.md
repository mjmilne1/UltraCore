# UltraCore Database Schema

## Overview

Comprehensive PostgreSQL database schema for UltraCore's security and banking entities with full support for multi-tenancy, audit trails, and AI-powered security.

---

## Security Tables

### 1. users

**Purpose:** User accounts with authentication and MFA

| Column | Type | Description |
|--------|------|-------------|
| user_id | UUID | Primary key |
| tenant_id | UUID | Multi-tenancy isolation |
| username | VARCHAR(255) | Unique username |
| email | VARCHAR(255) | Unique email |
| password_hash | VARCHAR(255) | Bcrypt hashed password |
| first_name | VARCHAR(100) | User's first name |
| last_name | VARCHAR(100) | User's last name |
| phone_number | VARCHAR(50) | Contact phone |
| role | VARCHAR(50) | User role (super_admin, admin, manager, officer, customer) |
| permissions | ARRAY(VARCHAR) | Specific permissions |
| is_active | BOOLEAN | Account active status |
| is_locked | BOOLEAN | Account locked status |
| is_verified | BOOLEAN | Email verified |
| mfa_enabled | BOOLEAN | MFA enabled |
| mfa_secret | VARCHAR(255) | TOTP secret (encrypted) |
| password_changed_at | TIMESTAMP | Last password change |
| password_expires_at | TIMESTAMP | Password expiration |
| failed_login_attempts | INTEGER | Failed login count |
| locked_until | TIMESTAMP | Lock expiration |
| trust_score | DECIMAL(5,2) | AI-powered trust score (0-100) |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update |
| last_login_at | TIMESTAMP | Last login |
| last_login_ip | INET | Last login IP |

**Indexes:**
- `idx_users_tenant` - Tenant isolation
- `idx_users_username` - Login lookup
- `idx_users_email` - Email lookup
- `idx_users_role` - Role-based queries
- `idx_users_active` - Active users
- `idx_users_tenant_role` - Composite for tenant + role
- `idx_users_email_active` - Composite for email + active

---

### 2. mfa_backup_codes

**Purpose:** MFA backup codes for account recovery

| Column | Type | Description |
|--------|------|-------------|
| code_id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| code_hash | VARCHAR(255) | Hashed backup code |
| used_at | TIMESTAMP | When code was used |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- `idx_mfa_backup_codes_user` - User lookup

---

### 3. refresh_tokens

**Purpose:** JWT refresh tokens for session management

| Column | Type | Description |
|--------|------|-------------|
| token_id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| token_hash | VARCHAR(255) | Hashed refresh token |
| expires_at | TIMESTAMP | Token expiration |
| revoked_at | TIMESTAMP | Revocation timestamp |
| device_fingerprint | VARCHAR(255) | Device identifier |
| ip_address | INET | IP address |
| user_agent | TEXT | Browser user agent |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- `idx_refresh_tokens_user` - User lookup
- `idx_refresh_tokens_expires` - Expiration cleanup
- `idx_refresh_tokens_user_expires` - Composite for user + expiration

---

### 4. trusted_devices

**Purpose:** Trusted devices for users

| Column | Type | Description |
|--------|------|-------------|
| device_id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| device_fingerprint | VARCHAR(255) | Device identifier |
| device_name | VARCHAR(255) | Device name (e.g., "iPhone 13 Pro") |
| device_type | VARCHAR(50) | Device type (mobile, desktop, tablet) |
| trust_score | DECIMAL(5,2) | AI-powered trust score (0-100) |
| is_trusted | BOOLEAN | Trusted status |
| first_seen_at | TIMESTAMP | First seen |
| last_seen_at | TIMESTAMP | Last seen |
| last_ip_address | INET | Last IP address |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update |

**Indexes:**
- `idx_trusted_devices_user` - User lookup
- `idx_trusted_devices_fingerprint` - Device lookup

---

### 5. security_events

**Purpose:** Security events for audit trail and threat detection

| Column | Type | Description |
|--------|------|-------------|
| event_id | UUID | Primary key |
| tenant_id | UUID | Multi-tenancy isolation |
| user_id | UUID | Foreign key to users |
| event_type | VARCHAR(100) | Event type (login_attempt, access_denied, etc.) |
| event_category | VARCHAR(50) | Category (authentication, authorization, threat, incident) |
| severity | VARCHAR(20) | Severity (low, medium, high, critical) |
| ip_address | INET | IP address |
| device_fingerprint | VARCHAR(255) | Device identifier |
| user_agent | TEXT | Browser user agent |
| geolocation | JSON | {latitude, longitude, city, country} |
| description | TEXT | Event description |
| metadata | JSON | Additional event data |
| risk_score | DECIMAL(5,2) | AI risk score (0-100) |
| fraud_score | DECIMAL(5,2) | Fraud probability (0-1) |
| anomaly_score | DECIMAL(5,2) | Anomaly score (0-1) |
| action_taken | VARCHAR(50) | Action (allow, deny, challenge, block, lock) |
| timestamp | TIMESTAMP | Event timestamp |

**Indexes:**
- `idx_security_events_tenant` - Tenant isolation
- `idx_security_events_user` - User lookup
- `idx_security_events_type` - Event type queries
- `idx_security_events_category` - Category queries
- `idx_security_events_severity` - Severity queries
- `idx_security_events_timestamp` - Time-based queries
- `idx_security_events_ip` - IP-based queries
- `idx_security_events_tenant_type` - Composite for tenant + type
- `idx_security_events_user_timestamp` - Composite for user + time
- `idx_security_events_severity_timestamp` - Composite for severity + time

---

### 6. threat_events

**Purpose:** Detected security threats

| Column | Type | Description |
|--------|------|-------------|
| threat_id | UUID | Primary key |
| tenant_id | UUID | Multi-tenancy isolation |
| threat_type | VARCHAR(100) | Threat type (fraud, brute_force, account_takeover) |
| severity | VARCHAR(20) | Severity (low, medium, high, critical) |
| status | VARCHAR(50) | Status (detected, investigating, mitigated, resolved) |
| description | TEXT | Threat description |
| indicators | ARRAY(VARCHAR) | Threat indicators |
| affected_user_ids | ARRAY(UUID) | Affected users |
| affected_account_ids | ARRAY(UUID) | Affected accounts |
| affected_transaction_ids | ARRAY(UUID) | Affected transactions |
| detection_method | VARCHAR(100) | Detection method (ml_model, rule_based, manual) |
| confidence | DECIMAL(5,2) | Confidence (0-100) |
| response_action | VARCHAR(100) | Response action (block, lock, alert, escalate) |
| response_status | VARCHAR(50) | Response status (pending, executed, failed) |
| detected_at | TIMESTAMP | Detection timestamp |
| mitigated_at | TIMESTAMP | Mitigation timestamp |
| resolved_at | TIMESTAMP | Resolution timestamp |

**Indexes:**
- `idx_threat_events_tenant` - Tenant isolation
- `idx_threat_events_type` - Threat type queries
- `idx_threat_events_severity` - Severity queries
- `idx_threat_events_status` - Status queries
- `idx_threat_events_detected` - Time-based queries
- `idx_threat_events_tenant_type` - Composite for tenant + type
- `idx_threat_events_severity_status` - Composite for severity + status

---

### 7. security_incidents

**Purpose:** Security incidents requiring investigation

| Column | Type | Description |
|--------|------|-------------|
| incident_id | UUID | Primary key |
| tenant_id | UUID | Multi-tenancy isolation |
| incident_type | VARCHAR(100) | Incident type |
| severity | VARCHAR(20) | Severity (low, medium, high, critical) |
| status | VARCHAR(50) | Status (open, investigating, resolved, closed) |
| priority | VARCHAR(20) | Priority (low, medium, high, critical) |
| title | VARCHAR(500) | Incident title |
| description | TEXT | Incident description |
| assigned_to | UUID | Assigned user |
| related_threat_ids | ARRAY(UUID) | Related threats |
| related_event_ids | ARRAY(UUID) | Related events |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update |
| resolved_at | TIMESTAMP | Resolution timestamp |
| closed_at | TIMESTAMP | Closure timestamp |

**Indexes:**
- `idx_security_incidents_tenant` - Tenant isolation
- `idx_security_incidents_type` - Incident type queries
- `idx_security_incidents_severity` - Severity queries
- `idx_security_incidents_status` - Status queries
- `idx_security_incidents_priority` - Priority queries
- `idx_security_incidents_tenant_status` - Composite for tenant + status
- `idx_security_incidents_severity_priority` - Composite for severity + priority

---

### 8. threat_intelligence

**Purpose:** Threat intelligence data

| Column | Type | Description |
|--------|------|-------------|
| intel_id | UUID | Primary key |
| indicator_type | VARCHAR(50) | Indicator type (ip, domain, email, hash) |
| indicator_value | VARCHAR(500) | Indicator value |
| threat_type | VARCHAR(100) | Threat type |
| severity | VARCHAR(20) | Severity (low, medium, high, critical) |
| confidence | DECIMAL(5,2) | Confidence (0-100) |
| source | VARCHAR(100) | Source (internal, virustotal, abuseipdb) |
| source_url | TEXT | Source URL |
| description | TEXT | Description |
| metadata | JSON | Additional data |
| first_seen | TIMESTAMP | First seen |
| last_seen | TIMESTAMP | Last seen |
| expires_at | TIMESTAMP | Expiration |
| is_active | BOOLEAN | Active status |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update |

**Indexes:**
- `idx_threat_intel_indicator_type` - Indicator type queries
- `idx_threat_intel_indicator_value` - Indicator value queries
- `idx_threat_intel_active` - Active indicators
- `idx_threat_intel_indicator` - Composite for type + value
- `idx_threat_intel_active_expires` - Composite for active + expiration

---

### 9. rate_limit_entries

**Purpose:** Rate limit tracking with ML-based adaptive limits

| Column | Type | Description |
|--------|------|-------------|
| entry_id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| ip_address | INET | IP address |
| endpoint | VARCHAR(255) | API endpoint |
| request_count | INTEGER | Request count in window |
| window_start | TIMESTAMP | Window start |
| window_end | TIMESTAMP | Window end |
| base_limit | INTEGER | Base rate limit |
| adaptive_limit | INTEGER | ML-calculated adaptive limit |
| trust_multiplier | DECIMAL(5,2) | Trust score multiplier |
| is_blocked | BOOLEAN | Blocked status |
| blocked_until | TIMESTAMP | Block expiration |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update |

**Indexes:**
- `idx_rate_limit_user` - User lookup
- `idx_rate_limit_ip` - IP lookup
- `idx_rate_limit_endpoint` - Endpoint lookup
- `idx_rate_limit_user_endpoint` - Composite for user + endpoint
- `idx_rate_limit_ip_endpoint` - Composite for IP + endpoint
- `idx_rate_limit_window` - Window queries

---

### 10. audit_log

**Purpose:** Comprehensive audit log for compliance

| Column | Type | Description |
|--------|------|-------------|
| audit_id | UUID | Primary key |
| tenant_id | UUID | Multi-tenancy isolation |
| user_id | UUID | Foreign key to users |
| action | VARCHAR(255) | Action performed |
| entity_type | VARCHAR(100) | Entity type |
| entity_id | UUID | Entity ID |
| old_values | JSON | Old values (before change) |
| new_values | JSON | New values (after change) |
| ip_address | INET | IP address |
| user_agent | TEXT | Browser user agent |
| timestamp | TIMESTAMP | Action timestamp |

**Indexes:**
- `idx_audit_log_tenant` - Tenant isolation
- `idx_audit_log_user` - User lookup
- `idx_audit_log_action` - Action queries
- `idx_audit_log_entity_type` - Entity type queries
- `idx_audit_log_entity_id` - Entity ID queries
- `idx_audit_log_timestamp` - Time-based queries
- `idx_audit_log_tenant_timestamp` - Composite for tenant + time
- `idx_audit_log_user_timestamp` - Composite for user + time
- `idx_audit_log_entity` - Composite for entity type + ID

---

## Key Features

### Multi-Tenancy
- All tables include `tenant_id` for data isolation
- Row-level security (RLS) can be enabled for additional isolation
- Composite indexes for tenant-based queries

### AI-Powered Security
- `trust_score` fields for users and devices
- `risk_score`, `fraud_score`, `anomaly_score` in security events
- `adaptive_limit` in rate limiting for ML-based throttling

### Comprehensive Audit Trail
- `security_events` table for all security-related events
- `audit_log` table for all data modifications
- Complete context (IP, user agent, geolocation)

### Threat Detection & Response
- `threat_events` for detected threats
- `security_incidents` for investigations
- `threat_intelligence` for external threat data

### Performance Optimization
- Strategic indexes for common query patterns
- Composite indexes for multi-column queries
- INET type for IP addresses
- JSON type for flexible metadata

---

## Migration Management

### Alembic Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Add security tables"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

---

## Security Considerations

1. **Password Storage:** Bcrypt hashing with cost factor 12
2. **MFA Secrets:** Encrypted before storage
3. **Backup Codes:** Hashed before storage
4. **Refresh Tokens:** Hashed before storage
5. **Audit Log:** Immutable (append-only)
6. **IP Addresses:** INET type for efficient storage and queries
7. **Sensitive Data:** Encrypted at rest (application layer)

---

## Compliance

- **APRA:** Comprehensive audit trail for prudential compliance
- **ASIC:** Complete transaction history and user actions
- **Privacy Act:** PII handling with encryption and access controls
- **CDR:** Open banking data access and consent tracking
