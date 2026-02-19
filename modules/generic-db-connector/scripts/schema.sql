-- ==============================================================================
-- OKTA GENERIC DATABASE CONNECTOR - SCHEMA
-- ==============================================================================
-- Schema for PostgreSQL to support:
-- - User provisioning (create, update, deactivate)
-- - Entitlement management (assign, revoke)
-- - User import to Okta
-- ==============================================================================

-- ==============================================================================
-- USERS TABLE
-- ==============================================================================
-- Core user table for provisioning
-- Maps to Okta user profile attributes

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(100) UNIQUE NOT NULL,  -- Unique identifier (maps to Okta externalId)
    username        VARCHAR(100) UNIQUE NOT NULL,  -- Login username
    email           VARCHAR(255) UNIQUE NOT NULL,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    display_name    VARCHAR(200),
    department      VARCHAR(100),
    title           VARCHAR(100),
    manager_id      VARCHAR(100),                  -- References another user's user_id
    employee_number VARCHAR(50),
    phone           VARCHAR(50),
    mobile_phone    VARCHAR(50),
    status          VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE, SUSPENDED
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deactivated_at  TIMESTAMP
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);

-- ==============================================================================
-- ENTITLEMENTS TABLE
-- ==============================================================================
-- Available entitlements/roles that can be assigned to users

