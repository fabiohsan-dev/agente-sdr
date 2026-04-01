-- ============================================
-- SDR AGENT - Multi-tenancy Migration
-- ============================================
-- Executar APÓS o schema.sql principal
-- Adiciona isolamento por tenant (cliente)
--
-- Uso:
--   1. Executar no SQL Editor do Supabase
--   2. Criar tenant via INSERT ou via API
--   3. Usar o api_key gerado para autenticar

-- ============================================
-- TABLE: tenants
-- ============================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identificação
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,  -- Ex: "acme-corp"

    -- Autenticação
    api_key TEXT NOT NULL UNIQUE,  -- Chave para autenticar requests

    -- Configurações do tenant
    settings JSONB DEFAULT '{}',
    -- Exemplos de settings:
    -- {
    --   "company_name": "Acme Corp",
    --   "industry": "SaaS",
    --   "calcom_api_key": "...",
    --   "calcom_event_type_id": 123,
    --   "chatwoot_account_id": 456,
    --   "chatwoot_inbox_id": 1,
    --   "chatwoot_api_token": "...",
    --   "openai_model": "gpt-4.1-mini",
    --   "custom_prompt_override": "...",
    --   "timezone": "America/Sao_Paulo",
    --   "business_hours": {"start": "09:00", "end": "18:00"}
    -- }

    -- Limites
    max_leads INTEGER DEFAULT 500,
    max_conversations_per_month INTEGER DEFAULT 5000,

    -- Estado
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_api_key ON tenants(api_key);
CREATE INDEX idx_tenants_is_active ON tenants(is_active);

-- Trigger updated_at
CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ADD tenant_id TO EXISTING TABLES
-- ============================================

-- leads
ALTER TABLE leads ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_leads_tenant_id ON leads(tenant_id);

-- Drop unique constraints que agora precisam incluir tenant_id
ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_email_unique;
ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_phone_unique;
-- Recriar como unique POR tenant
ALTER TABLE leads ADD CONSTRAINT leads_email_tenant_unique UNIQUE (email, tenant_id);
ALTER TABLE leads ADD CONSTRAINT leads_phone_tenant_unique UNIQUE (phone, tenant_id);

-- conversations
ALTER TABLE conversations ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_conversations_tenant_id ON conversations(tenant_id);

-- events
ALTER TABLE events ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_events_tenant_id ON events(tenant_id);

-- follow_jobs
ALTER TABLE follow_jobs ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_follow_jobs_tenant_id ON follow_jobs(tenant_id);

-- bookings
ALTER TABLE bookings ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_bookings_tenant_id ON bookings(tenant_id);

-- agent_snapshots
ALTER TABLE agent_snapshots ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_agent_snapshots_tenant_id ON agent_snapshots(tenant_id);

-- ============================================
-- RLS (Row Level Security)
-- ============================================
-- Com RLS, queries filtram automaticamente por tenant_id
-- IMPORTANTE: Requer configurar o role do service_role corretamente

-- Habilitar RLS nas tabelas principais
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE follow_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_snapshots ENABLE ROW LEVEL SECURITY;

-- Policies para service_role (bypass)
-- O service_role NÃO é afetado por RLS por padrão no Supabase

-- ============================================
-- VIEW: tenant_metrics
-- ============================================
-- View pré-computada para métricas por tenant

CREATE OR REPLACE VIEW tenant_metrics AS
SELECT
    t.id AS tenant_id,
    t.name AS tenant_name,
    t.slug AS tenant_slug,
    COUNT(DISTINCT l.id) AS total_leads,
    COUNT(DISTINCT l.id) FILTER (WHERE l.current_state = 'SCHEDULED') AS scheduled_leads,
    COUNT(DISTINCT c.id) AS total_conversations,
    COUNT(DISTINCT c.id) FILTER (WHERE c.is_active) AS active_conversations,
    COUNT(DISTINCT b.id) AS total_bookings,
    ROUND(
        COUNT(DISTINCT l.id) FILTER (WHERE l.current_state = 'SCHEDULED')::NUMERIC /
        NULLIF(COUNT(DISTINCT l.id), 0) * 100, 1
    ) AS conversion_rate_pct
FROM tenants t
LEFT JOIN leads l ON l.tenant_id = t.id
LEFT JOIN conversations c ON c.tenant_id = t.id
LEFT JOIN bookings b ON b.tenant_id = t.id
WHERE t.is_active = TRUE
GROUP BY t.id, t.name, t.slug;

-- ============================================
-- FUNCTION: create_tenant
-- ============================================
-- Helper para criar tenant com API key auto-gerada

CREATE OR REPLACE FUNCTION create_tenant(
    p_name TEXT,
    p_slug TEXT,
    p_settings JSONB DEFAULT '{}'
) RETURNS tenants AS $$
DECLARE
    v_tenant tenants;
    v_api_key TEXT;
BEGIN
    -- Gerar API key: sdr_<slug>_<random>
    v_api_key := 'sdr_' || p_slug || '_' || encode(gen_random_bytes(24), 'hex');

    INSERT INTO tenants (name, slug, api_key, settings)
    VALUES (p_name, p_slug, v_api_key, p_settings)
    RETURNING * INTO v_tenant;

    RETURN v_tenant;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- EXAMPLE: Create a default tenant
-- ============================================
-- SELECT * FROM create_tenant('Minha Empresa', 'minha-empresa', '{"industry": "SaaS"}'::jsonb);

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE tenants IS 'Clientes (multi-tenancy) com isolamento de dados';
COMMENT ON COLUMN tenants.slug IS 'Identificador URL-safe único do tenant';
COMMENT ON COLUMN tenants.api_key IS 'Chave de API para autenticação (prefixo sdr_)';
COMMENT ON COLUMN tenants.settings IS 'Configurações específicas do tenant (JSON)';
COMMENT ON VIEW tenant_metrics IS 'Métricas agregadas por tenant';
