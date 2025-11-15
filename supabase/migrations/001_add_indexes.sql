-- Add missing indexes for performance
CREATE INDEX IF NOT EXISTS idx_activity_logs_category ON activity_logs(category);
CREATE INDEX IF NOT EXISTS idx_activity_logs_outcome ON activity_logs(outcome);
CREATE INDEX IF NOT EXISTS idx_activity_logs_employee_created ON activity_logs(employee_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);
CREATE INDEX IF NOT EXISTS idx_clients_company_name ON clients(company_name);
CREATE INDEX IF NOT EXISTS idx_clients_contact_email ON clients(contact_email);
CREATE INDEX IF NOT EXISTS idx_clients_assigned_status ON clients(assigned_employee_id, status);
CREATE INDEX IF NOT EXISTS idx_daily_reports_employee_date ON daily_reports(employee_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_users_role_status ON users(role, status);

-- Add soft delete
ALTER TABLE clients ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_clients_deleted_at ON clients(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