CREATE TABLE IF NOT EXISTS entitlements (
    id              SERIAL PRIMARY KEY,
    entitlement_id  VARCHAR(100) UNIQUE NOT NULL,  -- Unique identifier for Okta
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    category        VARCHAR(100),                   -- e.g., 'Application', 'Role', 'Permission'
    risk_level      VARCHAR(20) DEFAULT 'LOW',      -- LOW, MEDIUM, HIGH, CRITICAL
    owner           VARCHAR(100),                   -- Owner email or ID
    status          VARCHAR(20) DEFAULT 'ACTIVE',   -- ACTIVE, DEPRECATED
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entitlements_category ON entitlements(category);
CREATE INDEX IF NOT EXISTS idx_entitlements_status ON entitlements(status);

-- ==============================================================================
-- USER_ENTITLEMENTS TABLE (Junction)
-- ==============================================================================
-- Maps users to their assigned entitlements

CREATE TABLE IF NOT EXISTS user_entitlements (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(100) NOT NULL,         -- References users.user_id
    entitlement_id  VARCHAR(100) NOT NULL,         -- References entitlements.entitlement_id
    granted_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by      VARCHAR(100),                   -- Who granted the entitlement
    expires_at      TIMESTAMP,                      -- Optional expiration
    status          VARCHAR(20) DEFAULT 'ACTIVE',   -- ACTIVE, REVOKED
    revoked_at      TIMESTAMP,
    revoked_by      VARCHAR(100),
    UNIQUE(user_id, entitlement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_entitlements_user ON user_entitlements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_entitlements_entitlement ON user_entitlements(entitlement_id);
CREATE INDEX IF NOT EXISTS idx_user_entitlements_status ON user_entitlements(status);

-- ==============================================================================
-- GROUPS TABLE (Optional)
-- ==============================================================================
-- Groups for organizing users

CREATE TABLE IF NOT EXISTS groups (
    id              SERIAL PRIMARY KEY,
    group_id        VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    group_type      VARCHAR(50) DEFAULT 'STANDARD', -- STANDARD, DYNAMIC
    status          VARCHAR(20) DEFAULT 'ACTIVE',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- USER_GROUPS TABLE (Junction)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS user_groups (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(100) NOT NULL,
    group_id        VARCHAR(100) NOT NULL,
    added_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by        VARCHAR(100),
    UNIQUE(user_id, group_id)
);

CREATE INDEX IF NOT EXISTS idx_user_groups_user ON user_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group ON user_groups(group_id);

-- ==============================================================================
-- AUDIT LOG TABLE
-- ==============================================================================
-- Track all provisioning operations for compliance

CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,
    operation       VARCHAR(50) NOT NULL,          -- CREATE, UPDATE, DELETE, ASSIGN, REVOKE
    entity_type     VARCHAR(50) NOT NULL,          -- USER, ENTITLEMENT, GROUP
    entity_id       VARCHAR(100) NOT NULL,
    old_values      JSONB,
    new_values      JSONB,
    performed_by    VARCHAR(100),
    performed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source          VARCHAR(50) DEFAULT 'OKTA'     -- OKTA, MANUAL, SYSTEM
);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_performed_at ON audit_log(performed_at);

-- ==============================================================================
-- TRIGGER FOR UPDATED_AT
-- ==============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entitlements_updated_at
    BEFORE UPDATE ON entitlements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- SAMPLE DATA - ENTITLEMENTS
-- ==============================================================================
-- Pre-populate with sample entitlements for demo

INSERT INTO entitlements (entitlement_id, name, description, category, risk_level) VALUES
    ('ent-read-only', 'Read Only Access', 'Basic read-only access to the system', 'Permission', 'LOW'),
    ('ent-read-write', 'Read/Write Access', 'Standard read and write access', 'Permission', 'MEDIUM'),
    ('ent-admin', 'Administrator', 'Full administrative access', 'Role', 'CRITICAL'),
    ('ent-analyst', 'Data Analyst', 'Access to analytics and reporting', 'Role', 'MEDIUM'),
    ('ent-developer', 'Developer', 'Developer access to APIs and tools', 'Role', 'MEDIUM'),
    ('ent-finance-view', 'Finance Viewer', 'View financial reports', 'Application', 'MEDIUM'),
    ('ent-finance-edit', 'Finance Editor', 'Edit financial data', 'Application', 'HIGH'),
    ('ent-hr-view', 'HR Viewer', 'View HR records', 'Application', 'MEDIUM'),
    ('ent-hr-admin', 'HR Administrator', 'Manage HR records', 'Application', 'HIGH'),
    ('ent-it-helpdesk', 'IT Helpdesk', 'IT helpdesk access', 'Role', 'LOW')
ON CONFLICT (entitlement_id) DO NOTHING;

-- ==============================================================================
-- SAMPLE DATA - USERS (Optional)
-- ==============================================================================
-- Sample users for testing

INSERT INTO users (user_id, username, email, first_name, last_name, department, title, status) VALUES
    ('usr-001', 'jsmith', 'john.smith@example.com', 'John', 'Smith', 'Engineering', 'Software Engineer', 'ACTIVE'),
    ('usr-002', 'jdoe', 'jane.doe@example.com', 'Jane', 'Doe', 'Engineering', 'Senior Engineer', 'ACTIVE'),
    ('usr-003', 'bwilson', 'bob.wilson@example.com', 'Bob', 'Wilson', 'Finance', 'Financial Analyst', 'ACTIVE'),
    ('usr-004', 'agarcia', 'alice.garcia@example.com', 'Alice', 'Garcia', 'HR', 'HR Manager', 'ACTIVE'),
    ('usr-005', 'mjohnson', 'mike.johnson@example.com', 'Mike', 'Johnson', 'IT', 'IT Admin', 'ACTIVE')
ON CONFLICT (user_id) DO NOTHING;

-- Assign some entitlements
INSERT INTO user_entitlements (user_id, entitlement_id, granted_by) VALUES
    ('usr-001', 'ent-developer', 'system'),
    ('usr-001', 'ent-read-write', 'system'),
    ('usr-002', 'ent-developer', 'system'),
    ('usr-002', 'ent-admin', 'system'),
    ('usr-003', 'ent-finance-view', 'system'),
    ('usr-003', 'ent-finance-edit', 'system'),
    ('usr-004', 'ent-hr-view', 'system'),
    ('usr-004', 'ent-hr-admin', 'system'),
    ('usr-005', 'ent-it-helpdesk', 'system'),
    ('usr-005', 'ent-admin', 'system')
ON CONFLICT (user_id, entitlement_id) DO NOTHING;

-- ==============================================================================
-- VIEWS FOR OKTA CONNECTOR
-- ==============================================================================

-- View for user import with entitlement count
CREATE OR REPLACE VIEW v_users_with_entitlements AS
SELECT
    u.user_id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.display_name,
    u.department,
    u.title,
    u.status,
    COUNT(ue.id) as entitlement_count,
    ARRAY_AGG(e.name) FILTER (WHERE e.name IS NOT NULL) as entitlement_names
FROM users u
LEFT JOIN user_entitlements ue ON u.user_id = ue.user_id AND ue.status = 'ACTIVE'
LEFT JOIN entitlements e ON ue.entitlement_id = e.entitlement_id
GROUP BY u.id, u.user_id, u.username, u.email, u.first_name, u.last_name,
         u.display_name, u.department, u.title, u.status;

-- View for active entitlements
CREATE OR REPLACE VIEW v_active_entitlements AS
SELECT
    e.entitlement_id,
    e.name,
    e.description,
    e.category,
    e.risk_level,
    COUNT(ue.id) as assigned_users
FROM entitlements e
LEFT JOIN user_entitlements ue ON e.entitlement_id = ue.entitlement_id AND ue.status = 'ACTIVE'
WHERE e.status = 'ACTIVE'
GROUP BY e.id, e.entitlement_id, e.name, e.description, e.category, e.risk_level;

-- ==============================================================================
-- STORED PROCEDURES FOR OKTA CONNECTOR
-- ==============================================================================

-- Create user (for Okta provisioning)
CREATE OR REPLACE FUNCTION create_user(
    p_user_id VARCHAR(100),
    p_username VARCHAR(100),
    p_email VARCHAR(255),
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    p_department VARCHAR(100) DEFAULT NULL,
    p_title VARCHAR(100) DEFAULT NULL
) RETURNS VARCHAR(100) AS $$
BEGIN
    INSERT INTO users (user_id, username, email, first_name, last_name, department, title, status)
    VALUES (p_user_id, p_username, p_email, p_first_name, p_last_name, p_department, p_title, 'ACTIVE');

    -- Audit log
    INSERT INTO audit_log (operation, entity_type, entity_id, new_values, performed_by, source)
    VALUES ('CREATE', 'USER', p_user_id,
            jsonb_build_object('username', p_username, 'email', p_email),
            'okta', 'OKTA');

    RETURN p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Update user
CREATE OR REPLACE FUNCTION update_user(
    p_user_id VARCHAR(100),
    p_email VARCHAR(255) DEFAULT NULL,
    p_first_name VARCHAR(100) DEFAULT NULL,
    p_last_name VARCHAR(100) DEFAULT NULL,
    p_department VARCHAR(100) DEFAULT NULL,
    p_title VARCHAR(100) DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_old_values JSONB;
BEGIN
    SELECT jsonb_build_object('email', email, 'first_name', first_name, 'last_name', last_name)
    INTO v_old_values FROM users WHERE user_id = p_user_id;

    UPDATE users SET
        email = COALESCE(p_email, email),
        first_name = COALESCE(p_first_name, first_name),
        last_name = COALESCE(p_last_name, last_name),
        department = COALESCE(p_department, department),
        title = COALESCE(p_title, title)
    WHERE user_id = p_user_id;

    -- Audit log
    INSERT INTO audit_log (operation, entity_type, entity_id, old_values, performed_by, source)
    VALUES ('UPDATE', 'USER', p_user_id, v_old_values, 'okta', 'OKTA');

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Deactivate user
CREATE OR REPLACE FUNCTION deactivate_user(p_user_id VARCHAR(100)) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users SET
        status = 'INACTIVE',
        deactivated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;

    -- Revoke all entitlements
    UPDATE user_entitlements SET
        status = 'REVOKED',
        revoked_at = CURRENT_TIMESTAMP,
        revoked_by = 'okta'
    WHERE user_id = p_user_id AND status = 'ACTIVE';

    -- Audit log
    INSERT INTO audit_log (operation, entity_type, entity_id, performed_by, source)
    VALUES ('DEACTIVATE', 'USER', p_user_id, 'okta', 'OKTA');

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Assign entitlement
CREATE OR REPLACE FUNCTION assign_entitlement(
    p_user_id VARCHAR(100),
    p_entitlement_id VARCHAR(100)
) RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO user_entitlements (user_id, entitlement_id, granted_by, status)
    VALUES (p_user_id, p_entitlement_id, 'okta', 'ACTIVE')
    ON CONFLICT (user_id, entitlement_id)
    DO UPDATE SET status = 'ACTIVE', granted_at = CURRENT_TIMESTAMP, revoked_at = NULL;

    -- Audit log
    INSERT INTO audit_log (operation, entity_type, entity_id, new_values, performed_by, source)
    VALUES ('ASSIGN', 'ENTITLEMENT', p_entitlement_id,
            jsonb_build_object('user_id', p_user_id),
            'okta', 'OKTA');

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Revoke entitlement
CREATE OR REPLACE FUNCTION revoke_entitlement(
    p_user_id VARCHAR(100),
    p_entitlement_id VARCHAR(100)
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE user_entitlements SET
        status = 'REVOKED',
        revoked_at = CURRENT_TIMESTAMP,
        revoked_by = 'okta'
    WHERE user_id = p_user_id AND entitlement_id = p_entitlement_id;

    -- Audit log
    INSERT INTO audit_log (operation, entity_type, entity_id, old_values, performed_by, source)
    VALUES ('REVOKE', 'ENTITLEMENT', p_entitlement_id,
            jsonb_build_object('user_id', p_user_id),
            'okta', 'OKTA');

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- GRANT PERMISSIONS
-- ==============================================================================
-- Grant permissions to the application user (run after connecting as admin)

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO oktaadmin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO oktaadmin;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO oktaadmin;

-- ==============================================================================
-- VERIFICATION QUERIES
-- ==============================================================================
-- Run these to verify the schema was created correctly:

-- SELECT COUNT(*) as user_count FROM users;
-- SELECT COUNT(*) as entitlement_count FROM entitlements;
-- SELECT * FROM v_users_with_entitlements;
-- SELECT * FROM v_active_entitlements;
